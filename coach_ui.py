import streamlit as st
import chatbot  # Import our RAG engine
import base64
from pathlib import Path

def set_state(state):
    st.session_state.app_state = state

# --- WHATSAPP DARK MODE CSS ---
def apply_whatsapp_css():
    st.markdown("""
    <style>
    /* 1. Global Reset */
    .stApp { background-color: #0b141a; }
    .stDeployButton, footer, header { visibility: hidden; }
    
    /* 2. Chat Bubbles */
    .stChatMessage { background-color: transparent !important; border: none !important; }

    /* User (Right) */
    [data-testid="stChatMessage"][data-test-tag="user"] { flex-direction: row-reverse; text-align: right; justify-content: flex-end; }
    [data-testid="stChatMessage"][data-test-tag="user"] .stMarkdown { background-color: #005c4b; color: white; padding: 10px 15px; border-radius: 10px 0px 10px 10px; max-width: 80%; display: inline-block; text-align: left; }

    /* Bot (Left) */
    [data-testid="stChatMessage"][data-test-tag="assistant"] { flex-direction: row; text-align: left; }
    [data-testid="stChatMessage"][data-test-tag="assistant"] .stMarkdown { background-color: #202c33; color: white; padding: 10px 15px; border-radius: 0px 10px 10px 10px; max-width: 80%; display: inline-block; }

    /* 3. Hide Avatars */
    .stChatMessageAvatar { display: none; }

    /* --- THE FIX IS HERE --- */

    /* 4. PIN INPUT TO BOTTOM */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 50 !important;
        width: 50% !important;
        background-color: #0b141a !important; /* Matches background so it's seamless */
        z-index: 00 !important;
        padding-bottom: 20px !important;
        padding-top: 10px !important;
        border-top: 1px solid #202c33;
    }

    /* 5. ADD PADDING TO PAGE so last message isn't hidden */
    .block-container {
        padding-bottom: 120px !important;
    }
    
    /* 6. Hide 'Stop' button to keep it clean */
    button[kind="header"] { display: none; }
    
    </style>
    """, unsafe_allow_html=True)

def get_image_base64(image_path):
    """Convert local image to base64 string."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

def render_coach_page():
    apply_whatsapp_css()
    
    # --- HEADER ---
    c1, c2, c3 = st.columns([1, 8, 2])
    with c1:
        # Female Avatar
        st.image("https://avatar.iran.liara.run/public/92", width=50) 
    with c2:
        st.subheader("Jamie (Wingman)")
        st.caption("Online")
    with c3:
        if st.button("Exit"):
            set_state("triage")
            st.rerun()

    # --- TABS: SEPARATE CHAT FROM CONTENT ---
    tab_chat, tab_learn = st.tabs(["💬 Chat", "📘 The Playbook"])

    # --- TAB 1: THE CHATBOT ---
    with tab_chat:
        # Initialize History
        if "coach_history" not in st.session_state:
            st.session_state.coach_history = [
                {"role": "assistant", "content": "Yo! It's Jamie. I've got the playbook open. Tell me about her profile or what's on your mind."}
            ]

        # Render Chat Bubbles
        for message in st.session_state.coach_history:
            role = message["role"]
            with st.chat_message(role):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Type a message..."):
            # 1. User Message
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.coach_history.append({"role": "user", "content": prompt})

            # 2. Bot Response
            with st.chat_message("assistant"):
                response_text = chatbot.coach_bot.get_response(prompt, st.session_state.coach_history)
                st.markdown(response_text)
            
            # 3. Save History
            st.session_state.coach_history.append({"role": "assistant", "content": response_text})

    # --- TAB 2: THE MASTERCLASS (STRATEGIES) ---
    with tab_learn:
        st.info("Reference these strategies while you chat.")
        
        with st.expander("Strategy 1: Yes And..."):
            st.write("**Concept:** Agree + Exaggerate.")
            st.caption("Her: 'I like travel.'")
            st.caption("You: 'Perfect. Looking for someone to share questionable airport snacks with.'")
            
        with st.expander("Strategy 2: Together/We Frame"):
            st.write("**Concept:** Playful presumption of a relationship.")
            st.caption("You: 'We would either get along perfectly or burn the city down.'")
            
        with st.expander("Strategy 3: False Time Constraint"):
            st.write("**Concept:** Lower pressure immediately.")
            st.caption("Start with: 'Hey, real quick...'")
            
        with st.expander("Strategy 4: Inner Game"):
            st.write("**Mindset:** You aren't trying to 'get' anything. You are just checking if she's cool.")
            
        st.markdown("---")
        st.markdown("### 🎓 Want the full course?")

        # Convert image to base64 and make it clickable
        img_base64 = get_image_base64("banter_blueprint.png")

        if img_base64:
            st.markdown(f"""
            <a href="https://jamie-date.mykajabi.com/the-banter-blueprint-new" target="_blank">
                <img src="data:image/png;base64,{img_base64}" 
                 style="width: 100%; cursor: pointer; border-radius: 8px;" 
                 alt="The Banter Blueprint">
            </a>
            """, unsafe_allow_html=True)
        else:
            st.error("Image not found. Please check the file path.")

        st.markdown("[**Get The Full Banter Blueprint Here**](https://jamie-date.mykajabi.com/the-banter-blueprint-new)")