"""
encryption.py - Core cryptographic primitives for the SSE demonstration.

Provides:
  - AES-256-CBC symmetric encryption / decryption
  - Deterministic HMAC-SHA256 encryption (used to build encrypted index tokens)
  - Trapdoor generation (simulates the SSE client-side trapdoor)
"""

import os
import hmac
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# AES block size in bytes
BLOCK_SIZE = AES.block_size  # 16 bytes


def generate_key() -> bytes:
    """Generate a random 256-bit (32-byte) AES secret key."""
    return os.urandom(32)


def encrypt(key: bytes, plaintext: str) -> bytes:
    """
    Encrypt *plaintext* using AES-256-CBC with a random IV.

    The returned ciphertext is: IV (16 bytes) || encrypted bytes.
    The IV is prepended so that decrypt() can recover it.

    Args:
        key: 32-byte AES secret key.
        plaintext: UTF-8 string to encrypt.

    Returns:
        bytes: IV prepended to the ciphertext.
    """
    iv = os.urandom(BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext.encode("utf-8"), BLOCK_SIZE)
    ciphertext = cipher.encrypt(padded)
    return iv + ciphertext


def decrypt(key: bytes, ciphertext: bytes) -> str:
    """
    Decrypt a ciphertext produced by encrypt().

    Extracts the IV from the first 16 bytes, then decrypts the remainder.

    Args:
        key: 32-byte AES secret key (must match the one used for encryption).
        ciphertext: bytes produced by encrypt() — IV || encrypted bytes.

    Returns:
        str: The original plaintext.
    """
    iv = ciphertext[:BLOCK_SIZE]
    encrypted_data = ciphertext[BLOCK_SIZE:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = cipher.decrypt(encrypted_data)
    return unpad(padded_plaintext, BLOCK_SIZE).decode("utf-8")


def deterministic_encrypt(key: bytes, keyword: str) -> str:
    """
    Produce a **deterministic** token for *keyword* using HMAC-SHA256.

    Unlike encrypt(), this always returns the same token for the same
    (key, keyword) pair.  This is intentional: it is what allows the
    server to compare a search trapdoor against index tokens without
    learning the keyword.  It is also the root cause of *search pattern*
    and *frequency leakage* — an adversarial server that sees the same
    token twice knows the same keyword was searched again.

    Args:
        key: 32-byte secret key.
        keyword: The plaintext keyword to tokenise.

    Returns:
        str: Hex-encoded HMAC-SHA256 digest.
    """
    mac = hmac.new(key, keyword.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def generate_trapdoor(key: bytes, keyword: str) -> str:
    """
    Generate a search trapdoor for *keyword*.

    In a real SSE scheme the client sends a trapdoor (derived from the
    secret key and the desired keyword) to the server so the server can
    locate matching index entries without learning the keyword itself.
    Here the trapdoor is identical to the deterministic token — this is
    the simplest (and most leaky) construction.

    Args:
        key: 32-byte secret key shared with the server.
        keyword: The keyword the client wants to search for.

    Returns:
        str: Hex-encoded trapdoor token.
    """
    return deterministic_encrypt(key, keyword)
