"""
empathySync - Your Compassionate Guide to Healthy AI Relationships
Main Streamlit application entry point
"""

import streamlit as st
import sys
import json
from pathlib import Path
from datetime import datetime, date

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from models.ai_wellness_guide import WellnessGuide
from utils.helpers import setup_logging, validate_environment
from utils.wellness_tracker import WellnessTracker

# Configure page
st.set_page_config(
    page_title="empathySync",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_chat_interface(wellness_mode):
    """Display the main chat interface"""

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What are you thinking through?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Reflecting..."):
                response = st.session_state.wellness_guide.generate_response(
                    prompt,
                    wellness_mode,
                    st.session_state.messages
                )
                st.markdown(response)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})


def main():
    """Main application function"""
    
    # Setup logging
    setup_logging()
    
    # Validate environment
    missing_config = validate_environment()
    if missing_config:
        st.error("Configuration Required")
        st.markdown("Please configure these environment variables in your `.env` file:")
        for config in missing_config:
            st.code(f"{config}=your_value_here")
        st.markdown("See `.env.example` for guidance.")
        return
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "wellness_guide" not in st.session_state:
        st.session_state.wellness_guide = WellnessGuide()
    if "wellness_tracker" not in st.session_state:
        st.session_state.wellness_tracker = WellnessTracker()
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now()
    
    # Header
    st.markdown("# empathySync")
    st.markdown("*Help that knows when to stop*")
    
    # Sidebar - minimal, manifesto-aligned
    with st.sidebar:
        # Conversation style selector
        st.markdown("**Style**")
        wellness_mode = st.selectbox(
            "Communication style",
            ["Gentle", "Direct", "Balanced"],
            index=2,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Usage health strip - lightweight session awareness
        summary = st.session_state.wellness_tracker.get_wellness_summary()
        sessions_today = summary.get("sessions_today", 0)
        if sessions_today > 0:
            st.caption(f"Sessions today: {sessions_today}")
            if sessions_today >= 5:
                st.warning("Consider a break or talking to someone you trust.")

        # Reality check button - from manifesto
        if st.button("Reality check", use_container_width=True, help="Am I relying on this too much?"):
            st.session_state.show_reality_check = True

        if st.session_state.get("show_reality_check"):
            st.markdown("---")
            st.markdown("**Pause and reflect:**")
            st.markdown(
                "This is software, not a person. It reflects patterns in text—"
                "it doesn't know you, care about you, or have your best interests at heart."
            )
            recent_sessions = summary.get("total_sessions", 0)
            if recent_sessions > 0:
                st.caption(f"You've had {recent_sessions} sessions recently.")
            st.markdown("Who in your life could you talk to about what's on your mind?")
            if st.button("Got it", use_container_width=True):
                st.session_state.show_reality_check = False
                st.rerun()

        st.markdown("---")

        # Bring someone in - human handoff
        with st.expander("Bring someone in"):
            st.markdown("Share a summary with someone you trust:")
            if st.session_state.messages:
                # Generate simple summary of conversation topics
                user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
                summary_text = f"I've been thinking about: {user_msgs[-1][:100]}..." if user_msgs else "I've been reflecting on some things."
                st.text_area("Message to copy:", value=f"Hey, {summary_text}\n\nCould we talk?", height=100)
            else:
                st.caption("Start a conversation first.")

        st.markdown("---")

        # Controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Chat", use_container_width=True):
                if hasattr(st.session_state, 'session_start'):
                    duration = (datetime.now() - st.session_state.session_start).total_seconds() / 60
                    st.session_state.wellness_tracker.add_session(int(duration))
                st.session_state.messages = []
                st.session_state.session_start = datetime.now()
                st.session_state.show_reality_check = False
                st.rerun()
        with col2:
            if st.button("Export", use_container_width=True):
                data = st.session_state.wellness_tracker._load_data()
                st.download_button(
                    "Download",
                    data=json.dumps(data, indent=2),
                    file_name=f"empathysync_{date.today()}.json",
                    mime="application/json"
                )

        st.markdown("---")
        st.caption("Local-first. Your data stays on your device.")
    
    # Main chat interface
    display_chat_interface(wellness_mode)


if __name__ == "__main__":
    main()
