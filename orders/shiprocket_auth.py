"""
Robust Shiprocket auth:
- Logs in with API User email/password (apiv2)
- Caches JWT for ~55 minutes
- Ensures a valid JWT when building headers (auto refresh if invalid)
- Accepts either SHIPROCKET_API_EMAIL/PASSWORD or legacy SHIPROCKET_EMAIL/PASSWORD
"""

import os
import time
import requests
from django.conf import settings

SR_LOGIN_URL = "https://apiv2.shiprocket.in/v1/external/auth/login"

_token_cache = {"token": None, "exp": 0}  # epoch seconds


def _is_valid_jwt(token: str) -> bool:
    return isinstance(token, str) and token.count(".") == 2 and len(token) > 40


def _creds():
    # Preferred env names
    email = getattr(settings, "SHIPROCKET_API_EMAIL", None) or os.getenv("SHIPROCKET_API_EMAIL")
    password = getattr(settings, "SHIPROCKET_API_PASSWORD", None) or os.getenv("SHIPROCKET_API_PASSWORD")

    # Fallback to legacy names if present
    if not email:
        email = getattr(settings, "SHIPROCKET_EMAIL", None) or os.getenv("SHIPROCKET_EMAIL")
    if not password:
        password = getattr(settings, "SHIPROCKET_PASSWORD", None) or os.getenv("SHIPROCKET_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "Missing Shiprocket credentials. Set SHIPROCKET_API_EMAIL/SHIPROCKET_API_PASSWORD "
            "(or legacy SHIPROCKET_EMAIL/SHIPROCKET_PASSWORD) in settings/.env."
        )
    return email, password


def _login_for_token() -> str:
    email, password = _creds()
    print(f"[Shiprocket] Logging in via: {SR_LOGIN_URL}")
    r = requests.post(
        SR_LOGIN_URL,
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Shiprocket login failed ({r.status_code}): {r.text[:400]}")

    data = r.json()
    token = data.get("token")
    if not _is_valid_jwt(token):
        raise RuntimeError(f"Shiprocket login returned invalid token: {data}")

    _token_cache["token"] = token
    _token_cache["exp"] = int(time.time()) + 55 * 60
    print(f"[Shiprocket] Token acquired (length={len(token)})")
    return token


def get_shiprocket_token() -> str:
    # Optional permanent JWT
    static = getattr(settings, "SHIPROCKET_API_TOKEN", None) or os.getenv("SHIPROCKET_API_TOKEN", None)
    if static:
        if not _is_valid_jwt(static):
            raise RuntimeError("SHIPROCKET_API_TOKEN looks invalid (not a JWT). Remove it or fix it.")
        return static

    now = int(time.time())
    tok = _token_cache["token"]
    if not _is_valid_jwt(tok) or now >= _token_cache["exp"]:
        return _login_for_token()
    return tok


def refresh_shiprocket_token() -> str:
    _token_cache["token"] = None
    _token_cache["exp"] = 0
    return _login_for_token()


def auth_headers() -> dict:
    token = get_shiprocket_token()
    if not _is_valid_jwt(token):
        print("[Shiprocket] Token looked invalid when building headers; refreshing…")
        token = refresh_shiprocket_token()

    # Safe peek prefix for debugging
    prefix = token.split(".", 1)[0] if token and "." in token else "?"
    print(f"[Shiprocket] Using JWT prefix '{prefix[:6]}…' in Authorization header")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
