import streamlit as st
import llm_generator  # Our AI "brain"
import prompts      # Our static data
import photo_ui     # Our UI file for all photo-related pages
import coach_ui     # Our UI file for the Conversation Coach page


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
        
        submitted = st.form_submit_button("Write my Bios & Prompts", use_container_width=True, type="primary")

        if submitted:
            if any(value.strip() == "" for value in user_answers.values()):
                st.error("Please fill out all 10 questions to get the best results!")
            else:
                st.session_state.user_answers = user_answers
                set_state("generating_recommendations")
                st.rerun()

def render_generating_recommendations_page():
    """Page 1.5: Run Agent 1 AND Agent 2 back-to-back (Automated Flow)."""
    st.title("Crafting your profile...")
    
    with st.spinner("Coming up with something great! May take several minutes..."):
        try:
            # 1. Run Agent 1 (Recommender)
            recommender_state = llm_generator.run_recommender_graph(st.session_state.user_answers, API_KEY)
            
            if recommender_state and recommender_state.get('recommendations'):
                # 2. AUTO-SELECT ALL RECOMMENDATIONS (Skip User Selection)
                # We take the full list from Agent 1 and define it as the "selected" list
                st.session_state.user_selected_prompts = recommender_state['recommendations']
                
                # Save intermediate state just in case
                st.session_state.recommender_state = recommender_state
                
                # 3. Run Agent 2 (Writer) IMMEDIATELY
                final_state = llm_generator.run_writer_graph(
                    recommender_state,
                    st.session_state.user_selected_prompts
                )
                
                if final_state:
                    st.session_state.final_generated_content = final_state
                    set_state("deliverable") # Jump straight to results
                    st.rerun()
                else:
                    st.error("There was an error generating your answers.")
                    if st.button("Try Again"):
                        set_state("prompt_generator")
            else:
                st.error("There was an error analyzing your profile.")
                if st.button("Try Again"):
                    set_state("prompt_generator")
                    
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            if st.button("Back to Start"):
                set_state("prompt_generator")

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
        # Use enumerate for stable keys, as the consultant suggested
        for i, rec in enumerate(hinge_recs):
            with st.container(border=True):
                is_selected = st.checkbox(rec['prompt'], key=f"hinge_{i}")
                st.caption(f"**Reason:** {rec['rationale']}")
                if is_selected:
                    # Append the ENTIRE recommendation object
                    selected_prompts_list.append(rec) # <-- NEW
        
        st.subheader("Bumble Recommendations")
        for i, rec in enumerate(bumble_recs):
            with st.container(border=True):
                is_selected = st.checkbox(rec['prompt'], key=f"bumble_{i}")
                st.caption(f"**Reason:** {rec['rationale']}")
                if is_selected:
                    # Append the ENTIRE recommendation object
                    selected_prompts_list.append(rec) # <-- NEW
        
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

    st.markdown("---")
    st.success("Want to see even better prompts?")
    st.markdown(
        """
        **My list of best selling Dating Prompts is only $27.**
        
        You'll get 25 pages of witty prompts you can use for any dating app.
        
        [**Click here to grab the list**](https://jamie-date.mykajabi.com/offers/XDy2mFmT/checkout)
        """
    )
    
    st.info(
        """
        **Pro-Tip: Reset Your Algorithm!**
        For the best results, delete your *entire* dating account and restart it fresh.
        """
    )


    st.markdown("---")
    st.subheader("What's Next?")
    st.write("Now that your profile is set, do you want pointers on **opening conversations**?")
    
    # This button triggers the switch
    if st.button("Yes, help me with openers", type="primary"):
        set_state("coach_mode") # This connects to the router above
        st.rerun()


# --- MAIN APP ROUTER (Modified for new flow) ---

def render_triage_page():
    """Renders the main homepage, which now acts as a router."""
    st.title("Your AI Profile Wingmans ❤️‍🔥")
    st.markdown("Choose your mission. We can write your bio and prompts, or audit your photos.")
    
    st.subheader("I need help with my text...")
    st.button("Fix my Online Dating Profile", on_click=set_state, args=["prompt_generator"], use_container_width=True, type="primary")
    
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


elif st.session_state.app_state == "coach_mode":
    coach_ui.render_coach_page()