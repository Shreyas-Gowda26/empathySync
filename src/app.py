"""
empathySync - Your Compassionate Guide to Healthy AI Relationships
Main Streamlit application entry point
"""

import streamlit as st
import sys
from pathlib import Path

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
    
    # Header
    st.markdown("#  empathySync")
    st.markdown("*Your compassionate guide to healthy AI relationships*")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## Settings")
        
        # Wellness mode selection
        wellness_mode = st.selectbox(
            "Conversation Style",
            ["Gentle", "Direct", "Balanced"],
            index=2,
            help="Choose how empathySync communicates with you"
        )
        
        # Privacy reminder
        st.info(" All conversations stay on your device")
        
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
