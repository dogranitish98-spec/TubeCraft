"""Optional edge-tts compatibility shim.

The production package still declares edge-tts as a dependency. This module only
prevents the whole application/test suite from crashing at import time when an
installation is incomplete or offline. Real TTS remains unavailable until
edge-tts is installed; callers receive an actionable RuntimeError instead.
"""
from __future__ import annotations

import importlib


try:
    edge_tts = importlib.import_module("edge_tts")
    AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    AVAILABLE = False

    class _MissingCommunicate:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "edge-tts is not installed. Install dependencies with "
                "'pip install -r requirements.txt' to enable online TTS."
            )

    class _FallbackSubMaker:
        def __init__(self):
            self.cues = []

        def feed(self, chunk):
            return None

    class _MissingEdgeTTS:
        Communicate = _MissingCommunicate
        SubMaker = _FallbackSubMaker

        async def list_voices(self):
            raise RuntimeError(
                "edge-tts is not installed. The app will use its offline voice catalog."
            )

    edge_tts = _MissingEdgeTTS()
