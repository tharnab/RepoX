"""AES-256-GCM encryption/decryption for GitHub tokens."""

import os

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore[import]
except ImportError as exc:
    raise ImportError(
        "Required dependency 'cryptography' is missing. Install it with: pip install cryptography"
    ) from exc

from app.config import ENCRYPTION_KEY


def _get_key() -> bytes:
    """
    Convert the hex encryption key from .env into bytes.
    Example: "a1b2c3..." (64 hex chars) → 32 bytes
    """
    key = bytes.fromhex(ENCRYPTION_KEY)

    if len(key) != 32:
        raise ValueError(
            f"ENCRYPTION_KEY must be 32 bytes (64 hex characters). "
            f"Got {len(key)} bytes. Regenerate with: "
            f"python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    return key


def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a GitHub token.
    Takes plaintext → returns hex-encoded ciphertext.
    
    Uses AES-256-GCM which provides both:
    - Confidentiality (can't read without key)
    - Integrity (can detect if someone tampered with it)
    """
    key = _get_key()
    aesgcm = AESGCM(key)

    # Generate a random 12-byte nonce (number used once)
    # This ensures the same token encrypted twice gives different output
    nonce = os.urandom(12)

    # Encrypt (no additional authenticated data needed)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # Store nonce + ciphertext together, encoded as hex
    combined = nonce + ciphertext
    return combined.hex()


def decrypt_token(hex_ciphertext: str) -> str:
    """
    Decrypt a GitHub token.
    Takes hex-encoded ciphertext → returns original plaintext.
    """
    key = _get_key()
    aesgcm = AESGCM(key)

    # Convert hex back to bytes
    combined = bytes.fromhex(hex_ciphertext)

    # First 12 bytes = nonce, rest = encrypted data
    nonce = combined[:12]
    ciphertext = combined[12:]

    # Decrypt
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return plaintext.decode("utf-8")