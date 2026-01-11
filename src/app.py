"""
empathySync - Help that knows when to stop
Main Streamlit application entry point

Core principle: Optimize for exit, not engagement.
Bridge people back to human connection.
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
from utils.trusted_network import TrustedNetwork

# Configure page
st.set_page_config(
    page_title="empathySync",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_safety_banner():
    """Display session safety banner when guardrails are active."""
    guide = st.session_state.wellness_guide

    if guide.last_policy_action:
        action = guide.last_policy_action
        policy_type = action.get("type", "")
        domain = action.get("domain", "")

        explanations = {
            "crisis_stop": "I detected crisis language and redirected to professional resources.",
            "harmful_stop": "I declined to engage with potentially harmful content.",
            "turn_limit_reached": f"We've reached the conversation limit for {domain} topics. This is by design.",
            "dependency_intervention": "I noticed a pattern that suggests it might be healthy to step back.",
            "high_risk_response": f"This topic ({domain}) involves significant decisions. My responses are shorter and I'm suggesting human guidance.",
            "cooldown_enforced": "Based on your usage pattern, I'm suggesting a break."
        }

        explanation = explanations.get(policy_type, "A safety guardrail was activated.")
        st.info(f"**Why I responded this way:** {explanation}")


def display_usage_health():
    """Display usage health indicators in sidebar."""
    tracker = st.session_state.wellness_tracker
    summary = tracker.get_wellness_summary()

    sessions_today = summary.get("sessions_today", 0)
    minutes_today = summary.get("minutes_today", 0)
    dependency_score = summary.get("dependency_score", 0)

    if sessions_today > 0 or minutes_today > 0:
        st.caption(f"Today: {sessions_today} sessions, {minutes_today} min")

    if dependency_score >= 7:
        st.error("Consider taking a break. Your usage pattern suggests over-reliance.")
    elif dependency_score >= 5:
        st.warning("You've been here often. Consider talking to someone you trust.")
    elif sessions_today >= 3:
        st.caption("Multiple sessions today. How are you feeling about that?")

    if tracker.is_late_night_session():
        st.caption("It's late. Consider whether this can wait until tomorrow.")


def display_trusted_network_setup():
    """Display trusted network setup panel."""
    network = st.session_state.trusted_network

    st.markdown("### Your Trusted People")
    st.markdown("*Who could you call if things got hard?*")

    people = network.get_all_people()

    if people:
        for person in people:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{person['name']}**")
                if person.get('relationship'):
                    st.caption(person['relationship'])
            with col2:
                if st.button("Remove", key=f"remove_{person['id']}", type="secondary"):
                    network.remove_person(person['id'])
                    st.rerun()
    else:
        st.caption("No one added yet.")
        prompt = network.get_setup_prompt()
        st.markdown(f"*{prompt}*")

    st.markdown("---")
    st.markdown("**Add someone:**")

    with st.form("add_person", clear_on_submit=True):
        name = st.text_input("Name", placeholder="e.g., Mom, Jake, Dr. Smith")
        relationship = st.text_input("Relationship", placeholder="e.g., friend, sister, therapist")
        contact = st.text_input("How to reach them", placeholder="e.g., phone, usually free evenings")

        domains = st.multiselect(
            "Good for talking about",
            ["relationships", "money", "health", "spirituality", "general"],
            default=["general"]
        )

        if st.form_submit_button("Add"):
            if name:
                network.add_person(name, relationship, contact, domains=domains)
                st.success(f"Added {name}")
                st.rerun()


def display_bring_someone_in(domain: str = "general"):
    """Enhanced human handoff panel."""
    network = st.session_state.trusted_network
    people = network.get_all_people()

    st.markdown("### Bring Someone In")

    # Suggest someone if we have people
    if people:
        suggested = network.suggest_person_for_domain(domain)
        if suggested:
            st.markdown(f"**Consider reaching out to:** {suggested['name']}")
            if suggested.get('relationship'):
                st.caption(suggested['relationship'])
    else:
        prompt = network.get_domain_prompt(domain)
        st.markdown(f"*{prompt}*")

    st.markdown("---")

    # Template selection
    st.markdown("**Need help starting the conversation?**")

    template_type = st.selectbox(
        "What kind of message?",
        ["need_to_talk", "reconnecting", "checking_in", "hard_conversation", "asking_for_help"],
        format_func=lambda x: {
            "need_to_talk": "I need to talk",
            "reconnecting": "Reconnecting after silence",
            "checking_in": "Just checking in",
            "hard_conversation": "Starting a hard conversation",
            "asking_for_help": "Asking for help"
        }.get(x, x),
        label_visibility="collapsed"
    )

    template = network.get_reach_out_template(template_type)

    # Build message with context from conversation
    if st.session_state.messages:
        user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        if user_msgs:
            context = user_msgs[-1][:100]
            full_message = f"{template['template']}\n\nI've been thinking about: {context}..."
        else:
            full_message = template['template']
    else:
        full_message = template['template']

    message = st.text_area(
        "Message to send:",
        value=full_message,
        height=120,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copy message", use_container_width=True):
            st.code(message)
            st.caption("Copy the text above")

    with col2:
        if st.button("I reached out!", use_container_width=True, type="primary"):
            # Log the reach out
            person_name = suggested['name'] if people and suggested else "someone"
            network.log_reach_out(person_name, method="message", topic=domain)

            # Show exit celebration
            celebration = network.get_exit_celebration(chose_human=True)
            st.success(celebration)
            st.balloons()


def display_reality_check():
    """Display the reality check panel."""
    tracker = st.session_state.wellness_tracker
    network = st.session_state.trusted_network

    signals = tracker.calculate_dependency_signals()
    connection_health = network.get_connection_health()

    st.markdown("---")
    st.markdown("### Pause and reflect")

    st.markdown(
        "**This is software, not a person.** It reflects patterns in text—"
        "it doesn't know you, care about you, or have your best interests at heart. "
        "It's a tool for thinking, not a companion or advisor."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Your AI usage:**")
        st.metric("Sessions today", signals["sessions_today"])
        st.metric("This week", signals["sessions_this_week"])
        if signals["late_night_sessions"] > 0:
            st.metric("Late night sessions", signals["late_night_sessions"])

    with col2:
        st.markdown("**Your human connection:**")
        st.metric("Trusted people saved", connection_health["total_trusted_people"])
        st.metric("Reach outs this week", connection_health["reach_outs_this_week"])
        if connection_health["neglected_contacts"] > 0:
            st.metric("Haven't contacted lately", connection_health["neglected_contacts"])

    if signals["warnings"]:
        st.markdown("---")
        st.markdown("**Patterns I notice:**")
        for warning in signals["warnings"]:
            st.markdown(f"- {warning}")

    # Reflection prompt
    st.markdown("---")
    reflection = network.get_reflection_prompt()
    st.markdown(f"**Ask yourself:** *{reflection}*")

    st.markdown("---")
    if st.button("I understand", use_container_width=True):
        st.session_state.show_reality_check = False
        st.rerun()


def display_chat_interface(wellness_mode):
    """Display the main chat interface."""
    guide = st.session_state.wellness_guide
    tracker = st.session_state.wellness_tracker
    network = st.session_state.trusted_network

    # Check for cooldown
    should_cooldown, cooldown_reason = tracker.should_enforce_cooldown()
    if should_cooldown:
        st.warning(cooldown_reason)

        # Suggest reaching out to someone
        people = network.get_all_people()
        if people:
            import random
            person = random.choice(people)
            st.markdown(f"**Consider calling {person['name']}** instead of being here.")
        else:
            st.markdown("**Consider:** Who could you call right now?")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        return

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Show safety banner if policy fired
    if guide.last_policy_action:
        display_safety_banner()

        # If high-risk domain, suggest specific person
        domain = guide.last_policy_action.get("domain", "")
        if domain in ["relationships", "money", "health", "spirituality"]:
            people = network.get_people_for_domain(domain)
            if people:
                person = people[0]
                st.markdown(f"💡 **You said {person['name']} is good for {domain} topics.** Consider reaching out to them.")

    # Chat input
    if prompt := st.chat_input("What are you thinking through?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(""):
                response = guide.generate_response(
                    prompt,
                    wellness_mode,
                    st.session_state.messages,
                    wellness_tracker=tracker
                )
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        if guide.last_policy_action:
            st.rerun()


def save_session_on_end():
    """Save session data when ending conversation."""
    guide = st.session_state.wellness_guide
    tracker = st.session_state.wellness_tracker

    if hasattr(st.session_state, 'session_start'):
        duration = (datetime.now() - st.session_state.session_start).total_seconds() / 60
        session_summary = guide.get_session_summary()

        tracker.add_session(
            duration_minutes=int(duration),
            turn_count=session_summary["turn_count"],
            domains_touched=session_summary["domains_touched"],
            max_risk_weight=session_summary["max_risk_weight"]
        )


def main():
    """Main application function"""

    setup_logging()

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
    if "trusted_network" not in st.session_state:
        st.session_state.trusted_network = TrustedNetwork()
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now()
    if "show_reality_check" not in st.session_state:
        st.session_state.show_reality_check = False
    if "show_network_setup" not in st.session_state:
        st.session_state.show_network_setup = False

    # Header
    st.markdown("# empathySync")
    st.markdown("*Help that knows when to stop*")

    # Check if network is empty - prompt setup
    network = st.session_state.trusted_network
    if not network.get_all_people() and not st.session_state.show_network_setup:
        st.info("**First time?** Consider adding your trusted people—the humans you could actually talk to.")
        if st.button("Set up my trusted network"):
            st.session_state.show_network_setup = True
            st.rerun()

    # Sidebar
    with st.sidebar:
        # Style selector
        st.markdown("**Style**")
        wellness_mode = st.selectbox(
            "Communication style",
            ["Gentle", "Direct", "Balanced"],
            index=2,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Usage health
        display_usage_health()

        st.markdown("---")

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reality check", use_container_width=True,
                         help="Am I relying on this too much?"):
                st.session_state.show_reality_check = True
                st.session_state.show_network_setup = False
                st.rerun()
        with col2:
            if st.button("My people", use_container_width=True,
                         help="Manage trusted network"):
                st.session_state.show_network_setup = True
                st.session_state.show_reality_check = False
                st.rerun()

        # Show appropriate panel
        if st.session_state.get("show_reality_check"):
            display_reality_check()
        elif st.session_state.get("show_network_setup"):
            st.markdown("---")
            display_trusted_network_setup()
            if st.button("Done", use_container_width=True):
                st.session_state.show_network_setup = False
                st.rerun()
        else:
            st.markdown("---")

            # Get current domain if available
            guide = st.session_state.wellness_guide
            current_domain = "general"
            if guide.last_risk_assessment:
                current_domain = guide.last_risk_assessment.get("domain", "general")

            # Bring someone in
            with st.expander("Bring someone in", expanded=False):
                display_bring_someone_in(current_domain)

            # Session info
            if guide.session_turn_count > 0:
                st.caption(f"This session: {guide.session_turn_count} turns")
                if guide.session_domains:
                    domains = ", ".join(guide.session_domains)
                    st.caption(f"Topics: {domains}")

            st.markdown("---")

            # Controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("New Chat", use_container_width=True):
                    save_session_on_end()
                    st.session_state.messages = []
                    st.session_state.session_start = datetime.now()
                    st.session_state.show_reality_check = False
                    st.session_state.wellness_guide.reset_session()
                    st.rerun()
            with col2:
                if st.button("Export", use_container_width=True):
                    tracker = st.session_state.wellness_tracker
                    data = tracker._load_data()
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
