"""
utils/invite.py
---------------
Invite-code generation lives here so the generation strategy can be
swapped (e.g. UUID-based, ULID, random alphanumeric) without touching
the service layer.
"""

import secrets
import string


_ALPHABET = string.ascii_uppercase + string.digits  # e.g. "A3K9MZ"
_CODE_LENGTH = 8


def generate_invite_code() -> str:
    """
    Return a cryptographically random, URL-safe invite code.
    8 characters from [A-Z0-9] → ~1.8 × 10¹² combinations.
    """
    return "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))
