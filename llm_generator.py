import openai
import json
import prompts  # Our local prompts.py file
import base64
import io
from PIL import Image

# --- New LangGraph Imports ---
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from typing import List, Dict, Any

# --- 1. Define The "State" for our Graph ---
# This is the "shared memory" (meeting notes) for our agents.
class ProfileGenerationState(TypedDict):
    """The shared state for the profile generation workflow."""
    
    # Input from user
    user_10_answers: Dict[str, str]
    
    # Output of Agent 1 (Recommender)
    holistic_story: str
    recommendations: List[Dict[str, str]]
    
    # Input from UI (Human-in-the-Loop)
    user_selected_prompts: List[Dict[str, str]]
    
    # Output of Agent 2 (Writer)
    generated_bio: str
    generated_prompts: List[Dict[str, Any]] # Will be [{ "question": "...", "options": [...] }]
    
    # API key
    api_key: str

# --- 2. Define The "Nodes" (Our Agents) ---

def _run_recommender_agent(state: ProfileGenerationState):
    """
    Node 1: The Recommender Agent.
    Runs Phase 1.A, 1.B, and 1.C to generate recommendations.
    """
    print("--- Running Recommender Agent ---")
    client = openai.OpenAI(api_key=state["api_key"])
    
    # We must provide the AI with the prompt dictionaries to choose from
    user_prompt_content = f"""
    Here are my 10 answers:
    {json.dumps(state["user_10_answers"], indent=2)}

    Here are the Hinge prompts, categorized by type:
    {json.dumps(prompts.HINGE_PROMPTS_BY_TYPE, indent=2)}
    
    Here are the Bumble prompts, categorized by type:
    {json.dumps(prompts.BUMBLE_PROMPTS_BY_TYPE, indent=2)}
    """
    
    completion = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",  # Use a smart model for this complex analysis
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompts.RECOMMENDER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt_content}
        ]
    )
    
    response_data = json.loads(completion.choices[0].message.content)
    
    # Update the shared state
    return {
        "holistic_story": response_data.get("holistic_story"),
        "recommendations": response_data.get("recommendations")
    }

def _run_bio_writer_agent(state: ProfileGenerationState):
    """
    Node 2a: The Bio Writer.
    Uses the holistic story to write a bio.
    """
    print("--- Running Bio Writer Agent ---")
    client = openai.OpenAI(api_key=state["api_key"])
    
    user_prompt_content = f"""
    Here is the "Holistic Story" you diagnosed for this user:
    "{state['holistic_story']}"
    
    Here are the user's 10 raw answers for material:
    {json.dumps(state["user_10_answers"], indent=2)}
    """
    
    completion = client.chat.completions.create(
        model="gpt-4.1-2025-04-14", # Good for creative writing
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompts.BIO_WRITER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt_content}
        ]
    )
    
    response_data = json.loads(completion.choices[0].message.content)
    return {"generated_bio": response_data.get("bio")}

def _run_prompt_writer_agent(state: ProfileGenerationState):
    """
    Node 2b: The Prompt Writer.
    Loops through the user's selected prompts (and their rationales + anchors)
    and generates 3 options for each.
    """
    print("--- Running Prompt Writer Agent ---")
    client = openai.OpenAI(api_key=state["api_key"])
    generated_prompts_list = []
    
    # Iterate over the list of full recommendation dictionaries
    for prompt_data in state["user_selected_prompts"]:
        prompt_text = prompt_data.get('prompt', 'Error: No prompt text')
        
        # This is the critical fix: Get the 'anchor_text' from the prompt_data
        anchor_text = prompt_data.get('anchor_text', 'Error: No anchor_text found') # <-- NEW
        
        print(f"  Generating answers for: {prompt_text}")
        
        # We now pass the ANCHOR_TEXT from Agent 1 directly into the prompt for Agent 2.
        # Your prompts.py (PROMPT_WRITER_SYSTEM_PROMPT) is already waiting for this.
        user_prompt_content = f"""
        Here is the "Holistic Story" for the user (use this for TONE only):
        "{state['holistic_story']}"
        
        Here is the *exact user quote* (anchor_text) you MUST build your answer around:
        "{anchor_text}"
        
        Here are the user's 10 raw answers (for context, but the anchor_text is your focus):
        {json.dumps(state["user_10_answers"], indent=2)}
        
        And here is the specific prompt I need you to write for:
        "{prompt_text}"
        """
        
        completion = client.chat.completions.create(
            model="gpt-4.1-2025-04-14", # Using your specified model
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompts.PROMPT_WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt_content}
            ]
        )
        response_data = json.loads(completion.choices[0].message.content)
        
        # Append the results for this specific prompt
        generated_prompts_list.append({
            "question": prompt_text,
            "options": response_data.get("answer_options", ["Error generating option 1.", "Error generating option 2.", "Error generating option 3."])
        })
        
    # Return the final list of generated prompts to update the state
    return {"generated_prompts": generated_prompts_list}


# --- 3. Define the "Public" Functions for app.py to call ---

def run_recommender_graph(user_answers_dict, api_key):
    """
    Public Function 1:
    Runs the first part of the workflow (Agent 1) to get recommendations.
    This graph stops and waits for human input.
    """
    workflow = StateGraph(ProfileGenerationState)
    
    # Add the first agent node
    workflow.add_node("recommender", _run_recommender_agent)
    
    # The entry point is the recommender
    workflow.set_entry_point("recommender")
    
    # After the recommender, the graph ends. We will return the state.
    workflow.add_edge("recommender", END)
    
    # Compile the graph
    app = workflow.compile()
    
    # Prepare the initial state
    initial_state = {
        "user_10_answers": user_answers_dict,
        "api_key": api_key,
        # Initialize other fields as empty
        "holistic_story": "",
        "recommendations": [],
        "user_selected_prompts": [],
        "generated_bio": "",
        "generated_prompts": []
    }
    
    # Run the graph
    try:
        final_state = app.invoke(initial_state)
        return final_state # This state now contains recommendations
    except Exception as e:
        print(f"Error in Recommender Graph: {e}")
        return None

def run_writer_graph(state_from_recommender, user_selected_prompts):
    """
    Public Function 2:
    Runs the second part of the workflow (Agent 2) to write answers.
    It takes the state from the previous run and the user's choices.
    """
    workflow = StateGraph(ProfileGenerationState)
    
    # Add the writer agent nodes
    workflow.add_node("bio_writer", _run_bio_writer_agent)
    workflow.add_node("prompt_writer", _run_prompt_writer_agent)
    
    # The entry point is the bio writer
    workflow.set_entry_point("bio_writer")
    
    # Define the flow: bio_writer -> prompt_writer -> END
    workflow.add_edge("bio_writer", "prompt_writer")
    workflow.add_edge("prompt_writer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    # Update the state with the user's selections
    state_from_recommender["user_selected_prompts"] = user_selected_prompts
    
    # Run the graph
    try:
        final_state = app.invoke(state_from_recommender)
        return final_state # This state now contains the final answers
    except Exception as e:
        print(f"Error in Writer Graph: {e}")
        return None

# --- 4. PHOTO ANALYSIS FUNCTION (Unchanged) ---
# (Keep the existing analyze_photo function exactly as it was)
def analyze_photo(api_key, image_bytes, photo_slot_number):
    """
    Calls the OpenAI Multimodal API to analyze a dating photo.
    ... (rest of the function is identical to the one you provided) ...
    """
    try:
        client = openai.OpenAI(api_key=api_key)

        # Convert image bytes to a web-safe base64 string
        # Resize image to prevent it from being too large for the API
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
            if img.mode == 'RGBA':
                # Create a white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            elif img.mode not in ('RGB', 'L'):
                # Convert other modes to RGB
                img = img.convert('RGB')
            
            # Resize while maintaining aspect ratio, max 1024px
            img.thumbnail((1024, 1024))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            image_bytes_resized = buf.getvalue()
            
        base64_image = base64.b64encode(image_bytes_resized).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"

        messages = [
            {
                "role": "system",
                "content": prompts.PHOTO_ANALYZER_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please analyze this photo. It is for photo_slot_number: {photo_slot_number}.Does it fit if not where does it fit?  Use your full knowledge base."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "low" # Use low detail for faster, cheaper analysis
                        }
                    }
                ]
            }
        ]

        completion = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",  # Must be a multimodal model
            response_format={"type": "json_object"},
            messages=messages,
            max_tokens=1000 
        )

        response_json_str = completion.choices[0].message.content
        response_data = json.loads(response_json_str)
        
        return response_data

    except Exception as e:
        print(f"Error calling OpenAI API for image: {e}")
        return None
# --- NEW FUNCTION FOR PHOTO ANALYSIS ---

def audit_profile_flow(photo_summaries_dict, api_key):
    """
    Sends text descriptions of all photos to the LLM for a holistic review.
    """
    try:
        client = openai.OpenAI(api_key=api_key)
        
        user_content = f"""
        Here are the descriptions of the photos I have selected:
        {json.dumps(photo_summaries_dict, indent=2)}
        
        Please audit the flow and variety of my profile.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Fast and cheap for text
            messages=[
                {"role": "system", "content": prompts.HOLISTIC_PHOTO_REVIEW_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error auditing profile: {e}"

def analyze_photo(api_key, image_bytes, photo_slot_number):
    """
    Calls the OpenAI Multimodal API to analyze a dating photo.

    Args:
        api_key (str): The OpenAI API key.
        image_bytes (bytes): The raw bytes of the image file.
        photo_slot_number (int): The intended slot (1-6) for this photo.

    Returns:
        dict: A dictionary with the detailed photo critique,
              or None if an error occurs.
    """
    try:
        client = openai.OpenAI(api_key=api_key)

        # Convert image bytes to a web-safe base64 string
        # Resize image to prevent it from being too large for the API
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
            if img.mode == 'RGBA':
                # Create a white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            elif img.mode not in ('RGB', 'L'):
                # Convert other modes to RGB
                img = img.convert('RGB')
            
            # Resize while maintaining aspect ratio, max 1024px
            img.thumbnail((1024, 1024))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            image_bytes_resized = buf.getvalue()
            
        base64_image = base64.b64encode(image_bytes_resized).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"

        messages = [
            {
                "role": "system",
                "content": prompts.PHOTO_ANALYZER_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please analyze this photo. It is for photo_slot_number: {photo_slot_number}. Use your full knowledge base."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "low" # Use low detail for faster, cheaper analysis
                        }
                    }
                ]
            }
        ]

        completion = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",  # Must be a multimodal model
            response_format={"type": "json_object"},
            messages=messages,
            max_tokens=1000 
        )

        response_json_str = completion.choices[0].message.content
        response_data = json.loads(response_json_str)
        
        return response_data

    except Exception as e:
        print(f"Error calling OpenAI API for image: {e}")
        return None

