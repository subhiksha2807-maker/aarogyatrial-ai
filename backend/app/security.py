from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

SECRET = os.getenv("AAROGYA_DEMO_SECRET", "aarogya-local-demo-secret-change-me").encode()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, expected = stored.split("$", 1)
    actual = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual, expected)


def create_token(user_id: int) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + 8 * 60 * 60}
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(SECRET, encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def decode_token(token: str) -> int | None:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(SECRET, encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload["exp"] < time.time():
            return None
        return int(payload["sub"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None

