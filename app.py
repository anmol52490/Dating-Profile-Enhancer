import streamlit as st
import llm_generator  # Our AI "brain"
import prompts      # Our static data
import photo_ui     # Our UI file for all photo-related pages

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Profile Wingmans",
    page_icon="❤️‍🔥",
    layout="centered"
)

# --- State Management ---
if "app_state" not in st.session_state:
    st.session_state.app_state = "triage"
if "user_answers" not in st.session_state:
    st.session_state.user_answers = None

# New state for our agentic workflow
if "recommender_state" not in st.session_state:
    st.session_state.recommender_state = None # Will hold the full state from Agent 1
if "final_generated_content" not in st.session_state:
    st.session_state.final_generated_content = None # Will hold the full state from Agent 2
if "user_selected_prompts" not in st.session_state:
    st.session_state.user_selected_prompts = []

# (Photo states remain unchanged)
if "guide_page" not in st.session_state:
    st.session_state.guide_page = 1
for i in range(1, 7):
    if f"critique_{i}" not in st.session_state:
        st.session_state[f"critique_{i}"] = None

# --- API Key Check ---
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
    if not API_KEY or API_KEY == "sk-...":
        st.error("OpenAI API key not found. Please add it to your `.streamlit/secrets.toml` file.")
        st.stop()
except KeyError:
    st.error("OpenAI API key not found. Please create a `.streamlit/secrets.toml` file and add it.")
    st.stop()

# --- Helper Function ---
def set_state(state):
    """Callback function to change the app state."""
    st.session_state.app_state = state

# --- Text-Gen UI ---

def render_personality_core_page():
    """Page 1: Collect the 10 answers."""
    st.title("The Personality Core")
    st.caption("Now for the fun part. The more detail you give me, the more I can work with! Don't worry about sounding witty or clever, that's my job! Just be yourself.")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    with st.form("profile_form"):
        user_answers = {}
        for q in prompts.QUESTIONS:
            placeholder = prompts.QUESTION_PLACEHOLDERS.get(q, "")
            user_answers[q] = st.text_area(q, placeholder=placeholder, height=100)
        
        submitted = st.form_submit_button("Analyze My Personality", use_container_width=True, type="primary")

        if submitted:
            if any(value.strip() == "" for value in user_answers.values()):
                st.error("Please fill out all 10 questions to get the best results!")
            else:
                st.session_state.user_answers = user_answers
                set_state("generating_recommendations")
                st.rerun()

def render_generating_recommendations_page():
    """Page 1.5: Run Agent 1 (Recommender)."""
    st.title("Crafting your profile...")
    with st.spinner("Analyzing your personality to find your 'vibe' and best prompts..."):
        # This is the call to Agent 1
        recommender_state = llm_generator.run_recommender_graph(st.session_state.user_answers, API_KEY)
        
        if recommender_state:
            st.session_state.recommender_state = recommender_state
            set_state("show_recommendations")
        else:
            st.error("There was an error analyzing your profile. Please try again.")
            set_state("prompt_generator")
        st.rerun()

def render_recommendations_page():
    """Page 2: The 'Human-in-the-Loop' UI."""
    st.title("Your Personality Analysis is Ready!")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    state = st.session_state.recommender_state
    if not state:
        st.error("No recommendation data found. Please go back.")
        return

    st.subheader("Your AI-Diagnosed 'Vibe'")
    st.info(f"**{state.get('holistic_story', 'No vibe found.')}**")
    st.markdown("Based on this, here are the top 10 prompts our AI recommends for you. Please select the ones you want to use (we recommend 3 Hinge and 2-3 Bumble).")
    
    recommendations = state.get('recommendations', [])
    hinge_recs = [r for r in recommendations if r['app'] == 'Hinge']
    bumble_recs = [r for r in recommendations if r['app'] == 'Bumble']
    
    selected_prompts_list = []
    
    with st.form("prompt_selection_form"):
        st.subheader("Hinge Recommendations")
        for rec in hinge_recs:
            with st.container(border=True):
                is_selected = st.checkbox(rec['prompt'], key=rec['prompt'])
                st.caption(f"**Reason:** {rec['rationale']}")
                if is_selected:
                    # Append a dictionary with BOTH prompt and rationale
                    selected_prompts_list.append({
                        "prompt": rec['prompt'],
                        "rationale": rec['rationale']
                    }) # <-- NEW
        
        st.subheader("Bumble Recommendations")
        for rec in bumble_recs:
            with st.container(border=True):
                is_selected = st.checkbox(rec['prompt'], key=rec['prompt'])
                st.caption(f"**Reason:** {rec['rationale']}")
                if is_selected:
                    selected_prompts_list.append({
                        "prompt": rec['prompt'],
                        "rationale": rec['rationale']
                    })
        
        st.markdown("---")
        submitted = st.form_submit_button("Write My Answers!", use_container_width=True, type="primary")
        
        if submitted:
            if not selected_prompts_list:
                st.error("Please select at least one prompt to continue.")
            else:
                st.session_state.user_selected_prompts = selected_prompts_list
                set_state("generating_answers")
                st.rerun()

def render_generating_answers_page():
    """Page 2.5: Run Agent 2 (Writer)."""
    st.title("Writing your answers...")
    with st.spinner(f"Your wingman is writing {len(st.session_state.user_selected_prompts)} new answers..."):
        
        # This is the call to Agent 2
        final_state = llm_generator.run_writer_graph(
            st.session_state.recommender_state,
            st.session_state.user_selected_prompts
        )
        
        if final_state:
            st.session_state.final_generated_content = final_state
            set_state("deliverable")
        else:
            st.error("There was an error generating your answers. Please try again.")
            set_state("show_recommendations")
        st.rerun()

def render_deliverable_page():
    """Page 3: Show the final generated Bio + Prompt Options."""
    st.title("Your New Profile is Ready!")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    content = st.session_state.final_generated_content
    if not content:
        st.error("Something went wrong. Please go back and try again.")
        return

    st.subheader("Your New Bio")
    st.markdown("Copy this into your Tinder or Bumble bio.")
    st.code(content.get("generated_bio", "Error: Bio not generated."), language=None)

    st.subheader("Your Generated Prompt Answers")
    st.markdown("For each prompt, we've generated 3 witty options. Pick your favorite!")
    
    generated_prompts = content.get("generated_prompts", [])
    if not generated_prompts:
        st.warning("No prompt answers were generated.")
        return

    for item in generated_prompts:
        with st.container(border=True):
            st.markdown(f"**Prompt:** `{item.get('question')}`")
            options = item.get('options', [])
            if options:
                # Use a radio button to let the user see all options and pick one
                st.radio(
                    "Pick your favorite answer:",
                    options,
                    key=item.get('question'),
                    label_visibility="collapsed"
                )
            else:
                st.write("No options generated for this prompt.")
    
    st.success(
        """
        **Pro-Tip: Reset Your Algorithm!**
        For the best results, delete your *entire* dating account and restart it fresh.
        """
    )


# --- MAIN APP ROUTER (Modified for new flow) ---

def render_triage_page():
    """Renders the main homepage, which now acts as a router."""
    st.title("Your AI Profile Wingmans ❤️‍🔥")
    st.markdown("Choose your mission. We can write your bio and prompts, or audit your photos.")
    
    st.subheader("I need help with my text...")
    st.button("Write My Bio & Prompts", on_click=set_state, args=["prompt_generator"], use_container_width=True, type="primary")
    
    st.markdown("---")
    
    st.subheader("I need help with my photos...")
    st.markdown("Do you have photos you want to analyze, or do you need to take new ones?")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Analyze My Photos", on_click=set_state, args=["photo_analyzer"], use_container_width=True)
    with col2:
        st.button("Teach Me How to Take Photos", on_click=set_state, args=["photo_guide"], use_container_width=True)

# --- Main App Router ---

if st.session_state.app_state == "triage":
    render_triage_page()

# New Text Generation Flow
elif st.session_state.app_state == "prompt_generator":
    render_personality_core_page()
elif st.session_state.app_state == "generating_recommendations":
    render_generating_recommendations_page()
elif st.session_state.app_state == "show_recommendations":
    render_recommendations_page()
elif st.session_state.app_state == "generating_answers":
    render_generating_answers_page()
elif st.session_state.app_state == "deliverable":
    render_deliverable_page()

# (Photo Flow remains unchanged)
elif st.session_state.app_state == "photo_analyzer":
    photo_ui.render_photo_analyzer_page()
elif st.session_state.app_state == "photo_guide":
    photo_ui.render_photo_guide_page()