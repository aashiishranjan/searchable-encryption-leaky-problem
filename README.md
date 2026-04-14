# Searchable Encryption Leaky Problem

A hands-on Python project that demonstrates the **four classical leakage
types** inherent in Searchable Symmetric Encryption (SSE) schemes, along
with an frequency-analysis attack simulation and a discussion of mitigation
strategies.

---

## Table of Contents
1. [What is Searchable Encryption?](#what-is-searchable-encryption)
2. [The Leaky Problem](#the-leaky-problem)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Installation & Usage](#installation--usage)
6. [Example Output](#example-output)
7. [Mitigation Strategies](#mitigation-strategies)
8. [References](#references)

---

## What is Searchable Encryption?

Searchable Symmetric Encryption (SSE) lets a client:

1. **Encrypt** a collection of documents and upload them to an untrusted
   server.
2. Later **search** for a keyword by sending a short *trapdoor* token to
   the server.
3. The server returns the matching encrypted documents **without ever
   learning the plaintext keyword or document content**.

The basic scheme works like this:

```
Client                                 Server
──────                                 ──────
1. Encrypt documents ──────────────►  Store encrypted documents
2. Build encrypted index ──────────►  Store token → [enc_doc_ids]
3. Generate trapdoor(keyword) ──────► Search index with trapdoor
4.                         ◄────────  Return matching enc_doc_ids
5. Decrypt results
```

The server only sees opaque byte strings — it cannot read documents or
keywords.  However, the **statistical patterns** of queries still leak
information — this is the *Searchable Encryption Leaky Problem*.

---

## The Leaky Problem

Even with strong encryption, a passive (honest-but-curious) server can
observe the following four leakage types:

### 1. Search Pattern Leakage
Because trapdoors are **deterministic** (same keyword → same token), the
server can tell when the *same keyword* is searched more than once.  Over
time it builds a timeline of repeated queries without knowing the keyword.

### 2. Access Pattern Leakage
For each query the server sees *which* encrypted documents are returned.
By observing which documents co-appear across queries, the server can
infer relationships between keywords and documents — even without reading
either.

### 3. Volume (Size) Pattern Leakage
The server counts *how many* documents each query returns.  This reveals
the **document frequency** of the keyword in the corpus.  Common keywords
(e.g., "the") return many results; rare keywords return few.

### 4. Frequency Leakage
Over a query log the server builds a histogram of trapdoor occurrences.
This histogram mirrors the **keyword frequency distribution** of the
client's queries.  An adversary who knows (or can guess) this distribution
can mount a **frequency analysis attack** — mapping trapdoors to likely
keywords purely from statistics.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  CLIENT                                                 │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ encryption  │  │ searchable_index │  │  search   │  │
│  │  (AES-256)  │  │  (build index)   │  │ (decrypt) │  │
│  └──────┬──────┘  └────────┬─────────┘  └─────┬─────┘  │
│         │                  │                   │        │
└─────────┼──────────────────┼───────────────────┼────────┘
          │ encrypted docs   │ encrypted index   │ trapdoor
          ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│  SERVER (untrusted)                                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  document_store          encrypted_index         │   │
│  │  enc_id → enc_content    token → [enc_id, ...]   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  leakage_analyzer        attack_simulation       │   │
│  │  (observes patterns)     (frequency attack)      │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
├── README.md
├── requirements.txt
├── demo.py
├── src/
│   ├── __init__.py
│   ├── encryption.py        # AES-256-CBC + HMAC trapdoor generation
│   ├── searchable_index.py  # Encrypted inverted index builder
│   ├── search.py            # Server-side lookup + client-side decryption
│   ├── leakage_analyzer.py  # Passive leakage monitor (4 types)
│   └── attack_simulation.py # Frequency analysis attack (Islam et al. 2012)
└── tests/
    ├── __init__.py
    └── test_encryption.py   # Unit tests (unittest)
```

---

## Installation & Usage

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the end-to-end demonstration
python demo.py

# 3. Run the unit tests
python -m pytest tests/ -v
# or
python -m unittest discover tests/
```

**Requirements:** Python 3.7+, `pycryptodome`

---

## Example Output

```
======================================================================
  SEARCHABLE ENCRYPTION LEAKY PROBLEM — DEMONSTRATION
======================================================================

--  >> STEP 1: Generate AES-256 Secret Key  --------------------------
  Secret key (hex): a3f8c2...  [32 bytes, kept by client]

--  >> STEP 2: Build Encrypted Searchable Index  ---------------------
  Indexing 10 documents...
  Encrypted index contains 87 keyword tokens.
  Sample encrypted index entries (server's view):
    Token 1: 9f4a2b8c1d...  →  2 doc(s)
    Token 2: 3e7d1f0a9c...  →  1 doc(s)
  OBSERVATION: The server sees only random-looking tokens.

--  >> STEP 4: Leakage Analysis (Server's Perspective)  --------------
[1] SEARCH PATTERN LEAKAGE
    3 trapdoor(s) were repeated:
      Token ...a4f2c8b19d3e  →  queried 3 times
      Token ...7b3c1d0e5f2a  →  queried 2 times  (malware)

[4] FREQUENCY LEAKAGE
    Token ...a4f2c8b19d3e  →    3 queries  ( 30.0%)  ###

--  >> STEP 5: Frequency Analysis Attack Simulation  -----------------
  Adversary guesses 'encryption' from token ...a4f2c8b19d3e  (conf: 92%)
```

---

## Mitigation Strategies

| Strategy | Leakage Addressed | Trade-off |
|---|---|---|
| **ORAM** (Oblivious RAM) | Access pattern | High communication overhead |
| **Result Padding** | Volume pattern | Bandwidth cost |
| **Differential Privacy** | Frequency leakage | Query utility loss |
| **Forward Privacy (OSSE)** | Access pattern (updates) | Requires round trips |
| **Randomised Trapdoors** | Search pattern | Larger index |
| **Secure Multi-Party Computation** | All patterns | Complex infrastructure |

---

## References

1. **Song, Wagner & Perrig (2000)** — *Practical Techniques for Searches on
   Encrypted Data.* IEEE S&P 2000.  The original SSE paper.

2. **Curtmola, Garay, Kamara & Ostrovsky (2006)** — *Searchable Symmetric
   Encryption: Improved Definitions and Efficient Constructions.* ACM CCS 2006.
   Formal SSE security definitions and the first provably secure scheme.

3. **Islam, Kuzu & Kantarcioglu (2012)** — *Access Pattern Disclosure on
   Searchable Encryption: Ramification, Attack and Mitigation.* NDSS 2012.
   The frequency analysis attack simulated in this project.

4. **Cash, Grubbs, Perry & Ristenpart (2015)** — *Leakage-Abuse Attacks
   Against Searchable Encryption.* ACM CCS 2015.  Comprehensive study of
   practical leakage-abuse attacks.
