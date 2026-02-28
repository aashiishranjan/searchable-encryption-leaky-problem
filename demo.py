"""
demo.py - End-to-end demonstration of the Searchable Encryption Leaky Problem.

Run with:
    python demo.py

Change the MODE variable below to switch between two educational scenarios:

  MODE = 'before'  — Shows the original SSE scheme with full leakage.
                     The server can observe exact result-set sizes (volume
                     leakage), repeated trapdoors (search-pattern leakage),
                     and the access pattern for every query.

  MODE = 'after'   — Activates result padding (a volume-leakage mitigation).
                     Every result set is padded to PADDED_RESULT_SIZE entries
                     with dummy doc IDs so the server always sees the same
                     number of results, hiding the real match count.
"""

# ---------------------------------------------------------------------------
# MODE SWITCH — set to 'before' (leakage demo) or 'after' (mitigation demo)
# ---------------------------------------------------------------------------
MODE = 'before'   # Change to 'after' to enable volume-leakage mitigation

# Fixed result-set size used when MODE == 'after' (padding target).
PADDED_RESULT_SIZE = 5

import os
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


def pad_results(results: list, target_size: int) -> list:
    """
    Pad *results* with dummy encrypted doc-ID strings to reach *target_size*.

    This is the volume-leakage mitigation used in MODE == 'after'.  The server
    always receives exactly *target_size* entries regardless of how many real
    documents matched, so it cannot infer the true match count.

    The dummy IDs are random hex strings that will not appear in the document
    store; decrypt_results() silently skips them, so the client still sees
    only the genuine documents.

    If ``len(results) >= target_size`` the original list is returned unchanged.

    Args:
        results:     Original list of encrypted doc-ID hex strings.
        target_size: Desired minimum result-set length.

    Returns:
        List[str]: List of length ``max(len(results), target_size)``.
    """
    padded = list(results)
    while len(padded) < target_size:
        # 16 random bytes → 32-hex-char dummy ID (never in the document store)
        padded.append(os.urandom(16).hex())
    return padded


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
    info(f"Running in MODE = '{MODE}'")
    if MODE == 'before':
        info("BEFORE: Full leakage is visible — exact result counts, repeated")
        info("        trapdoors, and access patterns are all observable by the server.")
    else:
        info("AFTER:  Volume-leakage mitigation active — result sets are padded to")
        info(f"        {PADDED_RESULT_SIZE} entries so the server cannot infer the true match count.")
    info("")
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
    if MODE == 'after':
        info(f"[AFTER] Result sets will be padded to {PADDED_RESULT_SIZE} entries "
             f"(volume-leakage mitigation).")
    else:
        info("[BEFORE] Result sets reflect real match counts — volume leakage is visible.")
    info("")

    analyzer = LeakageAnalyzer()

    for query_keyword in QUERIES:
        trapdoor = generate_trapdoor(key, query_keyword)
        results = search(encrypted_index, trapdoor)

        # --- Volume-leakage mitigation (MODE == 'after') -------------------
        # Pad the result set sent to the leakage analyzer so the server always
        # observes PADDED_RESULT_SIZE entries, hiding the real match count.
        if MODE == 'after':
            server_visible_results = pad_results(results, PADDED_RESULT_SIZE)
        else:
            server_visible_results = results

        # Log the query so the leakage analyzer can inspect it
        analyzer.log_query(trapdoor, server_visible_results)

        # Decrypt results (client-side); dummy padding IDs are silently skipped
        decrypted = decrypt_results(key, results, document_store)

        info(f"  Query: '{query_keyword}'")
        info(f"    Trapdoor: {trapdoor[:24]}...")
        if MODE == 'after':
            info(f"    Real matching docs: {len(results)}  |  "
                 f"Server-visible result count: {len(server_visible_results)} "
                 f"(padded, hides true count)")
        else:
            info(f"    Matching docs: {len(results)}  [server sees exact count — volume leakage]")
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
        # Highlight the mitigation that is active in 'after' mode
        active_tag = " ← ACTIVE in MODE='after'" if (
            MODE == 'after' and name == "Result Padding"
        ) else ""
        info(f"  [{name}]{active_tag}")
        info(f"    {desc}")
        info("")

    banner("END OF DEMONSTRATION")
    info("This project is for educational purposes only.")
    info("See README.md for references and further reading.")
    print()


if __name__ == "__main__":
    main()
