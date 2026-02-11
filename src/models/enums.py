"""
Type-safe enums for empathySync domain constants.

Using str-based enums (str, Enum) for backward compatibility:
    Domain.LOGISTICS == "logistics"  # True
    Domain.LOGISTICS == Domain.LOGISTICS  # True

This allows gradual migration — existing string comparisons
continue to work when enum values are substituted in.
"""

from enum import Enum


class Domain(str, Enum):
    """Content domain for classification."""

    LOGISTICS = "logistics"
    HEALTH = "health"
    CRISIS = "crisis"
    HARMFUL = "harmful"
    EMOTIONAL = "emotional"
    RELATIONSHIPS = "relationships"
    MONEY = "money"
    SPIRITUALITY = "spirituality"


class Intent(str, Enum):
    """Session intent — why the user is here."""

    PRACTICAL = "practical"
    PROCESSING = "processing"
    EMOTIONAL = "emotional"
    CONNECTION = "connection"


class EmotionalWeight(str, Enum):
    """Emotional weight of a task (not the user's emotional state)."""

    HIGH_WEIGHT = "high_weight"
    MEDIUM_WEIGHT = "medium_weight"
    LOW_WEIGHT = "low_weight"
    REFLECTION_REDIRECT = "reflection_redirect"


class ClassificationMethod(str, Enum):
    """How the classification was determined."""

    LLM = "llm"
    KEYWORD = "keyword"
    FAST_PATH = "fast_path"
    FALLBACK = "fallback"
