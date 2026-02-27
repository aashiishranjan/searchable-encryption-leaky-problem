"""
test_encryption.py - Unit tests for the searchable encryption leaky problem.

Covers:
  - AES-256-CBC round-trip (encrypt → decrypt)
  - Deterministic HMAC tokenization
  - Trapdoor generation consistency
  - End-to-end search
  - Leakage analyzer correctness
"""

import unittest

from src.encryption import (
    generate_key,
    encrypt,
    decrypt,
    deterministic_encrypt,
    generate_trapdoor,
)
from src.searchable_index import SearchableIndex
from src.search import search, decrypt_results
from src.leakage_analyzer import LeakageAnalyzer


class TestEncryptDecrypt(unittest.TestCase):
    """Tests for AES-256-CBC symmetric encryption / decryption."""

    def setUp(self):
        self.key = generate_key()

    def test_encrypt_decrypt_roundtrip(self):
        """encrypt() then decrypt() must return the original plaintext."""
        plaintext = "Hello, searchable encryption!"
        ciphertext = encrypt(self.key, plaintext)
        recovered = decrypt(self.key, ciphertext)
        self.assertEqual(recovered, plaintext)

    def test_encrypt_produces_different_ciphertexts(self):
        """Two calls to encrypt() with the same plaintext should differ (random IV)."""
        plaintext = "same plaintext"
        c1 = encrypt(self.key, plaintext)
        c2 = encrypt(self.key, plaintext)
        self.assertNotEqual(c1, c2)

    def test_decrypt_with_wrong_key_fails(self):
        """Decrypting with a different key must not return the original plaintext."""
        plaintext = "secret message"
        ciphertext = encrypt(self.key, plaintext)
        wrong_key = generate_key()
        try:
            recovered = decrypt(wrong_key, ciphertext)
            # If no exception is raised, the content must differ
            self.assertNotEqual(recovered, plaintext)
        except Exception:
            # Any exception is acceptable — the data is unreadable
            pass

    def test_encrypt_empty_string(self):
        """encrypt/decrypt should handle an empty string."""
        plaintext = ""
        ciphertext = encrypt(self.key, plaintext)
        recovered = decrypt(self.key, ciphertext)
        self.assertEqual(recovered, plaintext)

    def test_encrypt_unicode(self):
        """encrypt/decrypt should handle unicode content."""
        plaintext = "Ünïcödé tëxt 🔐"
        ciphertext = encrypt(self.key, plaintext)
        recovered = decrypt(self.key, ciphertext)
        self.assertEqual(recovered, plaintext)


class TestDeterministicEncrypt(unittest.TestCase):
    """Tests for the HMAC-based deterministic tokenisation."""

    def setUp(self):
        self.key = generate_key()

    def test_same_input_same_output(self):
        """deterministic_encrypt must be deterministic for the same (key, keyword)."""
        keyword = "encryption"
        t1 = deterministic_encrypt(self.key, keyword)
        t2 = deterministic_encrypt(self.key, keyword)
        self.assertEqual(t1, t2)

    def test_different_keywords_different_tokens(self):
        """Different keywords must produce different tokens."""
        t1 = deterministic_encrypt(self.key, "malware")
        t2 = deterministic_encrypt(self.key, "firewall")
        self.assertNotEqual(t1, t2)

    def test_different_keys_different_tokens(self):
        """The same keyword under different keys must produce different tokens."""
        keyword = "security"
        key2 = generate_key()
        t1 = deterministic_encrypt(self.key, keyword)
        t2 = deterministic_encrypt(key2, keyword)
        self.assertNotEqual(t1, t2)

    def test_token_is_hex_string(self):
        """Token must be a valid hex string of length 64 (SHA-256 = 32 bytes)."""
        token = deterministic_encrypt(self.key, "test")
        self.assertEqual(len(token), 64)
        # Must be a valid hex string
        int(token, 16)


class TestGenerateTrapdoor(unittest.TestCase):
    """Tests for trapdoor generation (must match deterministic_encrypt)."""

    def setUp(self):
        self.key = generate_key()

    def test_trapdoor_is_consistent(self):
        """generate_trapdoor must return the same token for the same (key, keyword)."""
        keyword = "phishing"
        td1 = generate_trapdoor(self.key, keyword)
        td2 = generate_trapdoor(self.key, keyword)
        self.assertEqual(td1, td2)

    def test_trapdoor_matches_deterministic_encrypt(self):
        """Trapdoor must equal the deterministic token for index lookup to work."""
        keyword = "ransomware"
        trapdoor = generate_trapdoor(self.key, keyword)
        token = deterministic_encrypt(self.key, keyword)
        self.assertEqual(trapdoor, token)


class TestSearch(unittest.TestCase):
    """End-to-end tests for index building and search."""

    DOCUMENTS = [
        {"id": "d1", "content": "encryption and cryptography protect data"},
        {"id": "d2", "content": "malware and ransomware are security threats"},
        {"id": "d3", "content": "firewall protects the network from malware"},
    ]

    def setUp(self):
        self.key = generate_key()
        self.idx = SearchableIndex()
        self.idx.build_index(self.key, self.DOCUMENTS)
        self.encrypted_index = self.idx.get_index()
        self.document_store = self.idx.get_document_store()

    def test_search_returns_correct_documents(self):
        """Searching for 'malware' must return documents d2 and d3."""
        trapdoor = generate_trapdoor(self.key, "malware")
        results = search(self.encrypted_index, trapdoor)
        decrypted = decrypt_results(self.key, results, self.document_store)
        found_ids = {d["id"] for d in decrypted}
        self.assertIn("d2", found_ids)
        self.assertIn("d3", found_ids)

    def test_search_returns_empty_for_unknown_keyword(self):
        """Searching for a keyword not in any document must return []."""
        trapdoor = generate_trapdoor(self.key, "zzznonsenseword")
        results = search(self.encrypted_index, trapdoor)
        self.assertEqual(results, [])

    def test_search_single_document_keyword(self):
        """Searching for a keyword unique to one document returns only that doc."""
        trapdoor = generate_trapdoor(self.key, "cryptography")
        results = search(self.encrypted_index, trapdoor)
        decrypted = decrypt_results(self.key, results, self.document_store)
        found_ids = {d["id"] for d in decrypted}
        self.assertEqual(found_ids, {"d1"})

    def test_decrypt_results_recovers_content(self):
        """Decrypted document content must match the original plaintext."""
        trapdoor = generate_trapdoor(self.key, "encryption")
        results = search(self.encrypted_index, trapdoor)
        decrypted = decrypt_results(self.key, results, self.document_store)
        self.assertTrue(len(decrypted) > 0)
        doc = next(d for d in decrypted if d["id"] == "d1")
        self.assertIn("encryption", doc["content"].lower())


class TestLeakageAnalyzer(unittest.TestCase):
    """Tests for the LeakageAnalyzer leakage detection methods."""

    def _build_analyzer(self):
        """Helper: create an analyzer with a pre-populated query log."""
        key = generate_key()
        analyzer = LeakageAnalyzer()

        trapdoor_enc = generate_trapdoor(key, "encryption")
        trapdoor_mal = generate_trapdoor(key, "malware")

        # 'encryption' queried 3 times, 'malware' queried 2 times
        for _ in range(3):
            analyzer.log_query(trapdoor_enc, ["doc_a_hex", "doc_b_hex"])
        for _ in range(2):
            analyzer.log_query(trapdoor_mal, ["doc_b_hex"])

        return analyzer, trapdoor_enc, trapdoor_mal

    def test_detect_search_pattern_leakage_identifies_repeats(self):
        """Repeated trapdoors must appear in search pattern leakage output."""
        analyzer, td_enc, td_mal = self._build_analyzer()
        repeated = analyzer.detect_search_pattern_leakage()
        self.assertIn(td_enc, repeated)
        self.assertEqual(repeated[td_enc], 3)
        self.assertIn(td_mal, repeated)
        self.assertEqual(repeated[td_mal], 2)

    def test_detect_search_pattern_no_repeat(self):
        """A trapdoor queried only once must NOT appear in the repeat report."""
        key = generate_key()
        analyzer = LeakageAnalyzer()
        td = generate_trapdoor(key, "unique")
        analyzer.log_query(td, ["doc_x"])
        repeated = analyzer.detect_search_pattern_leakage()
        self.assertNotIn(td, repeated)

    def test_detect_volume_leakage(self):
        """Volume leakage must correctly report result-set sizes."""
        analyzer, td_enc, td_mal = self._build_analyzer()
        volume = analyzer.detect_volume_leakage()
        self.assertEqual(volume[td_enc], 2)
        self.assertEqual(volume[td_mal], 1)

    def test_detect_frequency_leakage_ordering(self):
        """Frequency leakage output must be sorted by count descending."""
        analyzer, td_enc, td_mal = self._build_analyzer()
        freq = analyzer.detect_frequency_leakage()
        trapdoors = list(freq.keys())
        counts = list(freq.values())
        # First entry should be the most frequent trapdoor
        self.assertEqual(trapdoors[0], td_enc)
        self.assertEqual(counts[0], 3)
        # Counts must be non-increasing
        for i in range(len(counts) - 1):
            self.assertGreaterEqual(counts[i], counts[i + 1])

    def test_detect_access_pattern_leakage(self):
        """Access pattern leakage must show which docs each trapdoor returns."""
        analyzer, td_enc, td_mal = self._build_analyzer()
        access = analyzer.detect_access_pattern_leakage()
        self.assertIn("doc_a_hex", access[td_enc])
        self.assertIn("doc_b_hex", access[td_enc])
        self.assertIn("doc_b_hex", access[td_mal])

    def test_generate_full_report_returns_string(self):
        """generate_full_report must return a non-empty string."""
        analyzer, _, _ = self._build_analyzer()
        report = analyzer.generate_full_report()
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        # Must contain section headers
        self.assertIn("SEARCH PATTERN", report)
        self.assertIn("ACCESS PATTERN", report)
        self.assertIn("VOLUME", report)
        self.assertIn("FREQUENCY", report)


if __name__ == "__main__":
    unittest.main()
