"""
routes/search.py - Keyword search endpoints.

Endpoints
---------
POST /api/search    Search by keyword; returns results + full 6-step breakdown.
POST /api/compare   Run the same keyword in BEFORE and AFTER mode simultaneously.
"""

import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session as flask_session

import session_manager
from config import KNOWN_KEYWORD_FREQUENCIES, PADDED_RESULT_SIZE, SAMPLE_DOCUMENTS
from src.encryption import generate_trapdoor
from src.search import search as sse_search, decrypt_results
from src.attack_simulation import FrequencyAnalysisAttack

search_bp = Blueprint("search", __name__)

# Mitigation strategies catalogue (used in Step 6)
_MITIGATIONS = [
    {
        "name": "ORAM (Oblivious RAM)",
        "description": (
            "Randomises access patterns so the server cannot link queries "
            "to documents. Significant communication overhead."
        ),
        "addresses": ["access_pattern"],
    },
    {
        "name": "Result Padding",
        "description": (
            "Pads all result sets to a fixed (or random) size, hiding "
            "volume leakage. Costs bandwidth."
        ),
        "addresses": ["volume"],
        "active_in_after": True,
    },
    {
        "name": "Differential Privacy",
        "description": (
            "Adds calibrated noise to query frequencies so frequency "
            "analysis attacks become statistically unreliable."
        ),
        "addresses": ["frequency"],
    },
    {
        "name": "Forward Privacy (OSSE)",
        "description": (
            "Ensures that newly added documents cannot be linked to "
            "previous queries — breaks the access pattern."
        ),
        "addresses": ["access_pattern", "search_pattern"],
    },
    {
        "name": "Randomised Trapdoors (STE)",
        "description": (
            "Uses probabilistic trapdoor generation so repeated searches "
            "produce different tokens, hiding search pattern leakage."
        ),
        "addresses": ["search_pattern", "frequency"],
    },
    {
        "name": "Secure Multi-Party Computation",
        "description": (
            "Distributes the search computation across multiple servers "
            "so no single server observes the full query."
        ),
        "addresses": ["access_pattern", "volume", "search_pattern", "frequency"],
    },
]


def _sid():
    return flask_session.get("sid")


def _pad_results(results: list, target_size: int) -> list:
    """Pad *results* with random dummy IDs to reach *target_size* entries."""
    padded = list(results)
    while len(padded) < target_size:
        padded.append(os.urandom(16).hex())
    return padded


def _build_step4(sess: dict, current_trapdoor: str, mode: str) -> dict:
    """Build the Step-4 leakage-analysis payload from the session analyser."""
    analyzer = sess["analyzer"]

    # --- search-pattern / 3-gram leakage ---
    search_pattern = analyzer.detect_search_pattern_leakage()
    repeated_trapdoors = [
        {"trapdoor": td[:24] + "...", "count": cnt}
        for td, cnt in sorted(search_pattern.items(), key=lambda kv: -kv[1])
    ]

    # --- access-pattern / document leakage ---
    access_pattern = analyzer.detect_access_pattern_leakage()
    access_entries = []
    for td, docs in access_pattern.items():
        access_entries.append(
            {
                "trapdoor": td[:24] + "...",
                "doc_count": len(docs),
                "docs": [d[-16:] for d in docs[:5]],
            }
        )

    # --- volume / result leakage ---
    volume = analyzer.detect_volume_leakage()
    volume_entries = [
        {"trapdoor": td[:24] + "...", "result_count": cnt}
        for td, cnt in sorted(volume.items(), key=lambda kv: -kv[1])
    ]

    # --- frequency / term leakage ---
    freq = analyzer.detect_frequency_leakage()
    total = len(analyzer._query_log)
    freq_entries = [
        {
            "trapdoor": td[:24] + "...",
            "count": cnt,
            "percentage": round(cnt / total * 100, 1) if total > 0 else 0,
        }
        for td, cnt in list(freq.items())[:10]
    ]

    return {
        "title": "Step 4: Leakage Analysis",
        "description": (
            "The server analyses the query log using only trapdoor tokens "
            "and result sizes. It never sees plaintext keywords."
        ),
        "leakage_types": {
            "ngram": {
                "label": "3-gram / Search Pattern Leakage",
                "description": (
                    "The server detects when the SAME keyword is searched "
                    "multiple times because the trapdoor token is deterministic."
                ),
                "repeated_count": len(repeated_trapdoors),
                "entries": repeated_trapdoors,
            },
            "document": {
                "label": "Access Pattern / Document Leakage",
                "description": (
                    "The server sees WHICH encrypted documents are returned "
                    "for each trapdoor — revealing document co-occurrence."
                ),
                "entries": access_entries,
            },
            "term": {
                "label": "Frequency / Term Leakage",
                "description": (
                    "Over many queries the server builds a frequency histogram "
                    "of trapdoor usage that mirrors keyword popularity."
                ),
                "entries": freq_entries,
            },
            "result": {
                "label": "Volume / Result Leakage",
                "description": (
                    "The server learns HOW MANY documents match each query, "
                    "revealing the keyword's document frequency."
                ),
                "entries": volume_entries,
                "padded": mode == "after",
                "padded_size": PADDED_RESULT_SIZE if mode == "after" else None,
            },
        },
    }


def _build_step5(sess: dict) -> dict:
    """Build the Step-5 frequency-analysis attack payload."""
    observed_freq = sess["analyzer"].detect_frequency_leakage()
    attack = FrequencyAnalysisAttack(KNOWN_KEYWORD_FREQUENCIES, observed_freq)
    results = attack.run_attack()

    return {
        "title": "Step 5: Frequency Analysis Attack",
        "description": (
            "The adversary correlates observed trapdoor frequencies with a known "
            "background keyword frequency distribution to guess plaintext keywords. "
            "(Islam et al. 2012 — rank-correlation method)"
        ),
        "known_frequencies": KNOWN_KEYWORD_FREQUENCIES,
        "attack_results": [
            {
                "trapdoor": r["trapdoor"][:24] + "...",
                "guessed_keyword": r["guessed_keyword"],
                "trapdoor_frequency": r["trapdoor_frequency"],
                "known_frequency": r["known_frequency"],
                "confidence": r["confidence"],
                "confidence_pct": round(r["confidence"] * 100, 1),
            }
            for r in results
        ],
    }


def _build_step6(mode: str) -> dict:
    """Build the Step-6 mitigation strategies payload."""
    strategies = []
    for m in _MITIGATIONS:
        strategies.append(
            {
                "name": m["name"],
                "description": m["description"],
                "addresses": m["addresses"],
                "active": mode == "after" and m.get("active_in_after", False),
            }
        )

    return {
        "title": "Step 6: Mitigation Strategies",
        "description": (
            "Countermeasures that reduce or eliminate the leakage types "
            "observed in Steps 4 and 5."
        ),
        "mode": mode,
        "strategies": strategies,
    }


def _run_search(sess: dict, keyword: str, mode: str) -> dict:
    """
    Execute a single search and return the full 6-step result dict.

    Does NOT append to query_history – the caller is responsible for that.
    """
    key = sess["key"]
    encrypted_index = sess["encrypted_index"]
    document_store = sess["document_store"]
    analyzer = sess["analyzer"]

    # --- Step 1 ---
    step1 = {
        "title": "Step 1: Key Generation",
        "description": (
            "A 256-bit AES secret key is generated client-side and never "
            "shared with the server."
        ),
        "key_hex": sess["key_hex"][:32] + "...",
        "key_length_bytes": 32,
        "algorithm": "AES-256",
    }

    # --- Step 2 ---
    num_tokens = len(encrypted_index)
    sample_entries = [
        {"token": t[:24] + "...", "doc_count": len(docs)}
        for t, docs in list(encrypted_index.items())[:5]
    ]
    step2 = {
        "title": "Step 2: Index Building",
        "description": (
            "Documents are tokenised; each keyword is replaced by its "
            "HMAC-SHA256 token before being stored on the server."
        ),
        "num_documents": len(sess["documents"]),
        "num_tokens": num_tokens,
        "sample_entries": sample_entries,
        "observation": (
            "The server sees only random-looking tokens — it cannot tell "
            "which token corresponds to which keyword."
        ),
    }

    # --- Step 3 ---
    trapdoor = generate_trapdoor(key, keyword)
    step3 = {
        "title": "Step 3: Search Query / Trapdoor",
        "description": (
            "The client generates a trapdoor token for the keyword and "
            "sends it to the server.  The keyword itself is never transmitted."
        ),
        "keyword": keyword,
        "trapdoor_preview": trapdoor[:24] + "...",
        "mode": mode,
        "padding_note": (
            f"Results will be padded to {PADDED_RESULT_SIZE} entries "
            "(volume-leakage mitigation)."
            if mode == "after"
            else "Results reflect real match counts — volume leakage is visible."
        ),
    }

    # --- Actual search ---
    real_results = sse_search(encrypted_index, trapdoor)

    if mode == "after":
        server_visible = _pad_results(real_results, PADDED_RESULT_SIZE)
    else:
        server_visible = real_results

    # Log for leakage analysis
    analyzer.log_query(trapdoor, server_visible)

    # Decrypt (client-side)
    decrypted = decrypt_results(key, real_results, document_store)

    # --- Step 4, 5, 6 ---
    step4 = _build_step4(sess, trapdoor, mode)
    step5 = _build_step5(sess)
    step6 = _build_step6(mode)

    return {
        "keyword": keyword,
        "mode": mode,
        "trapdoor": trapdoor[:24] + "...",
        "results": decrypted,
        "real_count": len(real_results),
        "padded_count": len(server_visible) if mode == "after" else None,
        "steps": {
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4,
            "step5": step5,
            "step6": step6,
        },
    }


# ---------------------------------------------------------------------------
# POST /api/search
# ---------------------------------------------------------------------------

@search_bp.route("/search", methods=["POST"])
def search_keyword():
    """
    Search by keyword.

    Expected JSON body::

        {"keyword": "encryption", "mode": "before"}

    ``mode`` must be ``"before"`` or ``"after"``.
    """
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    data = request.get_json(silent=True) or {}
    keyword = (data.get("keyword") or "").strip().lower()
    mode = (data.get("mode") or "before").strip().lower()

    if not keyword:
        return jsonify({"error": "Provide a non-empty 'keyword'."}), 400
    if mode not in ("before", "after"):
        return jsonify({"error": "'mode' must be 'before' or 'after'."}), 400

    if not sess["initialized"]:
        return jsonify(
            {
                "error": (
                    "No documents loaded. "
                    "POST /api/upload/samples first to load the sample corpus."
                )
            }
        ), 400

    result = _run_search(sess, keyword, mode)

    # Append to query history
    sess["query_history"].append(
        {
            "keyword": keyword,
            "mode": mode,
            "result_count": result["real_count"],
            "padded_count": result["padded_count"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    return jsonify(result)


# ---------------------------------------------------------------------------
# POST /api/compare
# ---------------------------------------------------------------------------

@search_bp.route("/compare", methods=["POST"])
def compare_keyword():
    """
    Run the same keyword in BEFORE and AFTER mode and return both results.

    Expected JSON body::

        {"keyword": "encryption"}

    The comparison queries are NOT appended to the session query history so
    they do not skew the leakage analysis.
    """
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    data = request.get_json(silent=True) or {}
    keyword = (data.get("keyword") or "").strip().lower()

    if not keyword:
        return jsonify({"error": "Provide a non-empty 'keyword'."}), 400

    if not sess["initialized"]:
        return jsonify(
            {
                "error": (
                    "No documents loaded. "
                    "POST /api/upload/samples first."
                )
            }
        ), 400

    before = _run_search(sess, keyword, "before")
    after = _run_search(sess, keyword, "after")

    return jsonify({"keyword": keyword, "before": before, "after": after})
