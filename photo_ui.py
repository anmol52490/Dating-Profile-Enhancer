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
    st.title("The AI Photo Smart-Sorter")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    st.info("Upload your photos. We'll tell you if they're good and **where** they belong.")

    # --- 1. Initialize Session State for Summaries ---
    # We use this to store the text descriptions for the final audit
    if "photo_summaries" not in st.session_state:
        st.session_state.photo_summaries = {}

    # --- 2. Render Tabs ---
    tab_list = st.tabs([f"Slot {i}" for i in range(1, 7)])
    
    for i, tab in enumerate(tab_list, 1):
        with tab:
            st.subheader(f"Candidate for Slot {i}")
            
            # Unique keys for widgets
            uploader_key = f"uploader_{i}"
            btn_key = f"analyze_btn_{i}"
            result_key = f"photo_result_{i}"
            
            uploaded_file = st.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"], key=uploader_key)
            
            if uploaded_file:
                st.image(uploaded_file, caption=f"uploaded image", width=300)
                
                if st.button(f"Analyze Photo {i}", key=btn_key, type="primary"):
                    with st.spinner("Sorting and analyzing..."):
                        try:
                            api_key = st.secrets["OPENAI_API_KEY"]
                            image_bytes = uploaded_file.getvalue()
                            
                            # Call LLM
                            result = llm_generator.analyze_photo(api_key, image_bytes, i)
                            
                            # Store result in session state
                            st.session_state[result_key] = result
                            
                            # Store the visual description for the holistic review
                            if result and "visual_description" in result:
                                st.session_state.photo_summaries[i] = result["visual_description"]
                                
                        except Exception as e:
                            st.error(f"Error: {e}")

                # --- Display Results ---
                if result_key in st.session_state and st.session_state[result_key]:
                    data = st.session_state[result_key]
                    
                    # Top Row: Category & Quality
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Detected Category", data.get("photo_category", "Unknown"))
                    with c2:
                        # Color-code quality
                        q_score = data.get("quality_critique", {}).get("score", "Medium")
                        st.metric("Quality Score", q_score)

                    # "Best Slot" Logic
                    best_slots = data.get("best_suited_for_slots", [])
                    if i in best_slots:
                        st.success(f"✅ Perfect! This photo belongs in Slot {i}.")
                    else:
                        st.warning(f"⚠️ Good photo, but maybe better for Slot {best_slots}?")

                    # Description & Critique
                    st.write(f"**AI Sees:** *{data.get('visual_description')}*")
                    st.info(f"**Critique:** {data.get('quality_critique', {}).get('reason')}")

                    # Flags (Clean UI)
                    red_flags = data.get("red_flags", [])
                    green_flags = data.get("green_flags", [])
                    
                    if red_flags:
                        st.error(f"**Fix These:** {', '.join(red_flags)}")
                    if green_flags:
                        st.success(f"**Winning Traits:** {', '.join(green_flags)}")

    # --- 3. The Holistic Review Section ---
    st.markdown("---")
    st.subheader("🔍 Full Profile Audit")
    
    # Check if we have enough data (e.g., 3+ photos analyzed)
    photos_analyzed_count = len(st.session_state.photo_summaries)
    
    if photos_analyzed_count < 6:
        st.caption(f"Analyze all photos to unlock the full profile review. (Current: {photos_analyzed_count}/6)")
        st.button("Audit My Profile Flow", disabled=True)
    else:
        st.write("Ready to check your profile flow? We'll look for variety and storytelling.")
        if st.button("Audit My Profile Flow", type="primary"):
            with st.spinner("Reading your profile story..."):
                api_key = st.secrets["OPENAI_API_KEY"]
                # Send the text summaries to the LLM
                audit_text = llm_generator.audit_profile_flow(st.session_state.photo_summaries, api_key)
                
                st.success("Audit Complete!")
                with st.container(border=True):
                    st.markdown(audit_text)
# --- 2. THE DIY PHOTO GUIDE PAGE (Path B) ---
# In photo_ui.py

def render_photo_guide_page():
    """Renders the 'Digital Magazine' style guide based on PDF notes."""
    st.title("The DIY Photoshoot Guide")
    st.button("Back to Home", on_click=set_state, args=["triage"])
    st.markdown("---")
    
    if "guide_page" not in st.session_state:
        st.session_state.guide_page = 1

    page = st.session_state.guide_page

    # --- Page 1: Philosophy ---
    if page == 1:
        st.subheader("Page 1: The Philosophy")
        st.info("Your photos should be divided into 2 categories: 1. Headshots and 2. Lifestyle.")
        st.markdown(
            """
            **1. Notes on Headshots:**
            * Your first 1-2 photos should be a headshot.
            * Headshots should make up the majority of your photos (at least 3).
            * **Rule:** Viewer should be able to see your face clearly with good lighting.
            * **Framing:** Cropped chest-high at the bottom and slightly above your head at the top.
            * **Expression:** Looking at the camera or slightly off. Smiling with teeth!

            **2. Notes on Lifestyle:**
            * Photos where you are demonstrating competency in a certain area or "awe factor" (showcasing a cute dog etc.) work best.
            * **Group Photos:** It's okay to have group photos, but only 1-2. They must be listed towards the back, and the viewer must clearly identify who you are.
            * **Goal:** Showcasing hobbies, passions, and people you like to have fun with.
            """
        )
        # Keep your existing image placeholder or update if you have the specific drive images
        st.image("1.png", caption="Structure your profile correctly.")

    # --- Page 2: How to Take Better Photos ---
    elif page == 2:
        st.subheader("Page 2: How to Take Better Dating Profile Photos")
        st.markdown(
            """
            **What TO DO:**
            * ✅ **Smile with teeth!** A "half-smirk" is low energy. (Pro-tip: Do a round of Crest White Strips to make them pop).
            * ✅ **Eye Contact:** Look to the camera or look off-camera (like you're talking to someone at "10 or 2 o'clock").
            * ✅ **Style:** Look nice! A suit, blazer, or stylish layers work perfectly.
            * ✅ **The Vibe:** Get a "paparazzi" style shot. Have a friend take it, make it look natural.
            """
        )
        st.image("3.png", caption="Smile your way to heart.")

    # --- Page 3: The Gear & Timing ---
    elif page == 3:
        st.subheader("Page 3: The Gear & Timing")
        st.markdown(
            """
            **1. The Gear**
            * **Light:** A ring light with a clicker is great. Or, your "free ring light": a big window. Face the window when you take the shot.
            * **Lens:** **CLEAN YOUR LENS.** A smudged lens is the #1 killer of good photos.

            **2. The Timing (Outdoors)**
            * 🌟 **Best:** "Golden Hour" (7-10 AM or 2-3 PM).
            * ❌ **Worst:** High Noon (12 PM). It creates harsh shadows under your eyes. Overcast/cloudy days are also great.

            **3. The Posing**
            * Don't be a "mugshot." Tell your friend (or use a tripod) to **"go for movement."**
            * Look on or slightly off-camera, laugh, lean on something.
            * **Prop:** Use a prop like holding a drink or fixing your sleeve (indicating slight movement).
            """
        )
        
    # --- Page 4: The Action Plan ---
    elif page == 4:
        st.subheader("Page 4: Your DIY Action Plan")
        st.markdown(
            """
            **The Plan:**
            1.  Get 3-6 outfits. (Layers, suits, casual, active).
            2.  Go to 3+ locations. (A park, a cool coffee shop, a nice balcony).
            3.  Take 100+ photos. (Yes, 100. "Done is better than perfect").
            4.  Edit them. Use a free app like VSCO, Lightleap, or Adobe Lightroom to make the colors "pop."
            
            **Technique:**
            * **If using a friend:** Show them good example photos first so they understand the vibe. Best for lifestyle shots.
            * **If using a ring light:** Stand facing natural light. Use multiple outfits and angles so it looks like different days. Best for sharp headshots.

            **Next Step:**
            When you're done, bring them back to our **"AI Photo Analyzer"** and we'll help you pick the 6 winners.
            """
        )

    # --- Navigation (Keep existing) ---
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