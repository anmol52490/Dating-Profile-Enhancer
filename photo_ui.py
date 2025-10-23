import streamlit as st
import llm_generator
import base64
import io

# --- Helper Function to set state ---
def set_state(state):
    st.session_state.app_state = state

# --- Helper Function to render the critique ---
def render_critique_card(critique):
    """Parses and displays the JSON critique from the LLM."""
    if not critique:
        st.error("Analysis failed. Please try again.")
        return

    st.subheader(f"Overall Vibe: {critique.get('photo_type', 'N/A')}")
    st.info(f"Wingman Tip: {critique.get('wingman_tip', 'No tip available.')}")
    
    if critique.get('is_slot_appropriate', False):
        st.success("This photo is appropriate for this slot. Good choice!")
    else:
        st.error("This photo is NOT recommended for this slot. See checklist below.")

    st.markdown("---")
    st.markdown("#### Deep Audit Checklist")
    
    checklist = critique.get('pass_fail_checklist', [])
    if not checklist:
        st.write("No checklist data returned from analysis.")
        return
        
    for item in checklist:
        if item.get('pass', False):
            st.write(f"✅ **{item.get('check', 'N/A')}**: {item.get('comment', '')}")
        else:
            st.write(f"❌ **{item.get('check', 'N/A')}**: {item.get('comment', '')}")

# --- 1. THE PHOTO ANALYZER PAGE (Path A) ---
def render_photo_analyzer_page():
    """Renders the 6-slot photo uploader and analysis UI."""
    st.title("The AI Photo Analyzer")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    st.info("Upload your photos in the *exact order* you plan to use them. The critique changes depending on the slot!")

    # Use tabs for a clean 6-slot UI
    tab_list = st.tabs([f"Photo {i}" for i in range(1, 7)])
    
    for i, tab in enumerate(tab_list, 1):
        with tab:
            st.subheader(f"Upload Your *Intended* Photo #{i}")
            
            # Define keys for this tab
            uploader_key = f"uploader_{i}"
            button_key = f"button_{i}"
            critique_key = f"critique_{i}"
            
            uploaded_file = st.file_uploader(f"Slot {i}", type=["jpg", "jpeg", "png"], key=uploader_key)
            
            if uploaded_file:
                st.image(uploaded_file, caption=f"Your uploaded photo for slot {i}")
                
                if st.button(f"Analyze Photo {i}", key=button_key, use_container_width=True, type="primary"):
                    with st.spinner(f"Your wingman is analyzing Photo {i}..."):
                        try:
                            image_bytes = uploaded_file.getvalue()
                            api_key = st.secrets["OPENAI_API_KEY"]
                            critique_json = llm_generator.analyze_photo(api_key, image_bytes, i)
                            st.session_state[critique_key] = critique_json
                        except Exception as e:
                            st.error(f"Failed to analyze: {e}")
                            st.session_state[critique_key] = None
                
                # Render the critique card if it exists in the session state
                if st.session_state[critique_key]:
                    st.markdown("---")
                    st.subheader(f"Analysis for Photo {i}")
                    render_critique_card(st.session_state[critique_key])

# --- 2. THE DIY PHOTO GUIDE PAGE (Path B) ---
def render_photo_guide_page():
    """Renders the 'Digital Magazine' style guide."""
    st.title("The DIY Photoshoot Guide")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    if "guide_page" not in st.session_state:
        st.session_state.guide_page = 1

    page = st.session_state.guide_page

    # --- Page Content ---
    if page == 1:
        st.subheader("Page 1: The Philosophy")
        st.markdown(
            """
            Welcome to the guide. Your notes are clear on what women are *actually* looking for when they swipe:
            
            1.  **"What does he look like?"** (This is about CLARITY)
            2.  **"How will my life fit into his?"** (This is about LIFESTYLE)
            
            Your profile's job is to answer both. Your first 3 photos answer question #1. Your last 3 photos answer question #2.
            """
        )
        st.image("https://placehold.co/600x300/E2E8F0/4A5568?text=Image+of+clear+headshot+vs+lifestyle+shot", caption="Clarity first, lifestyle second.")

    elif page == 2:
        st.subheader("Page 2: Mastering 'The Date Photos' (Photos 1-3)")
        st.markdown(
            """
            Your first 3 photos are your most important. The goal is to answer "What does he look like?" clearly and attractively.
            
            #### The "1st Photo Commandments" (DO NOT BREAK)
            * ❌ **NO Sunglasses.** They want to see your eyes.
            * ❌ **NO Group Pics.** They don't want to play "Where's Waldo?"
            * ❌ **NO Selfies.** (Especially mirror, gym, or car selfies).
            * ❌ **NO Old Pics.** If it's 4+ years old, it's a lie.
            * ❌ **NO Face Shielding.** (Hats, ski masks, pets in front of your face).
            
            #### What TO Do
            * ✅ **Smile *with teeth***. A "half-smirk" is low energy.
            * ✅ **Look off-camera** (like you're talking to someone at "10 or 2 o'clock").
            * ✅ **Wear a 1st date outfit.** A suit, blazer, or stylish layers work perfectly.
            * ✅ **Get a "paparazzi" style shot.** Have a friend take it, make it look natural.
            """
        )
        st.image("https://placehold.co/600x300/E2E8F0/4A5568?text=Image+of+a+man+in+a+suit+smiling", caption="A perfect 'Photo 1' is clear, stylish, and has no sunglasses.")

    elif page == 3:
        st.subheader("Page 3: Mastering 'The Lifestyle Photos' (Photos 4-6)")
        st.markdown(
            """
            Now you've shown what you look like, it's time to show *who you are*.
            
            #### The "Awe Factor" (Use *one* of these)
            * **The Pet Pic:** One pic with your dog or cat is great. *Do not* make it a boring selfie. Make it an *activity* (e.g., hiking with your dog).
            * **The Family Pic:** A photo with your mom or grandma shows your "heart of gold."
            
            #### The "Hobby / Activity" Shot
            * This is where you show "intriguing lifestyle." Are you on a stage? Hiking? Playing guitar?
            * **The *Only* Time a Shirtless Pic is OK:** If it's an *activity* (beach volleyball, swimming, surfing). A "try-hard" gym or mirror selfie is an automatic RED FLAG.
            
            #### The "Social" Shot
            * You can have *one* group pic here (in slots 4-6).
            * **Rules:** The group must be small (< 5 people) and it MUST be obvious which one is you.
            """
        )
        st.image("https://placehold.co/600x300/E2E8F0/4A5568?text=Image+of+man+hiking+with+a+dog", caption="An 'activity' or 'awe factor' shot shows personality.")
        
    elif page == 4:
        st.subheader("Page 4: Your DIY Action Plan")
        st.markdown(
            """
            Ready to shoot? Here's your game plan.
            
            #### 1. The Gear
            * **Light:** A ring light is great. Or, your "free ring light": a big window. **Face the window** when you take the shot.
            * **Lens:** **CLEAN YOUR LENS.** A smudged lens is the #1 killer of good photos.
            
            #### 2. The Timing (Outdoors)
            * **Best:** "Golden Hour" (7-10 AM or 2-3 PM).
            * **Worst:** High Noon (12 PM). It creates harsh shadows under your eyes. Overcast/cloudy days are also great.
            
            #### 3. The Posing
            * Don't be a "mugshot." Tell your friend (or use a tripod) to "go for movement."
            * Look off-camera, laugh, lean on something, hold a drink.
            
            #### 4. The Plan
            1.  **Get 3-6 outfits.** (Layers, suits, casual, active).
            2.  **Go to 3+ locations.** (A park, a cool coffee shop, a nice balcony).
            3.  **Take 100+ photos.** (Yes, 100. "Done is better than perfect").
            4.  **Edit them.** Use a free app like VSCO, Lightleap, or Adobe Lightroom to make the colors "pop."
            
            When you're done, bring them back to our **"AI Photo Analyzer"** and we'll help you pick the 6 winners.
            """
        )

    # --- Navigation ---
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if page > 1:
            if st.button("< Previous"):
                st.session_state.guide_page -= 1
                st.rerun()
    
    with col2:
        st.write(f"Page {page} of 4")

    with col3:
        if page < 4:
            if st.button("Next >"):
                st.session_state.guide_page += 1
                st.rerun()
        else:
            if st.button("Finish Guide"):
                set_state("triage")
                st.rerun()
