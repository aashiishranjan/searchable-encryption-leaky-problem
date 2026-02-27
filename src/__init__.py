"""
Searchable Encryption Leaky Problem - Source Package

This package demonstrates the leakage vulnerabilities inherent in
Searchable Symmetric Encryption (SSE) schemes.
"""

from .encryption import generate_key, encrypt, decrypt, deterministic_encrypt, generate_trapdoor
from .searchable_index import SearchableIndex
from .search import search, decrypt_results
from .leakage_analyzer import LeakageAnalyzer
from .attack_simulation import FrequencyAnalysisAttack

__all__ = [
    "generate_key",
    "encrypt",
    "decrypt",
    "deterministic_encrypt",
    "generate_trapdoor",
    "SearchableIndex",
    "search",
    "decrypt_results",
    "LeakageAnalyzer",
    "FrequencyAnalysisAttack",
]
