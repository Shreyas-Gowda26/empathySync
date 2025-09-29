"""
empathySync - Your Compassionate Guide to Healthy AI Relationships
Main Streamlit application entry point
"""

import streamlit as st
import sys
from pathlib import Path
from utils.wellness_tracker import WellnessTracker


# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from models.ai_wellness_guide import WellnessGuide
from utils.helpers import setup_logging, validate_environment

# Configure page
st.set_page_config(
    page_title="empathySync",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add this import at the top
from utils.wellness_tracker import WellnessTracker

# Update the main() function to include wellness tracker
def main():
    """Main application function"""
    
    # Setup logging
    setup_logging()
    
    # Validate environment
    missing_config = validate_environment()
    if missing_config:
        st.error(" Configuration Required")
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
    
    # Header
    st.markdown("# 🤝 empathySync")
    st.markdown("*Your compassionate guide to healthy AI relationships*")
    
    # Sidebar with wellness features
    with st.sidebar:
        st.markdown("## 🧘 Wellness Check")
        
        # Daily check-in
        today_checkin = st.session_state.wellness_tracker.get_today_check_in()
        
        if not today_checkin:
            st.markdown("**How are you feeling about your AI use today?**")
            feeling = st.select_slider(
                "Feeling Scale",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "😟 Overwhelmed", 
                    2: "😐 Concerned", 
                    3: "😊 Balanced", 
                    4: "😌 Comfortable", 
                    5: "🌟 Empowered"
                }[x],
                value=3
            )
            
            notes = st.text_input("Optional notes", placeholder="Any specific concerns?")
            
            if st.button(" Check In"):
                st.session_state.wellness_tracker.add_check_in(feeling, notes)
                st.success("Thanks for checking in! 🙏")
                st.rerun()
        else:
            st.success(f" Today's check-in: {today_checkin['feeling_score']}/5")
            if today_checkin.get('notes'):
                st.info(f"Notes: {today_checkin['notes']}")
        
        st.markdown("---")
        
        # Conversation style
        wellness_mode = st.selectbox(
            "Conversation Style",
            ["Gentle", "Direct", "Balanced"],
            index=2,
            help="Choose how empathySync communicates with you"
        )
        
        # Recent check-ins
        recent = st.session_state.wellness_tracker.get_recent_check_ins(7)
        if recent:
            st.markdown("**Recent Check-ins**")
            for checkin in recent[-3:]:  # Show last 3
                date_str = checkin['date']
                score = checkin['feeling_score']
                st.caption(f"{date_str}: {score}/5")
        
        # Privacy reminder
        st.info(" All data stays on your device")
        
        # Clear conversation
        if st.button("Start Fresh Conversation"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    display_chat_interface(wellness_mode)


def display_chat_interface(wellness_mode: str):
    """Display the main chat interface"""
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("How are you feeling about your AI usage today?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking with empathy..."):
                try:
                    response = st.session_state.wellness_guide.generate_response(
                        prompt, 
                        wellness_mode,
                        st.session_state.messages
                    )
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Sorry, I'm having trouble connecting. Please check your Ollama setup: {str(e)}")

if __name__ == "__main__":
    main()
