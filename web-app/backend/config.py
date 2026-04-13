"""
config.py - Configuration settings for the Flask backend.
"""

import os
import warnings

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

_default_key = "dev-secret-key-change-in-production"
SECRET_KEY = os.environ.get("SECRET_KEY", _default_key)

if not DEBUG and SECRET_KEY == _default_key:
    warnings.warn(
        "SECRET_KEY is set to the insecure default value in a non-debug environment. "
        "Set the SECRET_KEY environment variable to a strong random secret before deploying.",
        stacklevel=2,
    )
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5000))

# CORS – allow the React dev server
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:3000")

# SSE – volume-leakage mitigation padding
PADDED_RESULT_SIZE = 5

# Background keyword frequency distribution (domain knowledge used by the
# frequency-analysis adversary, drawn from a cybersecurity query log).
KNOWN_KEYWORD_FREQUENCIES = {
    "encryption":    0.09,
    "malware":       0.08,
    "security":      0.07,
    "data":          0.07,
    "network":       0.06,
    "ransomware":    0.06,
    "attack":        0.05,
    "firewall":      0.05,
    "phishing":      0.04,
    "vulnerability": 0.03,
}

# Pre-loaded sample document corpus
SAMPLE_DOCUMENTS = [
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
