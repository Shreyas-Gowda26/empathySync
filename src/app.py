"""
empathySync - Help that knows when to stop
Main Streamlit application entry point

Core principle: Optimize for exit, not engagement.
Bridge people back to human connection.
"""

import streamlit as st
import sys
import json
import random
from pathlib import Path
from datetime import datetime, date
from typing import Dict

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from models.ai_wellness_guide import WellnessGuide
from models.risk_classifier import (
    RiskClassifier,
    INTENT_PRACTICAL,
    INTENT_PROCESSING,
    INTENT_EMOTIONAL,
    INTENT_CONNECTION,
)
from utils.helpers import setup_logging, validate_environment
from utils.wellness_tracker import WellnessTracker
from utils.trusted_network import TrustedNetwork
from utils.scenario_loader import get_scenario_loader
from utils.health_check import run_health_checks, has_critical_failures

# Configure page
st.set_page_config(
    page_title="empathySync", page_icon="", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS for better visual hierarchy (Phase 9.5)
st.markdown(
    """
<style>
    /* Sidebar section headers */
    .sidebar-header {
        font-size: 0.75rem;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* Better button spacing in sidebar */
    .stButton > button {
        margin-bottom: 0.25rem;
    }

    /* Primary action buttons stand out */
    .stButton > button[kind="primary"] {
        font-weight: 600;
    }

    /* Subtle dividers */
    hr {
        margin: 1rem 0;
        border: none;
        border-top: 1px solid #e0e0e0;
    }

    /* Main title styling */
    h1 {
        margin-bottom: 0 !important;
    }

    /* Subtitle styling */
    .subtitle {
        color: #666;
        font-style: italic;
        margin-top: 0;
    }
</style>
""",
    unsafe_allow_html=True,
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
            "cooldown_enforced": "Based on your usage pattern, I'm suggesting a break.",
        }

        explanation = explanations.get(policy_type, "A safety guardrail was activated.")
        st.info(f"**Why I responded this way:** {explanation}")


def display_transparency_panel():
    """Display the 'Why this response?' transparency panel (Phase 6)."""
    guide = st.session_state.wellness_guide
    loader = get_scenario_loader()

    # Only show if we have risk assessment data
    if not guide.last_risk_assessment:
        return

    assessment = guide.last_risk_assessment
    ui_labels = loader.get_transparency_ui_labels()

    # Get transparency settings
    settings = loader.get_transparency_settings()
    auto_expand = settings.get("auto_expand_on_policy", True)

    # Auto-expand if policy fired
    should_expand = auto_expand and guide.last_policy_action is not None

    with st.expander(ui_labels.get("panel_title", "Why this response?"), expanded=should_expand):
        # Domain detected
        domain = assessment.get("domain", "logistics")
        domain_info = loader.get_domain_explanation(domain)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{ui_labels.get('domain_label', 'Topic detected')}**")
        with col2:
            st.markdown(f"{domain_info.get('name', domain.title())}")
            st.caption(domain_info.get("description", ""))

        st.markdown("---")

        # Response mode
        # Phase 9.1: Check both domain and is_practical_technique flag
        is_practical_technique = assessment.get("is_practical_technique", False)
        is_practical = domain == "logistics" or is_practical_technique
        mode = "practical" if is_practical else "reflective"
        mode_info = loader.get_mode_explanation(mode)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{ui_labels.get('mode_label', 'Response mode')}**")
        with col2:
            st.markdown(f"{mode_info.get('name', mode.title())}")
            # Phase 9.1: Show note if practical technique detected in sensitive domain
            if is_practical_technique and domain != "logistics":
                st.caption(
                    f"Technique question detected in {domain} domain → full response allowed"
                )
            else:
                st.caption(mode_info.get("description", ""))

        # Word limit
        word_limit = ui_labels.get("no_limit", "None") if is_practical else "50-150 words"
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{ui_labels.get('word_limit_label', 'Word limit')}**")
        with col2:
            st.markdown(word_limit)

        st.markdown("---")

        # Emotional weight (for practical tasks)
        if is_practical:
            emotional_weight = assessment.get("emotional_weight", "low_weight")
            weight_info = loader.get_emotional_weight_explanation(emotional_weight)

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{ui_labels.get('emotional_weight_label', 'Emotional weight')}**")
            with col2:
                st.markdown(f"{weight_info.get('name', emotional_weight)}")
                if weight_info.get("note"):
                    st.caption(weight_info.get("note"))

            st.markdown("---")

        # Risk level
        risk_weight = assessment.get("risk_weight", 1.0)
        risk_info = loader.get_risk_level_explanation(risk_weight)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{ui_labels.get('risk_level_label', 'Risk level')}**")
        with col2:
            st.markdown(f"{risk_info.get('name', 'Low')} ({risk_weight:.1f}/10)")
            if risk_info.get("description"):
                st.caption(risk_info.get("description"))

        # Policy action (if any)
        if guide.last_policy_action:
            st.markdown("---")
            policy_type = guide.last_policy_action.get("type", "")
            policy_info = loader.get_policy_explanation(policy_type)

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{ui_labels.get('policy_label', 'Policy action')}**")
            with col2:
                st.markdown(f"{policy_info.get('name', policy_type)}")
                st.caption(policy_info.get("reason", ""))
                if policy_info.get("user_note"):
                    st.info(policy_info.get("user_note"))
        else:
            st.markdown("---")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{ui_labels.get('policy_label', 'Policy action')}**")
            with col2:
                st.markdown(ui_labels.get("none_triggered", "None triggered"))


def display_session_summary():
    """Display the end-of-session summary (Phase 6)."""
    guide = st.session_state.wellness_guide
    tracker = st.session_state.wellness_tracker
    loader = get_scenario_loader()

    summary_config = loader.get_session_summary_config()
    ui_labels = loader.get_transparency_ui_labels()

    # Get session data
    session_summary = guide.get_session_summary()
    turn_count = session_summary.get("turn_count", 0)
    domains_touched = session_summary.get("domains_touched", [])
    max_risk = session_summary.get("max_risk_weight", 0)
    policy_action = session_summary.get("last_policy_action")

    # Calculate duration
    duration_minutes = 0
    if hasattr(st.session_state, "session_start"):
        duration_minutes = int(
            (datetime.now() - st.session_state.session_start).total_seconds() / 60
        )

    # Check thresholds - don't show for very short sessions
    settings = loader.get_transparency_settings()
    min_duration = settings.get("summary_min_duration", 3)
    min_turns = settings.get("summary_min_turns", 2)

    if duration_minutes < min_duration and turn_count < min_turns:
        return

    st.markdown("---")
    st.markdown(f"### {summary_config.get('header', 'Session Summary')}")
    st.caption(summary_config.get("subheader", "Here's what happened in this conversation"))

    sections = summary_config.get("sections", {})

    # Duration
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**{sections.get('duration', {}).get('label', 'Duration')}**")
    with col2:
        st.markdown(f"{duration_minutes} minutes")

    # Turns
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**{sections.get('turns', {}).get('label', 'Exchanges')}**")
    with col2:
        st.markdown(f"{turn_count} turns")

    # Mode breakdown
    practical_turns = sum(1 for d in domains_touched if d == "logistics")
    reflective_turns = len(domains_touched) - practical_turns

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**{sections.get('mode_breakdown', {}).get('label', 'Conversation Type')}**")
    with col2:
        breakdown_parts = []
        if practical_turns > 0:
            breakdown_parts.append(f"{practical_turns} practical")
        if reflective_turns > 0:
            breakdown_parts.append(f"{reflective_turns} reflective")
        st.markdown(", ".join(breakdown_parts) if breakdown_parts else "Mixed")

    # Topics covered
    if domains_touched:
        unique_domains = list(set(domains_touched))
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{sections.get('domains_touched', {}).get('label', 'Topics Covered')}**")
        with col2:
            domain_names = []
            for domain in unique_domains:
                domain_info = loader.get_domain_explanation(domain)
                domain_names.append(domain_info.get("name", domain.title()))
            st.markdown(", ".join(domain_names))

    # Risk level
    risk_info = loader.get_risk_level_explanation(max_risk)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**{sections.get('max_risk', {}).get('label', 'Highest Risk Level')}**")
    with col2:
        st.markdown(f"{risk_info.get('name', 'Low')} ({max_risk:.1f}/10)")

    # Policy actions
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f"**{sections.get('policy_actions', {}).get('label', 'Guardrails Activated')}**"
        )
    with col2:
        if policy_action:
            policy_info = loader.get_policy_explanation(policy_action.get("type", ""))
            st.markdown(policy_info.get("name", "Yes"))
        else:
            st.markdown(sections.get("policy_actions", {}).get("none_message", "None"))

    # Footer message based on session type
    st.markdown("---")
    session_type = "all_practical"
    if reflective_turns > practical_turns:
        session_type = "mostly_reflective"
    elif practical_turns > 0 and reflective_turns > 0:
        session_type = "mixed"
    if policy_action:
        session_type = "policy_fired"
    if duration_minutes > 30:
        session_type = "long_session"

    footer_messages = loader.get_session_summary_footer(session_type)
    if footer_messages:
        st.info(random.choice(footer_messages))

    # Export button
    col1, col2 = st.columns(2)
    with col1:
        export_data = {
            "session_date": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "turn_count": turn_count,
            "domains_touched": list(set(domains_touched)),
            "max_risk_weight": max_risk,
            "policy_action": policy_action.get("type") if policy_action else None,
            "practical_turns": practical_turns,
            "reflective_turns": reflective_turns,
        }
        st.download_button(
            ui_labels.get("export_summary", "Export summary"),
            data=json.dumps(export_data, indent=2),
            file_name=f"session_summary_{date.today()}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        if st.button(ui_labels.get("close_summary", "Close"), use_container_width=True):
            st.session_state.show_session_summary = False
            st.rerun()


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

    # Only show late-night warning if there's a pattern (2+ late sessions this week)
    # Not just for being up late once
    if tracker.is_late_night_session() and tracker.get_late_night_sessions_this_week() >= 2:
        st.caption("You've been here late at night a few times. Everything okay?")


def display_my_patterns_dashboard():
    """
    Display the 'My Patterns' dashboard (Phase 7).

    Shows sensitive vs practical usage trends, anti-engagement score,
    and week-over-week comparisons. Only sensitive usage counts toward
    the reliance score - practical task usage is just using a tool.
    """
    tracker = st.session_state.wellness_tracker
    loader = get_scenario_loader()

    st.markdown("### My Patterns")
    st.markdown("*Track your relationship with this tool*")

    try:
        dashboard = tracker.get_my_patterns_dashboard()
    except Exception as e:
        st.caption("Not enough data yet. Check back after a few sessions.")
        return

    # Summary message based on health status
    health_status = dashboard.get("health_status", "moderate")
    summary = dashboard.get("summary", "")

    if health_status == "healthy":
        st.success(summary)
    elif health_status == "concerning":
        st.warning(summary)
    else:
        st.info(summary)

    st.markdown("---")

    # Week comparison section
    st.markdown("**This Week vs Last Week**")

    this_week = dashboard.get("this_week", {})
    last_week = dashboard.get("last_week", {})
    trends = dashboard.get("trends", {})

    # Sensitive topics (declining = good)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("Sensitive Topics")
        st.caption("*Relationships, health, money, etc.*")
    with col2:
        sensitive_trend = trends.get("sensitive_topics", {})
        trend_icon = sensitive_trend.get("icon", "→")
        trend_status = sensitive_trend.get("status", "stable")
        if trend_status == "improving":
            st.markdown(f"**{this_week.get('sensitive_topics', 0)}** {trend_icon}")
        elif trend_status == "concerning":
            st.markdown(f"**{this_week.get('sensitive_topics', 0)}** ⚠️ {trend_icon}")
        else:
            st.markdown(f"**{this_week.get('sensitive_topics', 0)}** {trend_icon}")
    with col3:
        st.caption(f"Last: {last_week.get('sensitive_topics', 0)}")

    # Connection seeking (declining = good)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("Connection Seeking")
        st.caption("*'Just wanted to talk' sessions*")
    with col2:
        conn_trend = trends.get("connection_seeking", {})
        trend_icon = conn_trend.get("icon", "→")
        trend_status = conn_trend.get("status", "stable")
        if trend_status == "improving":
            st.markdown(f"**{this_week.get('connection_seeking', 0)}** {trend_icon}")
        elif trend_status == "concerning":
            st.markdown(f"**{this_week.get('connection_seeking', 0)}** ⚠️ {trend_icon}")
        else:
            st.markdown(f"**{this_week.get('connection_seeking', 0)}** {trend_icon}")
    with col3:
        st.caption(f"Last: {last_week.get('connection_seeking', 0)}")

    # Human reach-outs (increasing = good)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("Human Reach-Outs")
        st.caption("*Logged human connections*")
    with col2:
        human_trend = trends.get("human_reach_outs", {})
        trend_icon = human_trend.get("icon", "→")
        trend_status = human_trend.get("status", "stable")
        if trend_status == "improving":
            st.markdown(f"**{this_week.get('human_reach_outs', 0)}** ✓ {trend_icon}")
        elif trend_status == "concerning":
            st.markdown(f"**{this_week.get('human_reach_outs', 0)}** {trend_icon}")
        else:
            st.markdown(f"**{this_week.get('human_reach_outs', 0)}** {trend_icon}")
    with col3:
        st.caption(f"Last: {last_week.get('human_reach_outs', 0)}")

    # Independence (increasing = good)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("Did It Myself")
        st.caption("*Tasks completed independently*")
    with col2:
        indep_trend = trends.get("did_it_myself", {})
        trend_icon = indep_trend.get("icon", "→")
        trend_status = indep_trend.get("status", "stable")
        if trend_status == "improving":
            st.markdown(f"**{this_week.get('did_it_myself', 0)}** ✓ {trend_icon}")
        else:
            st.markdown(f"**{this_week.get('did_it_myself', 0)}** {trend_icon}")
    with col3:
        st.caption(f"Last: {last_week.get('did_it_myself', 0)}")

    st.markdown("---")

    # Practical tasks note (neutral - no judgment)
    practical_count = this_week.get("practical_tasks", 0)
    if practical_count > 0:
        st.caption(f"Practical tasks this week: {practical_count}")
        st.caption("*(Email, code, explanations - just using a tool)*")

    st.markdown("---")

    # Anti-engagement score
    anti_engagement = dashboard.get("anti_engagement", {})
    score = anti_engagement.get("score", 0)
    level = anti_engagement.get("level", "moderate")
    label = anti_engagement.get("label", "Unknown")
    message = anti_engagement.get("message", "")
    trend = anti_engagement.get("trend", "stable")
    trend_message = anti_engagement.get("trend_message", "")

    st.markdown("**Reliance Score** (Sensitive Topics Only)")

    # Color-coded score display
    if level in ["excellent", "good"]:
        st.success(f"**{score}/10** - {label}")
    elif level == "moderate":
        st.warning(f"**{score}/10** - {label}")
    else:
        st.error(f"**{score}/10** - {label}")

    st.caption(message)

    # Trend badge
    if trend == "improving":
        st.info(f"📉 {trend_message}")
    elif trend == "increasing":
        st.warning(f"📈 {trend_message}")

    st.markdown("---")

    # Practical note
    st.caption(dashboard.get("practical_note", "Practical task usage is fine."))

    # Close button
    if st.button("Close", use_container_width=True, key="close_patterns"):
        st.session_state.show_my_patterns = False
        st.rerun()


def display_self_report_prompt():
    """
    Display a self-report prompt when conditions are met (Phase 7.2).

    Non-intrusive prompts to help users reflect on their usage.
    """
    tracker = st.session_state.wellness_tracker

    should_show, prompt_config = tracker.should_show_self_report()

    if not should_show or not prompt_config:
        return

    prompt_type = prompt_config.get("type", "")
    question = prompt_config.get("question", "")
    options = prompt_config.get("options", [])

    with st.expander("Quick check-in", expanded=True):
        st.markdown(f"**{question}**")

        for opt in options:
            if st.button(opt["label"], key=f"self_report_{opt['value']}", use_container_width=True):
                tracker.record_self_report(prompt_type, opt["value"])

                # Show appropriate follow-up
                if opt["value"] == "helpful":
                    st.success("Glad to hear that.")
                elif opt["value"] == "too_much":
                    st.info("Taking breaks is healthy. Consider reaching out to someone you trust.")
                elif opt["value"] == "skip":
                    st.caption("No problem.")

                st.rerun()


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
                if person.get("relationship"):
                    st.caption(person["relationship"])
            with col2:
                if st.button("Remove", key=f"remove_{person['id']}", type="secondary"):
                    network.remove_person(person["id"])
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
        contact = st.text_input(
            "How to reach them", placeholder="e.g., phone, usually free evenings"
        )

        domains = st.multiselect(
            "Good for talking about",
            ["relationships", "money", "health", "spirituality", "general"],
            default=["general"],
        )

        if st.form_submit_button("Add"):
            if name:
                network.add_person(name, relationship, contact, domains=domains)
                st.success(f"Added {name}")
                st.rerun()

    # Phase 12: Always show "Expand Your Network" option
    st.markdown("---")
    with st.expander("Expand Your Network", expanded=False):
        st.markdown("*Looking to find new people to connect with?*")

        # Get current domain if available for context-aware signposts
        guide = st.session_state.wellness_guide
        current_domain = None
        if guide.last_risk_assessment:
            current_domain = guide.last_risk_assessment.get("domain")

        content = network.get_building_network_content(current_domain)
        signposts = content.get("signposts", {})
        first_contact = content.get("first_contact", {})

        # Signposts section
        st.markdown("**Places to find connection:**")
        general = signposts.get("general_signposts", [])
        for signpost in general[:3]:  # Show top 3
            st.markdown(f"- **{signpost.get('category', '')}**")
            st.caption(f"  {signpost.get('search_hint', '')}")

        # Domain-specific signposts if available
        if "domain_signposts" in signposts:
            domain_content = signposts["domain_signposts"]
            st.markdown(f"\n*For {signposts.get('domain', 'your situation')}:*")
            for cat in domain_content.get("categories", [])[:2]:
                st.markdown(f"- {cat.get('category', '')}")

        # First-contact tip
        st.markdown("---")
        st.markdown("**Making first contact:**")
        principles = first_contact.get("principles", [])
        if principles:
            p = principles[0]  # Show just one principle
            st.markdown(f"*{p.get('title', '')}*: {p.get('content', '')}")

        # Encouragement
        encouragement = signposts.get("encouragement", "")
        if encouragement:
            st.info(encouragement)


def display_building_your_network(domain: str = None):
    """
    Display full "Building Your Network" panel (Phase 12).

    Primary use: When trusted network is empty, this replaces the simple "add someone" form.
    Also accessible via "Expand Your Network" expander in regular network setup.

    Shows:
    - Signposts: Types of places to find connection (tabbed view)
    - First-contact templates: How to initiate new connections
    - Add someone form: For when they already have someone in mind
    """
    network = st.session_state.trusted_network

    st.markdown("### Building Your Network")
    st.markdown("*Let's think about where you might find your people.*")

    # Get all content
    content = network.get_building_network_content(domain)
    signposts = content.get("signposts", {})
    first_contact = content.get("first_contact", {})

    # Tabs for different content types
    tab1, tab2, tab3 = st.tabs(["Where to Look", "Making First Contact", "Add Someone"])

    with tab1:
        st.markdown("**Places where people find connection:**")
        st.caption("No specific services—just types of places to search locally.")

        # Show general signposts
        general = signposts.get("general_signposts", [])
        for signpost in general:
            with st.expander(signpost.get("category", ""), expanded=False):
                st.markdown(signpost.get("description", ""))
                st.markdown(f"**Why it works:** {signpost.get('why_it_works', '')}")
                st.caption(signpost.get("search_hint", ""))

        # Show domain-specific signposts if available
        if "domain_signposts" in signposts:
            domain_content = signposts["domain_signposts"]
            st.markdown("---")
            st.markdown(f"**{domain_content.get('intro', '')}**")
            for cat in domain_content.get("categories", []):
                with st.expander(cat.get("category", ""), expanded=False):
                    st.markdown(cat.get("examples", ""))
                    st.caption(cat.get("search_hint", ""))

        # Reflection prompt
        st.markdown("---")
        reflection = signposts.get("reflection_prompt", "")
        if reflection:
            st.markdown(f"*Think about: {reflection}*")

        # Encouragement
        encouragement = signposts.get("encouragement", "")
        if encouragement:
            st.info(encouragement)

    with tab2:
        st.markdown("**Practical tips for initiating connection:**")

        situations = first_contact.get("situations", {})

        # Show each situation as an expander
        situation_titles = {
            "at_a_group_or_meetup": "Starting a conversation at a group",
            "turning_acquaintance_into_friend": "Moving from acquaintance to friend",
            "reconnecting_with_someone_from_the_past": "Reconnecting with someone",
            "joining_a_new_community": "Becoming part of a new community",
            "asking_for_help_or_support": "Asking someone for help",
        }

        for key, title in situation_titles.items():
            if key in situations:
                sit = situations[key]
                with st.expander(title, expanded=False):
                    st.markdown(sit.get("intro", ""))

                    # Show tips if available
                    tips = sit.get("before_tips", []) or sit.get("first_visits", [])
                    if tips:
                        st.markdown("**Tips:**")
                        for tip in tips:
                            st.markdown(f"- {tip}")

                    # Show conversation starters if available
                    starters = sit.get("conversation_starters", [])
                    if starters:
                        st.markdown("**Conversation starters:**")
                        for starter in starters:
                            st.markdown(f"- \"{starter.get('opener', '')}\"")
                            st.caption(f"  *{starter.get('why_it_works', '')}*")

                    # Show templates if available
                    templates = sit.get("templates", []) or sit.get(
                        "ways_to_suggest_hanging_out", []
                    )
                    if templates:
                        st.markdown("**Templates:**")
                        for template in templates:
                            if isinstance(template, dict):
                                st.markdown(f"- \"{template.get('template', '')}\"")
                                if template.get("context"):
                                    st.caption(f"  *{template.get('context', '')}*")
                            else:
                                st.markdown(f'- "{template}"')

        # General principles
        principles = first_contact.get("principles", [])
        if principles:
            st.markdown("---")
            st.markdown("**Remember:**")
            for p in principles[:3]:  # Show just 3
                st.markdown(f"- **{p.get('title', '')}**: {p.get('content', '')}")

        # Affirmation
        affirmation = first_contact.get("affirmation", "")
        if affirmation:
            st.info(affirmation)

    with tab3:
        st.markdown("**Already have someone in mind?**")
        st.caption("Add them here so empathySync can suggest reaching out when it matters.")

        # Reuse the existing add person form
        with st.form("add_person_building", clear_on_submit=True):
            name = st.text_input("Name", placeholder="e.g., Mom, Jake, Dr. Smith")
            relationship = st.text_input(
                "Relationship", placeholder="e.g., friend, sister, therapist"
            )
            contact = st.text_input(
                "How to reach them", placeholder="e.g., phone, usually free evenings"
            )

            domains = st.multiselect(
                "Good for talking about",
                ["relationships", "money", "health", "spirituality", "general"],
                default=["general"],
                key="building_domains",
            )

            if st.form_submit_button("Add"):
                if name:
                    network.add_person(name, relationship, contact, domains=domains)
                    st.success(f"Added {name}!")
                    st.balloons()
                    st.rerun()


def display_bring_someone_in(domain: str = "general"):
    """Enhanced context-aware human handoff panel (Phase 5)."""
    network = st.session_state.trusted_network
    tracker = st.session_state.wellness_tracker
    guide = st.session_state.wellness_guide
    people = network.get_all_people()

    st.markdown("### Bring Someone In")

    # Get session context for smart template selection
    emotional_weight = None
    session_intent = st.session_state.get("session_intent")
    dependency_score = 0

    if guide.last_risk_assessment:
        emotional_weight = guide.last_risk_assessment.get("emotional_weight")
        dependency_score = guide.last_risk_assessment.get("dependency_risk", 0)

    # Get context-aware handoff
    contextual = network.get_contextual_handoff(
        emotional_weight=emotional_weight,
        session_intent=session_intent,
        domain=domain,
        dependency_score=dependency_score,
        is_late_night=tracker.is_late_night_session(),
        sessions_today=tracker.get_wellness_summary().get("sessions_today", 0),
    )

    # Show context-aware intro prompt
    if contextual.get("intro_prompt"):
        st.info(contextual["intro_prompt"])

    # Suggest someone if we have people
    if people:
        suggested = network.suggest_person_for_domain(domain)
        if suggested:
            st.markdown(f"**Consider reaching out to:** {suggested['name']}")
            if suggested.get("relationship"):
                st.caption(suggested["relationship"])
    else:
        prompt = network.get_domain_prompt(domain)
        st.markdown(f"*{prompt}*")

    st.markdown("---")

    # Smart template selection based on context
    context_category = contextual.get("context", "general")

    # Map context to template options
    context_template_map = {
        "after_difficult_task": ["need_to_talk", "asking_for_help", "hard_conversation"],
        "processing_decision": ["need_to_talk", "asking_for_help", "checking_in"],
        "after_sensitive_topic": ["need_to_talk", "hard_conversation", "reconnecting"],
        "high_usage_pattern": ["checking_in", "reconnecting", "need_to_talk"],
        "general": [
            "need_to_talk",
            "reconnecting",
            "checking_in",
            "hard_conversation",
            "asking_for_help",
        ],
    }

    template_options = context_template_map.get(context_category, context_template_map["general"])

    st.markdown("**Need help starting the conversation?**")

    template_type = st.selectbox(
        "What kind of message?",
        template_options,
        format_func=lambda x: {
            "need_to_talk": "I need to talk",
            "reconnecting": "Reconnecting after silence",
            "checking_in": "Just checking in",
            "hard_conversation": "Starting a hard conversation",
            "asking_for_help": "Asking for help",
        }.get(x, x),
        label_visibility="collapsed",
    )

    # Get message template - prefer contextual if available, fallback to standard
    if contextual.get("message_template"):
        base_message = contextual["message_template"]
    else:
        template = network.get_reach_out_template(template_type)
        base_message = template["template"]

    # Build message with context from conversation
    if st.session_state.messages:
        user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        if user_msgs:
            context_snippet = user_msgs[-1][:100]
            full_message = f"{base_message}\n\nI've been thinking about: {context_snippet}..."
        else:
            full_message = base_message
    else:
        full_message = base_message

    message = st.text_area(
        "Message to send:", value=full_message, height=120, label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copy message", use_container_width=True):
            st.code(message)
            st.caption("Copy the text above")

    with col2:
        if st.button("I reached out!", use_container_width=True, type="primary"):
            # Log the reach out with context
            person_name = (
                suggested["name"] if people and "suggested" in dir() and suggested else "someone"
            )

            # Log in TrustedNetwork with handoff context
            network.log_handoff_initiated(
                context=context_category,
                domain=domain,
                person_name=person_name,
                message_sent=message,
            )

            # Also log in WellnessTracker for metrics
            tracker.log_handoff_event(
                event_type="initiated",
                context=context_category,
                domain=domain,
                details={"person_name": person_name},
            )

            # Show exit celebration
            celebration = network.get_exit_celebration(chose_human=True)
            st.success(celebration)
            st.balloons()


def display_handoff_follow_up(pending_handoff: Dict):
    """Display handoff follow-up prompt (Phase 5)."""
    network = st.session_state.trusted_network
    tracker = st.session_state.wellness_tracker
    loader = get_scenario_loader()

    st.markdown("---")
    st.markdown("### Quick check-in")

    context = pending_handoff.get("context", "general")
    follow_up_prompts = loader.get_handoff_follow_up_prompts(context)
    prompt = (
        random.choice(follow_up_prompts) if follow_up_prompts else "Did you reach out to someone?"
    )

    st.markdown(f"*{prompt}*")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Yes, I reached out", use_container_width=True, type="primary"):
            st.session_state.show_handoff_outcome = True
            st.session_state.pending_handoff_for_outcome = pending_handoff
            tracker.mark_handoff_follow_up_shown(pending_handoff.get("datetime"))
            st.rerun()

    with col2:
        if st.button("Not yet", use_container_width=True):
            tracker.log_handoff_event(event_type="follow_up", context=context, outcome="not_yet")
            tracker.mark_handoff_follow_up_shown(pending_handoff.get("datetime"))
            celebration = network.get_handoff_celebration("not_yet")
            st.info(celebration)
            st.session_state.show_handoff_follow_up = False
            st.rerun()

    with col3:
        if st.button("Skip", use_container_width=True):
            tracker.mark_handoff_follow_up_shown(pending_handoff.get("datetime"))
            st.session_state.show_handoff_follow_up = False
            st.rerun()


def display_handoff_outcome():
    """Display outcome selection for handoff follow-up (Phase 5)."""
    network = st.session_state.trusted_network
    tracker = st.session_state.wellness_tracker
    pending = st.session_state.get("pending_handoff_for_outcome", {})
    context = pending.get("context", "general")

    st.markdown("---")
    st.markdown("### How did it go?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Really helpful", use_container_width=True, type="primary"):
            tracker.log_handoff_event(
                event_type="reached_out", context=context, outcome="very_helpful"
            )
            tracker.log_handoff_event(
                event_type="outcome_reported", context=context, outcome="very_helpful"
            )
            celebration = network.get_handoff_celebration("very_helpful")
            st.success(celebration)
            st.balloons()
            st.session_state.show_handoff_outcome = False
            st.session_state.pending_handoff_for_outcome = None
            st.session_state.show_handoff_follow_up = False

    with col2:
        if st.button("Somewhat helpful", use_container_width=True):
            tracker.log_handoff_event(
                event_type="reached_out", context=context, outcome="somewhat_helpful"
            )
            tracker.log_handoff_event(
                event_type="outcome_reported", context=context, outcome="somewhat_helpful"
            )
            celebration = network.get_handoff_celebration("reached_out")
            st.success(celebration)
            st.session_state.show_handoff_outcome = False
            st.session_state.pending_handoff_for_outcome = None
            st.session_state.show_handoff_follow_up = False

    with col3:
        if st.button("Not very helpful", use_container_width=True):
            tracker.log_handoff_event(
                event_type="reached_out", context=context, outcome="not_helpful"
            )
            tracker.log_handoff_event(
                event_type="outcome_reported", context=context, outcome="not_helpful"
            )
            st.info("Not every conversation lands. The willingness to try is what counts.")
            st.session_state.show_handoff_outcome = False
            st.session_state.pending_handoff_for_outcome = None
            st.session_state.show_handoff_follow_up = False


def display_intent_check_in():
    """Display the 'What brings you here?' check-in at session start."""
    tracker = st.session_state.wellness_tracker
    network = st.session_state.trusted_network
    loader = get_scenario_loader()

    st.markdown("### What brings you here today?")

    # Get check-in config from scenarios
    check_in_config = loader.get_intent_check_in_config()
    options = check_in_config.get("options", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        practical = options.get("practical", {})
        if st.button(
            practical.get("label", "Get something done"),
            use_container_width=True,
            help=practical.get("description", "I have a specific task"),
        ):
            tracker.record_session_intent(INTENT_PRACTICAL, was_check_in=True)
            st.session_state.session_intent = INTENT_PRACTICAL
            st.session_state.show_intent_check_in = False
            st.rerun()

    with col2:
        processing = options.get("processing", {})
        if st.button(
            processing.get("label", "Think through something"),
            use_container_width=True,
            help=processing.get("description", "I need to work through something"),
        ):
            tracker.record_session_intent(INTENT_PROCESSING, was_check_in=True)
            st.session_state.session_intent = INTENT_PROCESSING
            st.session_state.show_intent_check_in = False
            st.rerun()

    with col3:
        connection = options.get("connection", {})
        if st.button(
            connection.get("label", "Just wanted to talk"),
            use_container_width=True,
            help=connection.get("description", "No specific goal"),
        ):
            # Connection-seeking - show gentle redirect
            tracker.record_session_intent(INTENT_CONNECTION, was_check_in=True)
            st.session_state.session_intent = INTENT_CONNECTION
            st.session_state.show_connection_redirect = True
            st.session_state.show_intent_check_in = False
            st.rerun()

    st.markdown("---")
    st.caption("This helps me calibrate how to help you.")

    # Skip option
    if st.button("Skip", type="secondary"):
        st.session_state.show_intent_check_in = False
        st.rerun()


def display_connection_redirect():
    """Display gentle redirect when user indicates they just want to talk."""
    tracker = st.session_state.wellness_tracker
    network = st.session_state.trusted_network
    loader = get_scenario_loader()

    st.markdown("---")

    # Get response from scenarios
    responses = loader.get_connection_responses("explicit")
    if responses:
        response = random.choice(responses)
    else:
        response = (
            "I'm here to help with tasks and thinking through things, but I'm not "
            "great at just chatting. Is there someone you could reach out to right now? "
            "Or if there's something specific on your mind, I'm happy to help you think through it."
        )

    st.info(response)

    # Show trusted people if available
    people = network.get_all_people()
    if people:
        st.markdown("**Your trusted people:**")
        for person in people[:3]:  # Show top 3
            st.markdown(f"- **{person['name']}** ({person.get('relationship', '')})")

        st.markdown("---")
        if st.button("I'll reach out to someone", type="primary", use_container_width=True):
            # Log this as a successful redirect
            tracker.log_policy_event(
                policy_type="connection_redirect",
                domain="connection_seeking",
                risk_weight=0,
                action_taken="User chose to reach out to human",
            )
            network.log_reach_out("someone", method="message", topic="general")
            st.balloons()
            st.success("That's the right call. Take care.")
            st.session_state.show_connection_redirect = False
            st.rerun()
    else:
        st.markdown("**Consider:** Who in your life could you reach out to right now?")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Actually, I have something specific", use_container_width=True):
            st.session_state.session_intent = INTENT_PRACTICAL
            st.session_state.show_connection_redirect = False
            st.rerun()
    with col2:
        if st.button("Set up trusted network", use_container_width=True):
            st.session_state.show_connection_redirect = False
            st.session_state.show_network_setup = True
            st.rerun()


def display_intent_shift_prompt(shift_info: dict):
    """Display prompt when intent shift is detected mid-session."""
    st.markdown("---")
    st.info(
        "It sounds like this became about more than just the task. "
        "Want to pause and talk about what's coming up? "
        "Or would you prefer I just help with the original task?"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Let's talk about what's coming up", use_container_width=True):
            st.session_state.session_intent = shift_info.get("to_intent", INTENT_EMOTIONAL)
            st.session_state.pending_shift = None
            st.rerun()
    with col2:
        if st.button("Just help with the task", use_container_width=True):
            st.session_state.acknowledged_shift = True
            st.session_state.pending_shift = None
            st.rerun()


def display_graduation_prompt(category: str, prompt_text: str):
    """Display a graduation prompt suggesting skill-building."""
    tracker = st.session_state.wellness_tracker
    loader = get_scenario_loader()

    st.markdown("---")
    st.info(prompt_text)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Show me some tips", use_container_width=True, type="primary"):
            st.session_state.show_skill_tips = category
            tracker.record_graduation_accepted(category)
            st.rerun()
    with col2:
        if st.button("Just help me", use_container_width=True):
            tracker.record_graduation_dismissal(category)
            st.session_state.graduation_shown_this_session = True
            st.rerun()


def display_skill_tips(category: str):
    """Display skill tips for a task category."""
    loader = get_scenario_loader()
    tips = loader.get_skill_tips(category)

    if not tips:
        return

    st.markdown("---")
    st.markdown("### Quick tips for doing this yourself")

    for tip in tips:
        with st.expander(tip.get("title", "Tip"), expanded=True):
            st.markdown(tip.get("content", ""))

    st.markdown("---")
    if st.button("Got it, thanks!", use_container_width=True):
        st.session_state.show_skill_tips = None
        st.rerun()


def display_independence_button():
    """Display the 'I did it myself!' button in sidebar."""
    tracker = st.session_state.wellness_tracker
    loader = get_scenario_loader()

    # Get button labels
    labels = loader.get_independence_button_labels()
    label = labels[0] if labels else "I did it myself!"

    if st.button(label, use_container_width=True, help="Did you complete a task on your own?"):
        st.session_state.show_independence_form = True
        st.rerun()


def display_independence_form():
    """Display form for recording independence."""
    tracker = st.session_state.wellness_tracker
    loader = get_scenario_loader()

    st.markdown("### Nice work!")
    st.markdown("What did you do on your own?")

    categories = loader.get_graduation_categories()
    category_options = ["general"] + list(categories.keys())
    category_labels = {
        "general": "Something else",
        "email_drafting": "Wrote an email",
        "code_help": "Solved a coding problem",
        "explanations": "Figured something out",
        "writing_general": "Wrote something",
        "summarizing": "Summarized content",
    }

    category = st.selectbox(
        "Category",
        category_options,
        format_func=lambda x: category_labels.get(x, x.replace("_", " ").title()),
        label_visibility="collapsed",
    )

    notes = st.text_input("Notes (optional)", placeholder="e.g., 'Wrote the meeting recap myself'")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Record it!", use_container_width=True, type="primary"):
            tracker.record_independence(category, notes)

            # Show celebration
            celebrations = loader.get_independence_celebrations()
            if celebrations:
                celebration = random.choice(celebrations)
                st.success(celebration)

            # Check for milestone
            stats = tracker.get_independence_stats()
            if stats.get("is_milestone"):
                st.balloons()
                count = stats.get("total_recent", 0)
                st.info(
                    f"You've done {count} things on your own recently. Your skills are growing."
                )

            st.session_state.show_independence_form = False
            st.rerun()

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_independence_form = False
            st.rerun()


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
        "it doesn't truly know you. It's a tool for thinking, not a companion or advisor."
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
    classifier = RiskClassifier()

    # Check for cooldown
    should_cooldown, cooldown_reason = tracker.should_enforce_cooldown()
    if should_cooldown:
        st.warning(cooldown_reason)

        # Suggest reaching out to someone
        people = network.get_all_people()
        if people:
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
                st.markdown(
                    f"**You said {person['name']} is good for {domain} topics.** Consider reaching out to them."
                )

    # Phase 6: Show transparency panel if we have assessment data
    if guide.last_risk_assessment and st.session_state.messages:
        display_transparency_panel()

    # Phase 4: Show intent shift prompt if detected
    if st.session_state.get("pending_shift") and not st.session_state.get("acknowledged_shift"):
        display_intent_shift_prompt(st.session_state.pending_shift)

    # Phase 3: Show skill tips if requested
    if st.session_state.get("show_skill_tips"):
        display_skill_tips(st.session_state.show_skill_tips)

    # Phase 3: Show graduation prompt if pending
    if st.session_state.get("pending_graduation") and not st.session_state.get("show_skill_tips"):
        grad = st.session_state.pending_graduation
        display_graduation_prompt(grad["category"], grad["prompt"])
        st.session_state.pending_graduation = None
        st.session_state.graduation_shown_this_session = True

    # Chat input (disabled in read-only mode)
    if is_read_only():
        st.chat_input("Read-only mode: close empathySync on other device first", disabled=True)
    elif prompt := st.chat_input("What are you thinking through?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Phase 4: Check for connection-seeking in first message
        if len(st.session_state.messages) == 1:
            is_connection, connection_type = classifier.is_connection_seeking(prompt)
            if is_connection:
                tracker.record_session_intent(INTENT_CONNECTION, auto_detected=True)
                st.session_state.session_intent = INTENT_CONNECTION

                # Handle AI relationship questions specially
                loader = get_scenario_loader()
                if connection_type == "ai_relationship":
                    responses = loader.get_connection_responses("ai_relationship")
                else:
                    responses = loader.get_connection_responses(connection_type)

                if responses:
                    response = random.choice(responses)
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                    return
            else:
                # Auto-detect intent from first message
                detected_intent, confidence = classifier.detect_intent(prompt)
                if confidence >= 0.6:
                    tracker.record_session_intent(detected_intent, auto_detected=True)
                    st.session_state.session_intent = detected_intent

        # Phase 4: Check for intent shift (after first turn)
        initial_intent = st.session_state.get("session_intent")
        if (
            initial_intent
            and len(st.session_state.messages) > 2
            and not st.session_state.get("acknowledged_shift")
        ):
            shift = classifier.detect_intent_shift(
                st.session_state.messages, initial_intent, prompt
            )
            if shift and shift.get("is_concerning"):
                st.session_state.pending_shift = shift
                # Don't block, just note - will show prompt on next render

        with st.chat_message("assistant"):
            with st.spinner(""):
                response = guide.generate_response(
                    prompt, wellness_mode, st.session_state.messages, wellness_tracker=tracker
                )
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        # Phase 3: Track task category for practical tasks
        if guide.last_risk_assessment:
            domain = guide.last_risk_assessment.get("domain", "")
            if domain == "logistics":
                # Detect and track task category
                task_category, confidence = classifier.detect_task_category(prompt)
                if task_category and confidence >= 0.6:
                    stats = tracker.record_task_category(task_category)
                    st.session_state.last_task_category = task_category

                    # Check if we should show graduation prompt
                    if not st.session_state.get("graduation_shown_this_session"):
                        loader = get_scenario_loader()
                        category_config = loader.get_graduation_category(task_category)
                        if category_config:
                            threshold = category_config.get("threshold", 10)
                            settings = loader.get_graduation_settings()
                            max_dismissals = settings.get("max_dismissals", 3)

                            should_show, reason = tracker.should_show_graduation_prompt(
                                task_category, threshold, max_dismissals
                            )
                            if should_show:
                                prompts = loader.get_graduation_prompts(task_category)
                                if prompts:
                                    st.session_state.pending_graduation = {
                                        "category": task_category,
                                        "prompt": random.choice(prompts),
                                    }
                                    tracker.record_graduation_shown(task_category)

        if guide.last_policy_action or st.session_state.get("pending_shift"):
            st.rerun()


def save_session_on_end():
    """Save session data when ending conversation."""
    guide = st.session_state.wellness_guide
    tracker = st.session_state.wellness_tracker

    if hasattr(st.session_state, "session_start"):
        duration = (datetime.now() - st.session_state.session_start).total_seconds() / 60
        session_summary = guide.get_session_summary()

        tracker.add_session(
            duration_minutes=int(duration),
            turn_count=session_summary["turn_count"],
            domains_touched=session_summary["domains_touched"],
            max_risk_weight=session_summary["max_risk_weight"],
        )


def display_lock_warning():
    """
    Check device lock status and configure read-only mode if needed (Phase 11).

    Instead of blocking the entire app when another device has the lock,
    we allow read-only viewing but disable write operations. This provides
    a better UX while maintaining data safety.

    Returns:
        True if locked by another device (app in read-only mode)
        False if we have the lock or lock checking is disabled
    """
    from utils.write_gate import set_read_only

    if not settings.ENABLE_DEVICE_LOCK:
        st.session_state.read_only_mode = False
        set_read_only(False)
        return False

    # Only check lock status once per session
    if "lock_status_checked" in st.session_state:
        return st.session_state.get("read_only_mode", False)

    try:
        from utils.lockfile import check_lock_status, acquire_lock

        status = check_lock_status()
        st.session_state.lock_status_checked = True

        if status["locked_by_other"]:
            st.session_state.read_only_mode = True
            st.session_state.lock_status = status
            set_read_only(True)  # Enable write gate
            return True
        else:
            # Try to acquire lock
            if not status["locked_by_us"]:
                acquire_lock()
            st.session_state.read_only_mode = False
            set_read_only(False)  # Disable write gate
            return False

    except Exception as e:
        # If lock check fails, log and continue (don't block the app)
        import logging

        logging.warning(f"Lock file check failed: {e}")
        st.session_state.lock_status_checked = True
        st.session_state.read_only_mode = False
        set_read_only(False)
        return False


def display_lock_banner():
    """Display a persistent banner when in read-only mode due to device lock."""
    if not st.session_state.get("read_only_mode"):
        return

    status = st.session_state.get("lock_status", {})
    hostname = status.get("hostname", "another device")
    started = status.get("started_at", "unknown time")

    # Parse started time for friendly display
    try:
        started_dt = datetime.fromisoformat(started)
        started = started_dt.strftime("%I:%M %p on %b %d")
    except (ValueError, TypeError):
        pass

    col1, col2, col3 = st.columns([5, 2, 1])
    with col1:
        st.warning(
            f"**Read-only mode**: empathySync is open on {hostname} (since {started}). "
            f"Writes are blocked to prevent sync conflicts. Close it there first."
        )
    with col2:
        if st.button(
            "Take Over",
            type="primary",
            help="Force access - use only if the other device is unavailable",
        ):
            handle_lock_takeover()
    with col3:
        if st.button("Dismiss"):
            st.session_state.lock_banner_dismissed = True
            st.rerun()


def handle_lock_takeover():
    """Handle user clicking 'Take Over' to force lock acquisition."""
    try:
        from utils.lockfile import acquire_lock
        from utils.write_gate import set_read_only

        if acquire_lock(force=True):
            st.session_state.read_only_mode = False
            st.session_state.lock_status = None
            set_read_only(False)  # Re-enable writes
            st.success("Lock acquired. You now have full access.")
            st.rerun()
    except Exception as e:
        st.error(f"Failed to take over lock: {e}")


def is_read_only():
    """Check if the app is in read-only mode due to device lock."""
    return st.session_state.get("read_only_mode", False)


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

    # Phase 13: Startup health checks (run once per session)
    if "health_checks_passed" not in st.session_state:
        checks = run_health_checks()
        if has_critical_failures(checks):
            st.error("**Startup Check Failed**")
            for check in checks:
                if check.ok:
                    st.success(f"**{check.name}**: {check.message}")
                elif check.critical:
                    st.error(f"**{check.name}**: {check.message}")
                    if check.details:
                        st.markdown(check.details)
                else:
                    st.warning(f"**{check.name}**: {check.message}")
                    if check.details:
                        st.markdown(check.details)
            st.markdown("---")
            st.markdown("Fix the issues above and refresh the page.")
            return
        st.session_state.health_checks_passed = True

    # Phase 11: Check device lock status (enables read-only mode if locked by other)
    display_lock_warning()

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
    # Phase 4: Session intent tracking
    if "session_intent" not in st.session_state:
        st.session_state.session_intent = None
    if "show_intent_check_in" not in st.session_state:
        # Check if we should show the check-in based on usage patterns
        tracker = st.session_state.wellness_tracker
        st.session_state.show_intent_check_in = tracker.should_show_intent_check_in()
    if "show_connection_redirect" not in st.session_state:
        st.session_state.show_connection_redirect = False
    if "pending_shift" not in st.session_state:
        st.session_state.pending_shift = None
    # Phase 3: Graduation tracking
    if "pending_graduation" not in st.session_state:
        st.session_state.pending_graduation = None
    if "graduation_shown_this_session" not in st.session_state:
        st.session_state.graduation_shown_this_session = False
    if "show_skill_tips" not in st.session_state:
        st.session_state.show_skill_tips = None
    if "last_task_category" not in st.session_state:
        st.session_state.last_task_category = None
    if "show_independence_form" not in st.session_state:
        st.session_state.show_independence_form = False
    if "acknowledged_shift" not in st.session_state:
        st.session_state.acknowledged_shift = False
    # Phase 5: Handoff tracking
    if "show_handoff_follow_up" not in st.session_state:
        st.session_state.show_handoff_follow_up = False
    if "show_handoff_outcome" not in st.session_state:
        st.session_state.show_handoff_outcome = False
    if "pending_handoff_for_outcome" not in st.session_state:
        st.session_state.pending_handoff_for_outcome = None
    if "pending_handoff_info" not in st.session_state:
        st.session_state.pending_handoff_info = None
    # Phase 6: Transparency tracking
    if "show_session_summary" not in st.session_state:
        st.session_state.show_session_summary = False
    # Phase 7: Success metrics
    if "show_my_patterns" not in st.session_state:
        st.session_state.show_my_patterns = False

    # Header
    st.markdown("# empathySync")
    st.markdown('<p class="subtitle">Help that knows when to stop</p>', unsafe_allow_html=True)

    # Phase 11: Show lock banner if in read-only mode
    if is_read_only() and not st.session_state.get("lock_banner_dismissed"):
        display_lock_banner()

    # Phase 4: Show connection redirect if user indicated they just want to talk
    if st.session_state.get("show_connection_redirect"):
        display_connection_redirect()
        return

    # Phase 4: Show intent check-in if appropriate (before the chat starts)
    if st.session_state.get("show_intent_check_in") and not st.session_state.messages:
        display_intent_check_in()
        # Still show the rest of the UI below, just with the check-in modal

    # Phase 5: Check for pending handoff follow-ups
    if not st.session_state.get("show_handoff_follow_up") and not st.session_state.get(
        "show_handoff_outcome"
    ):
        tracker = st.session_state.wellness_tracker
        should_show, pending = tracker.should_show_handoff_follow_up()
        if should_show and pending:
            st.session_state.show_handoff_follow_up = True
            st.session_state.pending_handoff_info = pending

    # Phase 5: Show handoff follow-up if pending
    if st.session_state.get("show_handoff_outcome"):
        display_handoff_outcome()
    elif st.session_state.get("show_handoff_follow_up") and st.session_state.get(
        "pending_handoff_info"
    ):
        display_handoff_follow_up(st.session_state.pending_handoff_info)

    # Phase 6: Show session summary if requested
    if st.session_state.get("show_session_summary"):
        display_session_summary()

    # Check if network is empty - show Building Your Network (Phase 12)
    network = st.session_state.trusted_network
    if not network.get_all_people() and not st.session_state.show_network_setup:
        # Get current domain if available for context-aware signposts
        current_domain = None
        if st.session_state.messages:
            guide = st.session_state.wellness_guide
            if hasattr(guide, "_session_state") and guide._session_state.get("domains"):
                # Get most recent domain
                current_domain = (
                    guide._session_state["domains"][-1] if guide._session_state["domains"] else None
                )

        st.info(
            "**No trusted network yet.** Instead of 'talk to someone', let's think about where you might find your people."
        )

        # Show Building Your Network panel
        display_building_your_network(domain=current_domain)

        st.markdown("---")

    # Sidebar
    with st.sidebar:
        # Default communication mode - system auto-adjusts based on domain
        wellness_mode = "Balanced"

        # Read-only mode indicator (Phase 11)
        if is_read_only():
            st.error("**Writes blocked** - another device has the lock")

        # Usage stats (no header needed - self-explanatory)
        display_usage_health()

        st.markdown("---")

        # === QUICK ACTIONS SECTION ===
        st.markdown('<p class="sidebar-header">Quick Actions</p>', unsafe_allow_html=True)

        # Primary actions in a row - toggle behavior (click again to close)
        reality_active = st.session_state.get("show_reality_check", False)
        network_active = st.session_state.get("show_network_setup", False)
        patterns_active = st.session_state.get("show_my_patterns", False)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "Reality Check",
                use_container_width=True,
                type="primary" if reality_active else "secondary",
                help="Am I relying on this too much?",
            ):
                if reality_active:
                    st.session_state.show_reality_check = False
                else:
                    st.session_state.show_reality_check = True
                    st.session_state.show_network_setup = False
                    st.session_state.show_my_patterns = False
                st.rerun()
        with col2:
            if st.button(
                "My People",
                use_container_width=True,
                type="primary" if network_active else "secondary",
                help="Manage trusted network",
            ):
                if network_active:
                    st.session_state.show_network_setup = False
                else:
                    st.session_state.show_network_setup = True
                    st.session_state.show_reality_check = False
                    st.session_state.show_my_patterns = False
                st.rerun()

        # Full-width secondary action - toggle behavior
        if st.button(
            "My Patterns",
            use_container_width=True,
            type="primary" if patterns_active else "secondary",
            help="Track your usage trends (sensitive vs practical)",
        ):
            if patterns_active:
                st.session_state.show_my_patterns = False
            else:
                st.session_state.show_my_patterns = True
                st.session_state.show_reality_check = False
                st.session_state.show_network_setup = False
            st.rerun()

        # Show appropriate panel
        if st.session_state.get("show_my_patterns"):
            st.markdown("---")
            display_my_patterns_dashboard()
        elif st.session_state.get("show_reality_check"):
            display_reality_check()
        elif st.session_state.get("show_network_setup"):
            st.markdown("---")
            # Phase 12: Show Building Your Network if empty, otherwise regular setup
            network = st.session_state.trusted_network
            if network.is_network_empty():
                # Get current domain for context-aware signposts
                guide = st.session_state.wellness_guide
                current_domain = None
                if guide.last_risk_assessment:
                    current_domain = guide.last_risk_assessment.get("domain")
                display_building_your_network(domain=current_domain)
            else:
                display_trusted_network_setup()
            if st.button("Done", use_container_width=True):
                st.session_state.show_network_setup = False
                st.rerun()
        else:
            st.markdown("---")

            # === HUMAN CONNECTION ===
            st.markdown('<p class="sidebar-header">Human Connection</p>', unsafe_allow_html=True)

            # Get current domain if available
            guide = st.session_state.wellness_guide
            current_domain = "general"
            if guide.last_risk_assessment:
                current_domain = guide.last_risk_assessment.get("domain", "general")

            # Bring someone in
            with st.expander("Reach Out to Someone", expanded=False):
                display_bring_someone_in(current_domain)

            # Phase 3: Independence button and form
            if st.session_state.get("show_independence_form"):
                display_independence_form()
            else:
                display_independence_button()

            st.markdown("---")

            # === SESSION CONTROLS ===
            st.markdown('<p class="sidebar-header">Session</p>', unsafe_allow_html=True)

            # New Chat - primary action
            if st.button("New Chat", use_container_width=True, type="primary"):
                save_session_on_end()
                st.session_state.messages = []
                st.session_state.session_start = datetime.now()
                st.session_state.show_reality_check = False
                st.session_state.wellness_guide.reset_session()
                # Phase 4: Reset intent state
                st.session_state.session_intent = None
                st.session_state.pending_shift = None
                st.session_state.acknowledged_shift = False
                tracker = st.session_state.wellness_tracker
                st.session_state.show_intent_check_in = tracker.should_show_intent_check_in()
                st.session_state.show_connection_redirect = False
                # Phase 3: Reset graduation state
                st.session_state.pending_graduation = None
                st.session_state.graduation_shown_this_session = False
                st.session_state.show_skill_tips = None
                st.session_state.last_task_category = None
                st.session_state.show_independence_form = False
                # Phase 5: Reset handoff state
                st.session_state.show_handoff_follow_up = False
                st.session_state.show_handoff_outcome = False
                st.session_state.pending_handoff_for_outcome = None
                st.session_state.pending_handoff_info = None
                # Phase 6: Reset transparency state
                st.session_state.show_session_summary = False
                # Phase 7: Reset metrics state
                st.session_state.show_my_patterns = False
                st.rerun()

            # Export - direct download button (simplified from nested approach)
            tracker = st.session_state.wellness_tracker
            data = tracker._load_data()
            st.download_button(
                "Export Data",
                data=json.dumps(data, indent=2),
                file_name=f"empathysync_{date.today()}.json",
                mime="application/json",
                use_container_width=True,
            )

            st.markdown("---")

            # === DATA SECTION ===
            with st.expander("Data & Privacy", expanded=False):
                st.caption("All data is stored locally on your device.")

                # Initialize reset confirmation state
                if "confirm_reset" not in st.session_state:
                    st.session_state.confirm_reset = False

                if st.session_state.confirm_reset:
                    st.warning(
                        "This will delete all your usage history, check-ins, and patterns. This cannot be undone."
                    )
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, reset", use_container_width=True, type="primary"):
                            tracker = st.session_state.wellness_tracker
                            tracker.reset_all_data()
                            st.session_state.confirm_reset = False
                            st.success("Data cleared.")
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.confirm_reset = False
                            st.rerun()
                else:
                    if st.button(
                        "Reset All Data",
                        use_container_width=True,
                        help="Clear all usage history and patterns",
                    ):
                        st.session_state.confirm_reset = True
                        st.rerun()

            # Phase 6: Session summary button (show only if there's been conversation)
            if guide.session_turn_count > 0:
                st.markdown("---")
                if st.button(
                    "View Session Summary",
                    use_container_width=True,
                    help="See a summary of this conversation",
                ):
                    st.session_state.show_session_summary = True
                    st.rerun()

            st.markdown("---")
            st.caption("Local-first. Your data stays on your device.")

    # Main chat interface
    display_chat_interface(wellness_mode)


if __name__ == "__main__":
    main()
