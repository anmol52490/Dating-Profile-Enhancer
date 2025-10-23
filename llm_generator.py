import openai
import json
import prompts  # Our local prompts.py file
import base64
import io
from PIL import Image

# --- (Keep the existing generate_profile function exactly as it was) ---

def generate_profile(user_answers_dict, api_key):
    """
    Calls the OpenAI API to generate a dating profile (bio and prompts).
    """
    try:
        client = openai.OpenAI(api_key=api_key)

        user_prompt_content = f"""
        Here are my 10 answers:
        {json.dumps(user_answers_dict, indent=2)}

        Here is the list of available Hinge prompts:
        {json.dumps(prompts.HINGE_PROMPTS)}

        Here is the list of available Bumble prompts:
        {json.dumps(prompts.BUMBLE_PROMPTS)}

        Please generate my profile based on these.
        """

        completion = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:jamie-date:jamiegpt-data-humanchat-custom:CIgpsCAk",  # Use a powerful model for text-gen
            response_format={"type": "json_object"}, # Enable JSON mode
            messages=[
                {"role": "system", "content": prompts.SYSTEM_PROMPT}, # Assuming SYSTEM_PROMPT is defined in prompts.py, or you can copy it here
                {"role": "user", "content": user_prompt_content}
            ]
        )

        response_json_str = completion.choices[0].message.content
        response_data = json.loads(response_json_str)
        
        return response_data

    except Exception as e:
        print(f"Error calling OpenAI API for text: {e}")
        return None

# --- NEW FUNCTION FOR PHOTO ANALYSIS ---

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
            model="gpt-4o",  # Must be a multimodal model
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

