"""
searchable_index.py - Builds an encrypted inverted index over a document corpus.

The SearchableIndex class:
  1. Tokenises each document into keywords.
  2. Replaces each keyword with its deterministic HMAC token.
  3. Maps token → [encrypted doc IDs].
  4. Stores the original documents in encrypted form.

This mirrors the *setup* phase of a basic SSE scheme (e.g., Curtmola et al. 2006).
"""

import re
from typing import Dict, List

from .encryption import encrypt, deterministic_encrypt


class SearchableIndex:
    """
    Encrypted inverted index for a collection of plaintext documents.

    After calling build_index() the instance exposes:
      - An *encrypted index*: token → [encrypted_doc_id, ...]
      - A *document store*:   encrypted_doc_id → encrypted_content

    Both structures are stored server-side.  The server sees only opaque
    byte strings — it cannot read keywords or document content.
    """

    def __init__(self) -> None:
        # token (hex str) → set of encrypted doc-ID hex strings (set for O(1) dedup)
        self._index_sets: Dict[str, set] = {}
        # token (hex str) → list of encrypted doc-ID hex strings (finalised view)
        self._index: Dict[str, List[str]] = {}
        # encrypted doc-ID (hex str) → encrypted content bytes
        self._document_store: Dict[str, bytes] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_index(self, key: bytes, documents: List[Dict[str, str]]) -> None:
        """
        Tokenise, encrypt and index the provided *documents*.

        Each document must be a dict with at least:
          - ``id``: a unique string identifier
          - ``content``: the plaintext body of the document

        Args:
            key: 32-byte AES secret key used for all encryption operations.
            documents: List of document dicts.
        """
        self._index_sets = {}
        self._index = {}
        self._document_store = {}

        for doc in documents:
            doc_id: str = doc["id"]
            content: str = doc["content"]

            # Encrypt the document ID and content and store them
            enc_doc_id: bytes = encrypt(key, doc_id)
            enc_content: bytes = encrypt(key, content)
            # Use a hex key for the document store so it is JSON-serialisable
            enc_doc_id_hex: str = enc_doc_id.hex()
            self._document_store[enc_doc_id_hex] = enc_content

            # Extract keywords from the document content
            keywords = self._extract_keywords(content)

            for keyword in keywords:
                # Replace the plaintext keyword with its deterministic token
                token: str = deterministic_encrypt(key, keyword)
                if token not in self._index_sets:
                    self._index_sets[token] = set()
                # Use a set for O(1) duplicate detection
                self._index_sets[token].add(enc_doc_id_hex)

        # Convert sets to sorted lists for a stable, serialisable index
        self._index = {t: sorted(docs) for t, docs in self._index_sets.items()}

    def get_index(self) -> Dict[str, List[str]]:
        """
        Return the encrypted inverted index.

        Returns:
            dict: token (str) → [encrypted_doc_id_hex (str), ...]
        """
        return dict(self._index)

    def get_document_store(self) -> Dict[str, bytes]:
        """
        Return the encrypted document store.

        Returns:
            dict: encrypted_doc_id_hex (str) → encrypted_content (bytes)
        """
        return dict(self._document_store)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """
        Extract unique, lowercase, alphabetic keywords (length ≥ 3) from *text*.

        A minimal stopword list is applied to reduce noise.

        Args:
            text: Plaintext string to tokenise.

        Returns:
            List[str]: Sorted list of unique keywords.
        """
        stopwords = {
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out", "use",
            "has", "his", "how", "its", "may", "new", "now", "old",
            "see", "two", "who", "did", "get", "let", "put", "say",
            "she", "too", "via", "per",
        }
        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        return sorted({w for w in words if w not in stopwords})
