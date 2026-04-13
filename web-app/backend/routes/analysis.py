"""
routes/analysis.py - Leakage analysis and query history endpoints.

Endpoints
---------
GET /api/analysis   Full leakage analysis for the current session.
GET /api/history    Query history with statistics.
"""

from flask import Blueprint, jsonify, session as flask_session

import session_manager
from config import KNOWN_KEYWORD_FREQUENCIES

analysis_bp = Blueprint("analysis", __name__)


def _sid():
    return flask_session.get("sid")


# ---------------------------------------------------------------------------
# GET /api/analysis
# ---------------------------------------------------------------------------

@analysis_bp.route("/analysis", methods=["GET"])
def get_analysis():
    """
    Return the full leakage analysis for the current session.

    Includes all four leakage types and the frequency-analysis attack results.
    """
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    analyzer = sess["analyzer"]
    total_queries = len(analyzer._query_log)

    if total_queries == 0:
        return jsonify(
            {
                "total_queries": 0,
                "message": "No queries logged yet. Perform a search first.",
                "search_pattern": {},
                "access_pattern": {},
                "volume": {},
                "frequency": {},
                "attack_results": [],
            }
        )

    # Search pattern leakage
    search_pattern = analyzer.detect_search_pattern_leakage()
    sp_entries = [
        {"trapdoor": td[:24] + "...", "count": cnt}
        for td, cnt in sorted(search_pattern.items(), key=lambda kv: -kv[1])
    ]

    # Access pattern leakage
    access_pattern = analyzer.detect_access_pattern_leakage()
    ap_entries = [
        {
            "trapdoor": td[:24] + "...",
            "doc_count": len(docs),
            "docs": [d[-16:] for d in sorted(docs)[:5]],
        }
        for td, docs in access_pattern.items()
    ]

    # Volume leakage
    volume = analyzer.detect_volume_leakage()
    vol_entries = [
        {"trapdoor": td[:24] + "...", "result_count": cnt}
        for td, cnt in sorted(volume.items(), key=lambda kv: -kv[1])
    ]

    # Frequency leakage
    freq = analyzer.detect_frequency_leakage()
    freq_entries = [
        {
            "trapdoor": td[:24] + "...",
            "count": cnt,
            "percentage": round(cnt / total_queries * 100, 1) if total_queries > 0 else 0,
        }
        for td, cnt in freq.items()
    ]

    # Frequency analysis attack
    from attack_simulation import FrequencyAnalysisAttack

    attack = FrequencyAnalysisAttack(KNOWN_KEYWORD_FREQUENCIES, freq)
    attack_raw = attack.run_attack()
    attack_entries = [
        {
            "trapdoor": r["trapdoor"][:24] + "...",
            "guessed_keyword": r["guessed_keyword"],
            "trapdoor_frequency": r["trapdoor_frequency"],
            "known_frequency": r["known_frequency"],
            "confidence": r["confidence"],
            "confidence_pct": round(r["confidence"] * 100, 1),
        }
        for r in attack_raw
    ]

    return jsonify(
        {
            "total_queries": total_queries,
            "search_pattern": {
                "label": "Search Pattern / 3-gram Leakage",
                "repeated_count": len(sp_entries),
                "entries": sp_entries,
            },
            "access_pattern": {
                "label": "Access Pattern / Document Leakage",
                "entries": ap_entries,
            },
            "volume": {
                "label": "Volume / Result Leakage",
                "entries": vol_entries,
            },
            "frequency": {
                "label": "Frequency / Term Leakage",
                "entries": freq_entries,
            },
            "attack_results": attack_entries,
        }
    )


# ---------------------------------------------------------------------------
# GET /api/history
# ---------------------------------------------------------------------------

@analysis_bp.route("/history", methods=["GET"])
def get_history():
    """Return the query history and basic statistics for the current session."""
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    history = sess["query_history"]
    total = len(history)

    # Keyword frequency in the history
    kw_counts: dict = {}
    mode_counts = {"before": 0, "after": 0}
    for entry in history:
        kw = entry["keyword"]
        kw_counts[kw] = kw_counts.get(kw, 0) + 1
        mode_counts[entry["mode"]] = mode_counts.get(entry["mode"], 0) + 1

    top_keywords = sorted(kw_counts.items(), key=lambda kv: -kv[1])[:10]

    return jsonify(
        {
            "history": history,
            "total": total,
            "statistics": {
                "top_keywords": [{"keyword": kw, "count": cnt} for kw, cnt in top_keywords],
                "mode_breakdown": mode_counts,
                "unique_keywords": len(kw_counts),
            },
        }
    )
