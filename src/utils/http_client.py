"""
Shared HTTP client for Ollama API calls.

Provides a module-level httpx.Client with connection pooling.
All Ollama-calling code should use get_http_client() rather than
creating ad-hoc requests sessions.

Using httpx sync client (not async) because Streamlit is synchronous.
When Phase 17 introduces the async daemon, swap to httpx.AsyncClient.
"""

import httpx
import logging

logger = logging.getLogger(__name__)

# Module-level client — reuses TCP connections across calls.
# Lazy-initialized on first access to avoid import-time side effects.
_client: httpx.Client | None = None


def get_http_client() -> httpx.Client:
    """Return the shared httpx.Client, creating it on first call."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        logger.debug("Created shared httpx.Client with connection pooling")
    return _client


def close_http_client() -> None:
    """Close the shared client (call during app shutdown)."""
    global _client
    if _client is not None and not _client.is_closed:
        _client.close()
        _client = None
        logger.debug("Closed shared httpx.Client")
