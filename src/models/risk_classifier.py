"""
RiskClassifier - estimates domain and influence / dependency risk
Used by WellnessGuide to become influence-aware without taking over decisions.
"""

from typing import List, Dict


class RiskClassifier:
    """
    Detect rough domain, emotional intensity, and dependency risk
    based on the current user input and recent conversation history.
    """

    def classify(
        self,
        user_input: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """
        Return a simple risk assessment dictionary.

        Example:
        {
            "domain": "spirituality",
            "emotional_intensity": 7.0,
            "dependency_risk": 3.0,
            "risk_weight": 8.1
        }
        """
        domain = self._detect_domain(user_input)
        emotional_intensity = self._measure_emotional_intensity(user_input)
        dependency_risk = self._assess_dependency(conversation_history)

        risk_weight = self._combine_scores(domain, emotional_intensity, dependency_risk)

        return {
            "domain": domain,
            "emotional_intensity": emotional_intensity,
            "dependency_risk": dependency_risk,
            "risk_weight": risk_weight
        }

    def _detect_domain(self, text: str) -> str:
        """Very simple keyword based domain detection."""
        t = text.lower()

        if any(w in t for w in ["loan", "debt", "salary", "investment", "mortgage", "budget", "pay", "crypto"]):
            return "money"

        if any(w in t for w in ["doctor", "hospital", "symptom", "illness", "diagnosis", "medication", "therapy", "panic attack"]):
            return "health"

        if any(w in t for w in ["relationship", "marriage", "boyfriend", "girlfriend", "partner", "breakup", "divorce", "argument"]):
            return "relationships"

        if any(w in t for w in ["god", "father in heaven", "holy spirit", "calling", "destiny", "prophecy", "spiritual", "anointing", "ministry"]):
            return "spirituality"

        if any(w in t for w in ["kill myself", "suicide", "do not want to live", "end it all"]):
            return "crisis"

        if any(w in t for w in [
            "rob", "robbing", "robbery", "steal", "stealing", "murder", "kill someone",
            "hurt someone", "attack", "bomb", "weapon", "illegal", "hack into",
            "break into", "fraud", "scam someone", "forge", "counterfeit",
            "want to kill", "going to kill", "plan to kill", "how to kill",
            "poison", "strangle", "shoot", "stab"
        ]):
            return "harmful"

        return "logistics"

    def _measure_emotional_intensity(self, text: str) -> float:
        """
        Crude emotional intensity scale 0–10 based on certain markers.
        This is deliberately simple and conservative.
        """
        t = text.lower()

        high_markers = [
            "terrified", "desperate", "panic attack", "cannot breathe",
            "kill myself", "suicide", "end it all", "no reason to live"
        ]
        medium_markers = [
            "afraid", "anxious", "overwhelmed", "ashamed",
            "confused", "lost", "heartbroken", "furious"
        ]
        low_markers = [
            "tired", "stressed", "worried", "sad"
        ]

        if any(m in t for m in high_markers):
            return 9.0
        if any(m in t for m in medium_markers):
            return 6.0
        if any(m in t for m in low_markers):
            return 4.0

        return 3.0  # fairly neutral default

    def _assess_dependency(self, history: List[Dict]) -> float:
        """
        Very rough dependency heuristic:
        - More turns recently → slightly higher risk.
        - Repeating similar content → higher risk.
        """
        if not history:
            return 0.0

        recent = history[-12:]  # last 12 messages (user + assistant)
        user_messages = [m["content"] for m in recent if m.get("role") == "user"]

        if not user_messages:
            return 0.0

        n = len(user_messages)

        # Base on frequency: many recent user turns → higher score
        base = min(n * 0.7, 6.0)  # cap at 6 from frequency alone

        # Check repetition of similar openings (very crude)
        prefixes = [m[:60].lower() for m in user_messages]
        unique_prefixes = len(set(prefixes))
        repetition_ratio = 1.0 - (unique_prefixes / max(len(prefixes), 1))

        repetition_boost = repetition_ratio * 4.0  # up to +4

        score = base + repetition_boost
        return min(score, 10.0)

    def _combine_scores(self, domain: str, intensity: float, dependency: float) -> float:
        """
        Combine domain, intensity, and dependency to a single 0–10 risk score.
        This is not precise, only a first approximation.
        """
        domain_weight = {
            "logistics": 1.0,
            "money": 6.0,
            "health": 7.0,
            "relationships": 5.0,
            "spirituality": 8.0,
            "crisis": 10.0,
            "harmful": 10.0
        }

        base = domain_weight.get(domain, 2.0)

        score = base
        score += 0.3 * intensity
        score += 0.2 * dependency

        return float(min(score, 10.0))
