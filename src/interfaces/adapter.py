"""
InterfaceAdapter - Protocol for UI adapters that drive a ConversationSession.

Any interface (Streamlit, CLI, messaging) implements this protocol to
receive conversation results and handle user interactions.
"""

from typing import Dict, Iterator, List, Optional, Protocol

from models.conversation_result import ConversationResult


class InterfaceAdapter(Protocol):
    """
    Minimal protocol for conversation interfaces.

    Adapters render results and handle interactive prompts.
    Optional methods can be left unimplemented.
    """

    def render_result(self, result: ConversationResult) -> None:
        """Render the result of processing a message."""
        ...

    def render_stream(self, result: ConversationResult) -> None:
        """Render a streaming result, consuming response_stream token by token."""
        ...

    def prompt_intent_shift(self, shift_info: Dict) -> bool:
        """
        Prompt user about detected intent shift.

        Returns True if user accepts shift, False to continue original intent.
        """
        ...

    def prompt_graduation(self, category: str, prompt_text: str) -> str:
        """
        Prompt user about skill graduation.

        Returns "accept" or "dismiss".
        """
        ...
