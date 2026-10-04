"""Optional single-user access control for PWA/LAN deployments.

When ``TUBECRAFT_ACCESS_TOKEN`` is configured, mutating API requests require
that token in ``X-TubeCraft-Access-Token`` or ``Authorization: Bearer ...``.
GET media remains readable so native <video>/<img> elements keep working.
"""
from __future__ import annotations

import hmac
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

PUBLIC_MUTATION_PATHS = {
    "/api/auth/status",
}

PROTECTED_READ_PATHS = {
    "/api/metrics",
    "/api/config",
    "/api/config/keys",
    "/api/config/text-providers",
    "/api/workspaces",
    "/api/concurrency",
}


def get_access_token() -> str:
    # Fast path: avoid importing the full application/config graph for the
    # lightweight auth-status and middleware checks. This also keeps minimal
    # security tests runnable when optional media dependencies are absent.
    env_value = os.environ.get("TUBECRAFT_ACCESS_TOKEN", "")
    if env_value.strip():
        return env_value.strip()
    try:
        from core.config import get_settings
        return (getattr(get_settings(), "tubecraft_access_token", "") or "").strip()
    except Exception:
        return ""


def is_protected_mutation(request: Request) -> bool:
    path = request.url.path
    return (
        path.startswith("/api/")
        and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and path not in PUBLIC_MUTATION_PATHS
    )


def is_protected_read(request: Request) -> bool:
    if request.method != "GET":
        return False
    path = request.url.path
    if path in PROTECTED_READ_PATHS:
        return True
    # Task metadata can contain prompts, paths, provider errors, checkpoints,
    # and other user/project details. Keep it behind the optional LAN token.
    # Direct media/file endpoints remain readable so <video>/<img>/<a> work.
    if path == "/api/self-test" or path.startswith("/api/self-test/live/"):
        return True
    if path == "/api/tasks" or (path.startswith("/api/tasks/") and not path.endswith("/file") and "/cascade-preview" not in path):
        return True
    # Gallery metadata is private; thumbnail/media delivery stays public.
    if path == "/api/gallery":
        return True
    return False


def extract_access_token(request: Request) -> str:
    token = request.headers.get("x-tubecraft-access-token", "").strip()
    if token:
        return token
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def require_access_token(request: Request) -> Optional[Response]:
    expected = get_access_token()
    if not expected or (not is_protected_mutation(request) and not is_protected_read(request)):
        return None
    supplied = extract_access_token(request)
    if supplied and hmac.compare_digest(supplied, expected):
        return None
    return JSONResponse(
        {"ok": False, "error": "access_token_required"},
        status_code=401,
        headers={"Cache-Control": "no-store", "WWW-Authenticate": "Bearer"},
    )


class TubeCraftAccessControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        blocked = require_access_token(request)
        if blocked is not None:
            return blocked
        return await call_next(request)
