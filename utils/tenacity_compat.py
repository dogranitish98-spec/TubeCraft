"""Tiny retry compatibility layer for incomplete/offline installations.

If the real `tenacity` package exists, it is used unchanged. Otherwise the two
retry forms used by TubeCraft are implemented locally with bounded attempts.
"""
from __future__ import annotations

import functools
import time

try:
    from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
except Exception:  # pragma: no cover
    class RetryError(Exception):
        pass

    def stop_after_attempt(attempts: int):
        return max(1, int(attempts))

    def wait_fixed(seconds: float):
        return max(0.0, float(seconds))

    def retry(*, stop=3, wait=0, **_kwargs):
        attempts = int(stop) if isinstance(stop, int) else 3
        delay = float(wait) if isinstance(wait, (int, float)) else 0.0

        def decorator(fn):
            if hasattr(fn, "__call__"):
                @functools.wraps(fn)
                def wrapped(*args, **kwargs):
                    last = None
                    for attempt in range(attempts):
                        try:
                            return fn(*args, **kwargs)
                        except Exception as exc:
                            last = exc
                            if attempt + 1 < attempts and delay:
                                time.sleep(delay)
                    raise RetryError(last)
                return wrapped
            return fn
        return decorator
