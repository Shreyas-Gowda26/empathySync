"""
Write Gate for empathySync

Centralized write permission control for read-only mode.
When another device holds the lock, all write operations should be blocked.

Usage:
    from utils.write_gate import set_read_only, require_write, WriteBlockedError

    # In app.py when detecting lock conflict
    set_read_only(True)

    # In storage backends
    @require_write
    def add_check_in(self, ...):
        ...

    # Or manually check
    if not is_write_allowed():
        raise WriteBlockedError("Read-only mode active")
"""

import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Module-level state (thread-safe for single-threaded Streamlit)
_read_only_mode: bool = False


class WriteBlockedError(Exception):
    """Raised when a write operation is attempted in read-only mode."""

    pass


def set_read_only(enabled: bool):
    """
    Set the global read-only mode.

    Call with True when another device holds the lock.
    Call with False when lock is acquired or released.
    """
    global _read_only_mode
    _read_only_mode = enabled
    if enabled:
        logger.info("Write gate: read-only mode enabled")
    else:
        logger.debug("Write gate: read-only mode disabled")


def is_write_allowed() -> bool:
    """Check if writes are currently allowed."""
    return not _read_only_mode


def is_read_only() -> bool:
    """Check if currently in read-only mode."""
    return _read_only_mode


def require_write(func: Callable) -> Callable:
    """
    Decorator that blocks function execution in read-only mode.

    Usage:
        @require_write
        def save_data(self, data):
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        if _read_only_mode:
            logger.warning(f"Write blocked in read-only mode: {func.__name__}")
            raise WriteBlockedError(
                f"Cannot execute {func.__name__}: read-only mode is active. "
                "Close empathySync on the other device first."
            )
        return func(*args, **kwargs)

    return wrapper


def check_write_permission():
    """
    Explicit check that raises if writes are blocked.

    Use this for inline checks instead of the decorator.
    """
    if _read_only_mode:
        raise WriteBlockedError(
            "Cannot write: read-only mode is active. "
            "Close empathySync on the other device first."
        )
