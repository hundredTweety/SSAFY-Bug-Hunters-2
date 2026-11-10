"""Anonymous portfolio practice progress kept in a separate signed browser cookie.

This cookie is NEVER used for authentication or real raid accounting. Django's
database-backed sessions remain exclusively responsible for admin login.
Signed values can be replayed by the holder: harmless for local practice.
"""
from django.conf import settings
from django.core import signing

COOKIE_NAME = "bughunters_demo"
COOKIE_SALT = "raid.portfolio-demo.v1"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30
COOKIE_MAX_LENGTH = 4096
MAX_MISSIONS = 32
MAX_ATTEMPTS = 9999


def _valid_ids(values):
    if not isinstance(values, list):
        return []
    return sorted({value for value in values
                   if type(value) is int and 0 < value <= 100000})[:MAX_MISSIONS]


def demo_state(request):
    """Cache normalized state for one request; never access request.session."""
    if hasattr(request, "_demo_progress"):
        return request._demo_progress

    raw = request.COOKIES.get(COOKIE_NAME, "")
    try:
        data = signing.loads(raw, salt=COOKIE_SALT, max_age=COOKIE_MAX_AGE) if (
            raw and len(raw) <= COOKIE_MAX_LENGTH) else {}
    except (signing.BadSignature, TypeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}

    cleared = _valid_ids(data.get("c"))
    verified = [pk for pk in _valid_ids(data.get("v")) if pk not in cleared]
    source_attempts = data.get("a", {})
    attempts = {}
    if isinstance(source_attempts, dict):
        for key, value in source_attempts.items():
            if (isinstance(key, str) and key.isdigit() and
                    0 < int(key) <= 100000 and type(value) is int and 0 <= value <= MAX_ATTEMPTS):
                attempts[key] = value
                if len(attempts) >= MAX_MISSIONS:
                    break

    request._demo_progress = {"c": cleared, "v": verified, "a": attempts}
    return request._demo_progress


def save_demo_state(response, request):
    """Return response with a signed practice cookie, not a DB session update."""
    value = signing.dumps(demo_state(request), salt=COOKIE_SALT, compress=True)
    response.set_cookie(
        COOKIE_NAME, value, max_age=COOKIE_MAX_AGE, path="/",
        secure=not settings.DEBUG, httponly=True, samesite="Lax",
    )
    return response


def clear_demo_state(response):
    response.delete_cookie(COOKIE_NAME, path="/", samesite="Lax")
    return response
