"""Tiny auth-status endpoints used by the TubeCraft PWA bootstrap."""
from __future__ import annotations

import hmac
import time
from collections import defaultdict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from web.access_control import extract_access_token, get_access_token

router = APIRouter(tags=["auth"])

# Small in-process throttle for invalid access-token probes. The token is an
# optional LAN safeguard, so a failed-attempt brake is preferable to leaving
# the check endpoint as a zero-cost brute-force oracle.
_FAILURES: dict[str, list[float]] = defaultdict(list)
_FAILURE_WINDOW_SECONDS = 60.0
_FAILURE_LIMIT = 5

def _client_key(request: Request) -> str:
    return (request.client.host if request.client else "unknown").strip() or "unknown"

def _rate_limited(client: str) -> bool:
    now = time.monotonic()
    recent = [t for t in _FAILURES.get(client, []) if now - t < _FAILURE_WINDOW_SECONDS]
    _FAILURES[client] = recent
    return len(recent) >= _FAILURE_LIMIT

def _record_failure(client: str) -> None:
    now = time.monotonic()
    recent = [t for t in _FAILURES.get(client, []) if now - t < _FAILURE_WINDOW_SECONDS]
    recent.append(now)
    _FAILURES[client] = recent[-_FAILURE_LIMIT:]


@router.get("/api/auth/status")
async def auth_status():
    response = JSONResponse(
        {
            "ok": True,
            "required": bool(get_access_token()),
            "header": "X-TubeCraft-Access-Token",
            "scheme": "Bearer",
        },
        headers={"Cache-Control": "no-store"},
    )
    return response


@router.get("/api/auth/check")
async def auth_check(request: Request):
    expected = get_access_token()
    if not expected:
        return JSONResponse(
            {"ok": True, "required": False},
            headers={"Cache-Control": "no-store"},
        )

    client = _client_key(request)
    if _rate_limited(client):
        return JSONResponse(
            {"ok": False, "error": "rate_limited"},
            status_code=429,
            headers={"Cache-Control": "no-store", "Retry-After": "60"},
        )

    supplied = extract_access_token(request)
    if not supplied or not hmac.compare_digest(supplied, expected):
        _record_failure(client)
        return JSONResponse(
            {"ok": False},
            status_code=401,
            headers={"Cache-Control": "no-store"},
        )

    _FAILURES.pop(client, None)
    return JSONResponse(
        {"ok": True, "required": True},
        headers={"Cache-Control": "no-store"},
    )
