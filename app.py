import streamlit as st
import llm_generator  # Our AI "brain"
import prompts      # Our static data
import photo_ui     # Our new UI file for all photo-related pages

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Profile Wingman",
    page_icon="❤️‍🔥",
    layout="centered"
)

# --- State Management ---
if "app_state" not in st.session_state:
    st.session_state.app_state = "triage"
if "user_answers" not in st.session_state:
    st.session_state.user_answers = None
if "generated_profile" not in st.session_state:
    st.session_state.generated_profile = None

# Initialize states for the new UI modules
if "guide_page" not in st.session_state:
    st.session_state.guide_page = 1
# Create critique states for all 6 slots
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

# --- (Keep all existing text-gen UI functions) ---
# render_personality_core_page(), render_generating_page(), render_deliverable_page()
# ... (These functions remain unchanged from our previous file) ...

def render_personality_core_page():
    st.title("The Personality Core")
    st.caption("Now for the fun part. The more detail you give me, the more I can work with! Don't worry about sounding witty or clever, that's my job! Just be yourself.")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    with st.form("profile_form"):
        user_answers = {}
        for q in prompts.QUESTIONS:
            placeholder = prompts.QUESTION_PLACEHOLDERS.get(q, "")
            user_answers[q] = st.text_area(q, placeholder=placeholder, height=100)
        
        submitted = st.form_submit_button("Generate My Profile", use_container_width=True, type="primary")

        if submitted:
            if any(value.strip() == "" for value in user_answers.values()):
                st.error("Please fill out all 10 questions to get the best results!")
            else:
                st.session_state.user_answers = user_answers
                set_state("generating_text")
                st.rerun()

def render_generating_page():
    st.title("Crafting your profile...")
    with st.spinner("Writing your new bio and prompts... this can take up to 30 seconds."):
        profile_json = llm_generator.generate_profile(st.session_state.user_answers, API_KEY)
        
        if profile_json:
            st.session_state.generated_profile = profile_json
            set_state("deliverable")
        else:
            st.error("There was an error generating your profile. Please try again.")
            set_state("prompt_generator")
        st.rerun()

def render_deliverable_page():
    st.title("Your New Profile is Ready!")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    profile = st.session_state.generated_profile
    if not profile:
        st.error("Something went wrong. Please go back and try again.")
        return

    st.subheader("Your New Bio")
    st.markdown("Copy this into your Tinder or Bumble bio.")
    st.code(profile.get("bio", "Error: Bio not generated."), language=None)

    st.subheader("Your Generated Prompts")
    st.markdown("Copy these answers into your Hinge or Bumble prompts.")
    
    for item in profile.get("prompts", []):
        with st.container(border=True):
            st.markdown(f"**{item.get('app')} Prompt:** `{item.get('question')}`")
            st.code(item.get('answer'), language=None)
    
    st.success(
        """
        **Pro-Tip: Reset Your Algorithm!**
        For the best results, delete your *entire* dating account and restart it fresh.
        """
    )


# --- MODIFIED TRIAGE PAGE ---

def render_triage_page():
    """Renders the main homepage, which now acts as a router."""
    st.title("Your AI Profile Wingman ❤️‍🔥")
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


# --- MAIN APP ROUTER (Modified) ---
# This block checks the app_state and calls the correct render function.

if st.session_state.app_state == "triage":
    render_triage_page()

# Text Generation Flow
elif st.session_state.app_state == "prompt_generator":
    render_personality_core_page()
elif st.session_state.app_state == "generating_text":
    render_generating_page()
elif st.session_state.app_state == "deliverable":
    render_deliverable_page()

# New Photo Flow
elif st.session_state.app_state == "photo_analyzer":
    photo_ui.render_photo_analyzer_page()
elif st.session_state.app_state == "photo_guide":
    photo_ui.render_photo_guide_page()

