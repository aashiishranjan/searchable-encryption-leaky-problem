"""
session_manager.py - Server-side session state for the Flask backend.

Each user gets a UUID session ID stored in a signed cookie.  All
stateful Python objects (encryption key, index, leakage analyser) live
in the in-memory _sessions dict keyed by that UUID.
"""

import os
import uuid
from typing import Any, Dict, Optional, Tuple

# Import src/ modules – sys.path is adjusted in app.py before this module loads.
from src.encryption import generate_key
from src.searchable_index import SearchableIndex
from src.leakage_analyzer import LeakageAnalyzer

# In-memory store: session_id → session_data dict.
# NOTE: This is intentionally simple for a demo application.  For production
# use replace with a proper session backend (e.g. Redis with TTL) to avoid
# unbounded memory growth as sessions accumulate.
_sessions: Dict[str, Dict[str, Any]] = {}


def _make_session() -> Dict[str, Any]:
    """Create a fresh, empty session data dict."""
    key = generate_key()
    return {
        "key": key,
        "key_hex": key.hex(),
        "documents": [],
        "encrypted_index": {},
        "document_store": {},
        "analyzer": LeakageAnalyzer(),
        "query_history": [],
        "initialized": False,
    }


def create_session() -> str:
    """
    Allocate a new session and return its UUID string.

    Returns:
        str: The new session ID.
    """
    sid = str(uuid.uuid4())
    _sessions[sid] = _make_session()
    return sid


def get_session(sid: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Return session data for *sid*, or None if the session does not exist.

    Args:
        sid: Session ID string, or None.

    Returns:
        dict | None: Session data dict or None.
    """
    if sid is None:
        return None
    return _sessions.get(sid)


def get_or_create_session(sid: Optional[str]) -> Tuple[str, Dict[str, Any], bool]:
    """
    Return (sid, session_data, created) for *sid*.

    If *sid* is None or unknown a new session is created.

    Args:
        sid: Existing session ID or None.

    Returns:
        Tuple[str, dict, bool]: (session_id, session_data, was_created)
    """
    if sid and sid in _sessions:
        return sid, _sessions[sid], False
    new_sid = create_session()
    return new_sid, _sessions[new_sid], True


def reset_session(sid: str) -> str:
    """
    Wipe and re-initialise a session, returning the same *sid*.

    Args:
        sid: Existing session ID.

    Returns:
        str: The same *sid* with fresh state.
    """
    _sessions[sid] = _make_session()
    return sid


def delete_session(sid: str) -> None:
    """Remove a session from the store."""
    _sessions.pop(sid, None)
