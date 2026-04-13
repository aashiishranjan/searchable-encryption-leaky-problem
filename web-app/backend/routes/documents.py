"""
routes/documents.py - Document upload and management endpoints.

Endpoints
---------
GET  /api/documents          List documents in the current session.
POST /api/upload             Upload custom documents (JSON body).
POST /api/upload/samples     Load the built-in sample document corpus.
POST /api/reset              Wipe the current session and start fresh.
"""

from flask import Blueprint, jsonify, request, session as flask_session

import session_manager
from config import SAMPLE_DOCUMENTS
from src.searchable_index import SearchableIndex

documents_bp = Blueprint("documents", __name__)


def _sid():
    """Return the session ID from the Flask signed-cookie session."""
    return flask_session.get("sid")


def _rebuild_index(sess: dict) -> None:
    """
    (Re-)build the encrypted searchable index from sess['documents'].

    Mutates *sess* in-place, setting:
      - ``encrypted_index``
      - ``document_store``
      - ``initialized``
    """
    builder = SearchableIndex()
    builder.build_index(sess["key"], sess["documents"])
    sess["encrypted_index"] = builder.get_index()
    sess["document_store"] = builder.get_document_store()
    sess["initialized"] = True


# ---------------------------------------------------------------------------
# GET /api/documents
# ---------------------------------------------------------------------------

@documents_bp.route("/documents", methods=["GET"])
def list_documents():
    """Return the list of documents stored in the current session."""
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    return jsonify(
        {
            "documents": sess["documents"],
            "count": len(sess["documents"]),
            "initialized": sess["initialized"],
        }
    )


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------

@documents_bp.route("/upload", methods=["POST"])
def upload_documents():
    """
    Upload custom documents.

    Expected JSON body::

        {
          "documents": [
            {"id": "doc_001", "content": "..."},
            ...
          ]
        }

    The uploaded documents are merged with any existing ones; if a document
    with the same ``id`` already exists it is replaced.  The index is rebuilt
    after every upload.
    """
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    data = request.get_json(silent=True) or {}
    new_docs = data.get("documents", [])

    if not isinstance(new_docs, list) or not new_docs:
        return jsonify({"error": "Provide a non-empty 'documents' list."}), 400

    # Validate each document
    for doc in new_docs:
        if not isinstance(doc, dict) or "id" not in doc or "content" not in doc:
            return jsonify(
                {"error": "Each document must have 'id' and 'content' fields."}
            ), 400
        if not doc["id"].strip() or not doc["content"].strip():
            return jsonify({"error": "Document 'id' and 'content' must be non-empty."}), 400

    # Merge: replace existing docs with same id
    existing = {d["id"]: d for d in sess["documents"]}
    for doc in new_docs:
        existing[doc["id"]] = doc
    sess["documents"] = list(existing.values())

    _rebuild_index(sess)

    return jsonify(
        {
            "success": True,
            "count": len(sess["documents"]),
            "message": f"Indexed {len(sess['documents'])} document(s).",
        }
    )


# ---------------------------------------------------------------------------
# POST /api/upload/samples
# ---------------------------------------------------------------------------

@documents_bp.route("/upload/samples", methods=["POST"])
def load_sample_documents():
    """Load the built-in sample document corpus into the current session."""
    sid, sess, _ = session_manager.get_or_create_session(_sid())
    flask_session["sid"] = sid

    sess["documents"] = list(SAMPLE_DOCUMENTS)
    _rebuild_index(sess)

    return jsonify(
        {
            "success": True,
            "count": len(sess["documents"]),
            "message": f"Loaded {len(sess['documents'])} sample document(s).",
            "documents": sess["documents"],
        }
    )


# ---------------------------------------------------------------------------
# POST /api/reset
# ---------------------------------------------------------------------------

@documents_bp.route("/reset", methods=["POST"])
def reset_session():
    """Wipe the current session and return a fresh one."""
    sid = _sid()
    if sid:
        session_manager.reset_session(sid)
    else:
        sid = session_manager.create_session()
    flask_session["sid"] = sid

    return jsonify({"success": True, "message": "Session reset."})
