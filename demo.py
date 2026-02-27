"""
demo.py - End-to-end demonstration of the Searchable Encryption Leaky Problem.

Run with:
    python demo.py

This script walks through the full lifecycle of a basic SSE scheme, then
deliberately exposes the four classical leakage types so that you can see
exactly what information a passive (honest-but-curious) server can extract
from encrypted queries — without ever learning the plaintext keywords.
"""

import sys

from src.encryption import generate_key, generate_trapdoor
from src.searchable_index import SearchableIndex
from src.search import search, decrypt_results
from src.leakage_analyzer import LeakageAnalyzer
from src.attack_simulation import FrequencyAnalysisAttack


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(text: str) -> None:
    width = 70
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def section(text: str) -> None:
    print()
    print("-" * 70)
    print(f"  >> {text}")
    print("-" * 70)


def info(text: str) -> None:
    print(f"  {text}")


# ---------------------------------------------------------------------------
# Sample document corpus
# ---------------------------------------------------------------------------

DOCUMENTS = [
    {
        "id": "doc_001",
        "content": (
            "Encryption is the process of converting plaintext data into "
            "ciphertext using a cryptographic algorithm and a secret key. "
            "Strong encryption prevents unauthorised access to sensitive data."
        ),
    },
    {
        "id": "doc_002",
        "content": (
            "A data breach occurs when sensitive or confidential information "
            "is accessed by unauthorised individuals. Data breaches often expose "
            "passwords, credit card numbers, and personal data."
        ),
    },
    {
        "id": "doc_003",
        "content": (
            "A firewall is a network security device that monitors and filters "
            "incoming and outgoing network traffic based on security rules. "
            "Firewalls protect internal networks from external threats."
        ),
    },
    {
        "id": "doc_004",
        "content": (
            "Malware is malicious software designed to damage, disrupt, or gain "
            "unauthorised access to computer systems. Common malware types include "
            "viruses, worms, ransomware, and spyware."
        ),
    },
    {
        "id": "doc_005",
        "content": (
            "Public key cryptography uses a pair of mathematically related keys: "
            "a public key for encryption and a private key for decryption. "
            "RSA and elliptic-curve cryptography are widely used algorithms."
        ),
    },
    {
        "id": "doc_006",
        "content": (
            "Ransomware is a type of malware that encrypts the victim's files and "
            "demands a ransom payment to restore access. Ransomware attacks have "
            "cost organisations billions of dollars in recent years."
        ),
    },
    {
        "id": "doc_007",
        "content": (
            "Intrusion Detection Systems (IDS) monitor network traffic for "
            "suspicious activity and known attack patterns. They alert security "
            "teams when potential threats are detected."
        ),
    },
    {
        "id": "doc_008",
        "content": (
            "Zero-day vulnerabilities are security flaws that are unknown to the "
            "software vendor. Attackers exploit zero-day vulnerabilities before a "
            "patch is available, making them especially dangerous."
        ),
    },
    {
        "id": "doc_009",
        "content": (
            "Phishing is a social engineering attack where adversaries send "
            "fraudulent emails to trick users into revealing credentials or "
            "installing malware. Phishing remains one of the most common attack vectors."
        ),
    },
    {
        "id": "doc_010",
        "content": (
            "Searchable Symmetric Encryption (SSE) allows a client to store "
            "encrypted documents on an untrusted server and later search them "
            "using trapdoor tokens without revealing the query keyword. However, "
            "SSE schemes inevitably leak statistical information — this is the "
            "searchable encryption leaky problem."
        ),
    },
]

# Background keyword frequency distribution (simulates domain knowledge that
# an adversary might have about cybersecurity query logs).
KNOWN_KEYWORD_FREQUENCIES = {
    "encryption":   0.09,
    "malware":      0.08,
    "security":     0.07,
    "data":         0.07,
    "network":      0.06,
    "ransomware":   0.06,
    "attack":       0.05,
    "firewall":     0.05,
    "phishing":     0.04,
    "vulnerability":0.03,
}

# Search queries to execute (some are repeated to trigger search/frequency leakage)
QUERIES = [
    "encryption",
    "malware",
    "encryption",    # repeated → search pattern leakage
    "firewall",
    "ransomware",
    "malware",       # repeated
    "encryption",    # repeated again
    "phishing",
    "security",
    "malware",       # repeated
]


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    banner("SEARCHABLE ENCRYPTION LEAKY PROBLEM — DEMONSTRATION")
    info("This demo illustrates the four classical leakage types in SSE.")
    info("Reference: Curtmola et al. 2006, Islam et al. 2012, Cash et al. 2015")

    # -----------------------------------------------------------------------
    # Step 1: Generate encryption key
    # -----------------------------------------------------------------------
    section("STEP 1: Generate AES-256 Secret Key")
    key = generate_key()
    info(f"Secret key (hex): {key.hex()[:32]}...  [32 bytes, kept by client]")

    # -----------------------------------------------------------------------
    # Step 2: Build the encrypted searchable index
    # -----------------------------------------------------------------------
    section("STEP 2: Build Encrypted Searchable Index")
    info(f"Indexing {len(DOCUMENTS)} documents...")
    index_builder = SearchableIndex()
    index_builder.build_index(key, DOCUMENTS)
    encrypted_index = index_builder.get_index()
    document_store = index_builder.get_document_store()

    info(f"Encrypted index contains {len(encrypted_index)} keyword tokens.")
    info(f"Document store contains {len(document_store)} encrypted documents.")
    info("")
    info("Sample encrypted index entries (server's view):")
    for i, (token, doc_ids) in enumerate(list(encrypted_index.items())[:5]):
        info(f"  Token {i+1}: {token}  →  {len(doc_ids)} doc(s)")
    info("  ... (keywords replaced by opaque HMAC tokens)")
    info("")
    info("OBSERVATION: The server sees only random-looking tokens — it cannot")
    info("tell which token corresponds to which keyword.")

    # -----------------------------------------------------------------------
    # Step 3: Perform searches with trapdoors
    # -----------------------------------------------------------------------
    section("STEP 3: Client Issues Search Queries via Trapdoors")
    info("Queries: " + ", ".join(QUERIES))
    info("")

    analyzer = LeakageAnalyzer()

    for query_keyword in QUERIES:
        trapdoor = generate_trapdoor(key, query_keyword)
        results = search(encrypted_index, trapdoor)

        # Log the query so the leakage analyzer can inspect it
        analyzer.log_query(trapdoor, results)

        # Decrypt results (client-side)
        decrypted = decrypt_results(key, results, document_store)

        info(f"  Query: '{query_keyword}'")
        info(f"    Trapdoor: {trapdoor[:24]}...")
        info(f"    Matching docs: {len(results)}")
        for doc in decrypted:
            snippet = doc["content"][:60].replace("\n", " ")
            info(f"      [{doc['id']}] {snippet}...")
        info("")

    # -----------------------------------------------------------------------
    # Step 4: Leakage Analysis
    # -----------------------------------------------------------------------
    section("STEP 4: Leakage Analysis (Server's Perspective)")
    info("The server now analyses its query log — using ONLY trapdoor tokens")
    info("and result sizes.  It never sees any plaintext keyword.")
    info("")
    report = analyzer.generate_full_report()
    print(report)

    # -----------------------------------------------------------------------
    # Step 5: Frequency Analysis Attack
    # -----------------------------------------------------------------------
    section("STEP 5: Frequency Analysis Attack Simulation")
    info("The adversary correlates observed trapdoor frequencies with a known")
    info("background keyword frequency distribution to guess plaintext keywords.")
    info("")

    observed_frequencies = analyzer.detect_frequency_leakage()
    attack = FrequencyAnalysisAttack(KNOWN_KEYWORD_FREQUENCIES, observed_frequencies)
    attack.print_attack_results()

    # -----------------------------------------------------------------------
    # Step 6: Mitigation Strategies
    # -----------------------------------------------------------------------
    section("STEP 6: Mitigation Strategies")
    mitigations = [
        ("ORAM (Oblivious RAM)",
         "Randomises access patterns so the server cannot link queries\n"
         "    to documents.  Significant communication overhead."),
        ("Result Padding",
         "Pads all result sets to a fixed (or random) size, hiding\n"
         "    volume leakage.  Costs bandwidth."),
        ("Differential Privacy",
         "Adds calibrated noise to query frequencies so frequency\n"
         "    analysis attacks become statistically unreliable."),
        ("Forward Privacy (OSSE)",
         "Ensures that newly added documents cannot be linked to\n"
         "    previous queries — breaks the access pattern."),
        ("Randomised Trapdoors (STE)",
         "Uses probabilistic trapdoor generation so repeated searches\n"
         "    produce different tokens, hiding search pattern leakage."),
        ("Secure Multi-Party Computation",
         "Distributes the search computation across multiple servers\n"
         "    so no single server observes the full query."),
    ]
    for name, desc in mitigations:
        info(f"  [{name}]")
        info(f"    {desc}")
        info("")

    banner("END OF DEMONSTRATION")
    info("This project is for educational purposes only.")
    info("See README.md for references and further reading.")
    print()


if __name__ == "__main__":
    main()
