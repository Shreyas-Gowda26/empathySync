"""
Wellness tracking for empathySync users
Local storage of wellness check-ins, usage patterns, and dependency monitoring
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config.settings import settings


# Session intent types
INTENT_PRACTICAL = "practical"
INTENT_PROCESSING = "processing"
INTENT_CONNECTION = "connection"
INTENT_UNKNOWN = "unknown"


class WellnessTracker:
    """
    Track user wellness patterns locally.

    Monitors session frequency, duration, and patterns to detect
    dependency and enforce healthy usage boundaries.
    """

    def __init__(self):
        self.data_file = settings.DATA_DIR / "wellness_data.json"
        self.ensure_data_file()

    def ensure_data_file(self):
        """Ensure wellness data file exists"""
        if not self.data_file.exists():
            self._save_data({
                "check_ins": [],
                "usage_sessions": [],
                "policy_events": [],  # Track when safety policies fire
                "created_at": datetime.now().isoformat()
            })

    # ==================== CHECK-INS ====================

    def add_check_in(self, feeling_score: int, notes: str = ""):
        """Add a wellness check-in (1-5 scale)"""
        data = self._load_data()

        check_in = {
            "date": date.today().isoformat(),
            "datetime": datetime.now().isoformat(),
            "feeling_score": feeling_score,
            "notes": notes
        }

        data["check_ins"].append(check_in)
        self._save_data(data)

        return check_in

    def get_recent_check_ins(self, days: int = 7) -> List[Dict]:
        """Get check-ins from last N days"""
        data = self._load_data()
        recent = data["check_ins"][-days:] if data["check_ins"] else []
        return recent

    def get_today_check_in(self) -> Optional[Dict]:
        """Check if user has checked in today"""
        today_str = date.today().isoformat()
        data = self._load_data()

        for check_in in reversed(data["check_ins"]):
            if check_in["date"] == today_str:
                return check_in

        return None

    # ==================== SESSION TRACKING ====================

    def add_session(self, duration_minutes: int, turn_count: int = 0,
                    domains_touched: List[str] = None, max_risk_weight: float = 0):
        """
        Track a usage session with rich metadata.

        Args:
            duration_minutes: How long the session lasted
            turn_count: Number of conversation turns
            domains_touched: List of risk domains encountered
            max_risk_weight: Highest risk weight seen in session
        """
        data = self._load_data()

        session = {
            "date": date.today().isoformat(),
            "datetime": datetime.now().isoformat(),
            "hour": datetime.now().hour,
            "duration_minutes": duration_minutes,
            "turn_count": turn_count,
            "domains_touched": domains_touched or [],
            "max_risk_weight": max_risk_weight
        }

        data["usage_sessions"].append(session)
        self._save_data(data)

        return session

    def get_sessions_today(self) -> List[Dict]:
        """Get all sessions from today"""
        today_str = date.today().isoformat()
        data = self._load_data()

        return [s for s in data.get("usage_sessions", []) if s.get("date") == today_str]

    def get_sessions_this_week(self) -> List[Dict]:
        """Get all sessions from the past 7 days"""
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        data = self._load_data()

        return [s for s in data.get("usage_sessions", []) if s.get("date", "") >= week_ago]

    def count_sessions_today(self) -> int:
        """Count number of sessions today"""
        return len(self.get_sessions_today())

    def count_sessions_this_week(self) -> int:
        """Count number of sessions this week"""
        return len(self.get_sessions_this_week())

    def get_total_minutes_today(self) -> int:
        """Get total minutes spent in sessions today"""
        sessions = self.get_sessions_today()
        return sum(s.get("duration_minutes", 0) for s in sessions)

    def is_late_night_session(self) -> bool:
        """Check if current time is late night (10pm - 6am)"""
        hour = datetime.now().hour
        return hour >= 22 or hour < 6

    def get_late_night_sessions_this_week(self) -> int:
        """Count late night sessions in the past week"""
        sessions = self.get_sessions_this_week()
        return sum(1 for s in sessions if s.get("hour", 12) >= 22 or s.get("hour", 12) < 6)

    # ==================== DEPENDENCY DETECTION ====================

    def calculate_dependency_signals(self) -> Dict:
        """
        Calculate dependency warning signals based on usage patterns.

        Returns dict with:
        - sessions_today: count
        - sessions_this_week: count
        - late_night_sessions: count this week
        - minutes_today: total
        - is_escalating: bool (usage increasing over time)
        - dependency_score: 0-10 composite score
        - warnings: list of human-readable warnings
        """
        sessions_today = self.count_sessions_today()
        sessions_week = self.count_sessions_this_week()
        late_night = self.get_late_night_sessions_this_week()
        minutes_today = self.get_total_minutes_today()

        # Check if usage is escalating (compare this week to prior)
        two_weeks_ago = (date.today() - timedelta(days=14)).isoformat()
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        data = self._load_data()

        prior_week = [s for s in data.get("usage_sessions", [])
                      if two_weeks_ago <= s.get("date", "") < week_ago]
        is_escalating = sessions_week > len(prior_week) * 1.5 if prior_week else False

        # Calculate composite dependency score (0-10)
        score = 0.0
        warnings = []

        # Sessions today factor
        if sessions_today >= 7:
            score += 4.0
            warnings.append(f"You've started {sessions_today} sessions today")
        elif sessions_today >= 5:
            score += 2.5
            warnings.append(f"You've had {sessions_today} sessions today")
        elif sessions_today >= 3:
            score += 1.5

        # Minutes today factor
        if minutes_today >= 120:
            score += 2.0
            warnings.append(f"You've spent {minutes_today} minutes with me today")
        elif minutes_today >= 60:
            score += 1.0

        # Late night factor
        if late_night >= 3:
            score += 2.0
            warnings.append(f"You've had {late_night} late-night sessions this week")
        elif late_night >= 1:
            score += 1.0

        # Escalation factor
        if is_escalating:
            score += 1.5
            warnings.append("Your usage is increasing compared to last week")

        # Current late night bonus
        if self.is_late_night_session():
            score += 0.5

        return {
            "sessions_today": sessions_today,
            "sessions_this_week": sessions_week,
            "late_night_sessions": late_night,
            "minutes_today": minutes_today,
            "is_escalating": is_escalating,
            "dependency_score": min(score, 10.0),
            "warnings": warnings
        }

    def should_enforce_cooldown(self) -> tuple[bool, str]:
        """
        Check if a cooldown should be enforced.

        Returns (should_cooldown, reason)
        """
        signals = self.calculate_dependency_signals()

        if signals["sessions_today"] >= 7:
            return True, "You've had many sessions today. Please take a break and talk to someone you trust."

        if signals["minutes_today"] >= 120:
            return True, "You've spent a lot of time here today. Step away for a while."

        if signals["dependency_score"] >= 8:
            return True, "Your usage pattern suggests you might be relying on me too much. Take a break."

        return False, ""

    # ==================== POLICY EVENT LOGGING ====================

    def log_policy_event(self, policy_type: str, domain: str,
                         risk_weight: float, action_taken: str):
        """
        Log when a safety policy fires (for transparency/audit).

        Args:
            policy_type: e.g., "domain_redirect", "crisis_stop", "dependency_intervention"
            domain: The detected domain
            risk_weight: The calculated risk weight
            action_taken: What the system did
        """
        data = self._load_data()

        if "policy_events" not in data:
            data["policy_events"] = []

        event = {
            "datetime": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "policy_type": policy_type,
            "domain": domain,
            "risk_weight": risk_weight,
            "action_taken": action_taken
        }

        data["policy_events"].append(event)
        self._save_data(data)

        return event

    def get_recent_policy_events(self, limit: int = 10) -> List[Dict]:
        """Get recent policy events for transparency"""
        data = self._load_data()
        events = data.get("policy_events", [])
        return events[-limit:] if events else []

    # ==================== WELLNESS SUMMARY ====================

    def get_wellness_summary(self) -> Dict:
        """Get comprehensive summary of wellness patterns"""
        data = self._load_data()

        # Session stats
        sessions_today = self.count_sessions_today()
        sessions_week = self.count_sessions_this_week()
        minutes_today = self.get_total_minutes_today()

        # Check-in stats
        total_checkins = len(data.get("check_ins", []))

        if data.get("check_ins"):
            scores = [c["feeling_score"] for c in data["check_ins"]]
            avg_score = sum(scores) / len(scores)
            latest_checkin = data["check_ins"][-1]["date"]
        else:
            avg_score = 0
            latest_checkin = None

        # Dependency signals
        dependency = self.calculate_dependency_signals()

        return {
            "sessions_today": sessions_today,
            "sessions_this_week": sessions_week,
            "minutes_today": minutes_today,
            "total_sessions": len(data.get("usage_sessions", [])),
            "total_checkins": total_checkins,
            "average_feeling": round(avg_score, 1) if avg_score else None,
            "latest_checkin": latest_checkin,
            "dependency_score": dependency["dependency_score"],
            "dependency_warnings": dependency["warnings"],
            "should_take_break": dependency["dependency_score"] >= 5
        }

    # ==================== DATA MANAGEMENT ====================

    def _load_data(self) -> Dict:
        """Load wellness data from file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {"check_ins": [], "usage_sessions": [], "policy_events": []}

    def _save_data(self, data: Dict):
        """Save wellness data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def clear_data(self):
        """Clear all wellness data (user-initiated)"""
        self._save_data({
            "check_ins": [],
            "usage_sessions": [],
            "policy_events": [],
            "session_intents": [],
            "created_at": datetime.now().isoformat()
        })

    # ==================== SESSION INTENT CHECK-IN ====================

    def should_show_intent_check_in(self, first_message: str = "") -> bool:
        """
        Determine if we should show the "What brings you here?" check-in.

        Rules:
        - Don't show if first message is clearly practical (starts with imperative)
        - Show after min_sessions_between sessions without check-in
        - Always show if max_days_between days since last check-in
        """
        data = self._load_data()
        intents = data.get("session_intents", [])

        # Config defaults (could load from scenarios/intents/session_intents.yaml)
        min_sessions_between = 3
        max_days_between = 7

        # Skip if first message is clearly practical
        if first_message:
            practical_starters = [
                "write me", "write a", "help me write", "draft a", "draft me",
                "create a", "make me", "code for", "write code", "explain how",
                "show me how", "give me a", "template for", "list of"
            ]
            msg_lower = first_message.lower()
            if any(msg_lower.startswith(starter) for starter in practical_starters):
                return False

        if not intents:
            # First session ever - don't interrupt, let them discover naturally
            return False

        # Count sessions since last check-in
        sessions_since_checkin = 0
        last_checkin_date = None

        for intent_record in reversed(intents):
            if intent_record.get("was_check_in"):
                last_checkin_date = intent_record.get("date")
                break
            sessions_since_checkin += 1

        # Check if enough sessions have passed
        if sessions_since_checkin >= min_sessions_between:
            return True

        # Check if enough days have passed
        if last_checkin_date:
            try:
                last_date = datetime.fromisoformat(last_checkin_date).date()
                days_since = (date.today() - last_date).days
                if days_since >= max_days_between:
                    return True
            except (ValueError, TypeError):
                pass

        return False

    def record_session_intent(
        self,
        intent: str,
        was_check_in: bool = False,
        auto_detected: bool = False
    ) -> Dict:
        """
        Record the intent for this session.

        Args:
            intent: One of INTENT_PRACTICAL, INTENT_PROCESSING, INTENT_CONNECTION
            was_check_in: Whether this came from explicit user selection
            auto_detected: Whether this was auto-detected from message content
        """
        data = self._load_data()

        if "session_intents" not in data:
            data["session_intents"] = []

        record = {
            "date": date.today().isoformat(),
            "datetime": datetime.now().isoformat(),
            "intent": intent,
            "was_check_in": was_check_in,
            "auto_detected": auto_detected
        }

        data["session_intents"].append(record)
        self._save_data(data)

        return record

    def get_connection_seeking_frequency(self, days: int = 30) -> Dict:
        """
        Analyze connection-seeking patterns over time.

        Returns frequency and trend data for anti-engagement metrics.
        """
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        data = self._load_data()
        intents = data.get("session_intents", [])

        recent = [i for i in intents if i.get("date", "") >= cutoff]

        total = len(recent)
        connection_count = sum(1 for i in recent if i.get("intent") == INTENT_CONNECTION)
        practical_count = sum(1 for i in recent if i.get("intent") == INTENT_PRACTICAL)
        processing_count = sum(1 for i in recent if i.get("intent") == INTENT_PROCESSING)

        # Calculate ratio
        connection_ratio = connection_count / total if total > 0 else 0

        # Determine if this is a concern
        is_concerning = connection_ratio > 0.3 and connection_count >= 3

        return {
            "total_sessions": total,
            "connection_seeking": connection_count,
            "practical": practical_count,
            "processing": processing_count,
            "connection_ratio": round(connection_ratio, 2),
            "is_concerning": is_concerning,
            "days_analyzed": days
        }

    def get_recent_intent(self) -> Optional[str]:
        """Get the most recent recorded session intent."""
        data = self._load_data()
        intents = data.get("session_intents", [])

        if intents:
            return intents[-1].get("intent")
        return None
