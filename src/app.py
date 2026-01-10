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
    if prompt := st.chat_input("Share what's on your mind about AI and technology..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking compassionately..."):
                # OPTION 1: positional args (simplest)
                response = st.session_state.wellness_guide.generate_response(
                    prompt,                 # user_input
                    wellness_mode,          # wellness_mode
                    st.session_state.messages  # conversation_history
                )

                # OPTION 2: named args (if you prefer)
                # response = st.session_state.wellness_guide.generate_response(
                #     user_input=prompt,
                #     wellness_mode=wellness_mode,
                #     conversation_history=st.session_state.messages
                # )

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
    
    # Header with wellness context
    st.markdown("# empathySync")
    st.markdown("*Your compassionate guide to healthy AI relationships*")
    
    # Sidebar with comprehensive wellness features
    with st.sidebar:
        st.markdown("## Daily Wellness Check")
        
        # Daily check-in section
        today_checkin = st.session_state.wellness_tracker.get_today_check_in()
        
        if not today_checkin:
            st.markdown("**How do you feel about your AI use today?**")
            
            feeling_mapping = {
                1: "Overwhelmed", 
                2: "Concerned", 
                3: "Balanced", 
                4: "Comfortable", 
                5: "Empowered"
            }
            
            feeling = st.select_slider(
                "Wellness Scale",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: feeling_mapping[x],
                value=3,
                help="Rate how you feel about your relationship with AI today"
            )
            
            notes = st.text_input(
                "Optional reflection", 
                placeholder="Any specific thoughts or concerns?",
                help="Share what's on your mind about technology use"
            )
            
            if st.button("Check In", use_container_width=True):
                checkin = st.session_state.wellness_tracker.add_check_in(feeling, notes)
                st.success(f"Thank you for checking in! Feeling: {feeling_mapping[feeling]}")
                st.rerun()
        else:
            # Show today's check-in
            st.success(f"Today's check-in: {today_checkin['feeling_score']}/5")
            if today_checkin.get('notes'):
                st.info(f"Your reflection: {today_checkin['notes']}")
        
        st.markdown("---")
        
        # Wellness summary
        summary = st.session_state.wellness_tracker.get_wellness_summary()
        if summary.get("days_active", 0) > 0:
            st.markdown("**Your Wellness Journey**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Check-ins", summary["total_checkins"])
            with col2:
                st.metric("Days Active", summary["days_active"])
            
            if summary.get("average_feeling"):
                feeling_color = "green" if summary["average_feeling"] >= 3.5 else "orange" if summary["average_feeling"] >= 2.5 else "red"
                st.markdown(f"**Average Feeling:** :{feeling_color}[{summary['average_feeling']}/5]")
        
        st.markdown("---")
        
        # Conversation settings
        st.markdown("**Conversation Style**")
        wellness_mode = st.selectbox(
            "How should empathySync communicate?",
            ["Gentle", "Direct", "Balanced"],
            index=2,
            help="Choose the communication style that feels right for you today"
        )
        
        # Recent check-ins history
        recent = st.session_state.wellness_tracker.get_recent_check_ins(5)
        if recent:
            st.markdown("**Recent Check-ins**")
            for checkin in recent[-3:]:  # Show last 3
                date_str = checkin['date']
                score = checkin['feeling_score']
                st.caption(f"{date_str}: {score}/5")
        
        st.markdown("---")
        
        # Privacy and controls
        st.info("All conversations and data stay on your device")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Chat", use_container_width=True):
                # Track session duration before clearing
                if hasattr(st.session_state, 'session_start'):
                    duration = (datetime.now() - st.session_state.session_start).total_seconds() / 60
                    st.session_state.wellness_tracker.add_session(int(duration))
                
                st.session_state.messages = []
                st.session_state.session_start = datetime.now()
                st.rerun()
        
        with col2:
            if st.button("Export Data", use_container_width=True):
                # Simple data export feature
                data = st.session_state.wellness_tracker._load_data()
                st.download_button(
                    "Download wellness data",
                    data=json.dumps(data, indent=2),
                    file_name=f"empathysync_data_{date.today()}.json",
                    mime="application/json"
                )
    
    # Main chat interface
    display_chat_interface(wellness_mode)


if __name__ == "__main__":
    main()
