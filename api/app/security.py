import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session_token")
SESSION_MAX_AGE_SECONDS = int(os.getenv("SESSION_MAX_AGE_SECONDS", "86400"))
JWT_SECRET = os.getenv("JWT_SECRET", "replace_me")
JWT_ALGORITHM = "HS256"

PBKDF2_ITERATIONS = 100_000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, iterations_str, salt_b64, digest_b64 = hashed_password.split("$", 3)
        if scheme != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
    except Exception:  # noqa: BLE001
        return False

    candidate = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, plain_password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def create_session_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=SESSION_MAX_AGE_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
