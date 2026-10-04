"""Small SRT compatibility layer used only when the optional `srt` package is absent.

The official `srt` package remains the preferred implementation. This fallback covers
the simple Subtitle/parse/compose operations TubeCraft uses for local rendering and
keeps startup/diagnostics from collapsing because one optional wheel is unavailable.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass

try:
    import srt as _srt
    AVAILABLE = True
    srt = _srt
except Exception:  # pragma: no cover
    AVAILABLE = False

    @dataclass
    class Subtitle:
        index: int
        start: _dt.timedelta
        end: _dt.timedelta
        content: str

    _TIMECODE = re.compile(
        r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})"
    )

    def _parse_time(value: str) -> _dt.timedelta:
        m = _TIMECODE.fullmatch(value.strip())
        if not m:
            raise ValueError(f"Invalid SRT timestamp: {value!r}")
        return _dt.timedelta(
            hours=int(m.group("h")), minutes=int(m.group("m")),
            seconds=int(m.group("s")), milliseconds=int(m.group("ms"))
        )

    def _format_time(value: _dt.timedelta) -> str:
        total_ms = max(0, int(round(value.total_seconds() * 1000)))
        hours, rem = divmod(total_ms, 3_600_000)
        minutes, rem = divmod(rem, 60_000)
        seconds, ms = divmod(rem, 1_000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    def parse(content_or_file):
        text = content_or_file.read() if hasattr(content_or_file, "read") else str(content_or_file)
        blocks = re.split(r"\n\s*\n", text.strip()) if text.strip() else []
        out = []
        for fallback_index, block in enumerate(blocks, start=1):
            lines = [ln.rstrip("\r") for ln in block.splitlines()]
            if len(lines) < 3:
                continue
            try:
                index = int(lines[0].strip())
                timing = lines[1].split(" --> ", 1)
                start = _parse_time(timing[0]); end = _parse_time(timing[1])
                content = "\n".join(lines[2:])
            except Exception:
                index = fallback_index
                timing = lines[0].split(" --> ", 1)
                if len(timing) != 2:
                    continue
                start = _parse_time(timing[0]); end = _parse_time(timing[1])
                content = "\n".join(lines[1:])
            out.append(Subtitle(index=index, start=start, end=end, content=content))
        return out

    def compose(subtitles):
        parts = []
        for idx, sub in enumerate(subtitles, start=1):
            number = getattr(sub, "index", None) or idx
            parts.append(
                f"{number}\n{_format_time(sub.start)} --> {_format_time(sub.end)}\n{sub.content.strip()}"
            )
        return "\n\n".join(parts) + ("\n\n" if parts else "")

    class _FallbackSrtModule:
        Subtitle = Subtitle
        parse = staticmethod(parse)
        compose = staticmethod(compose)

    srt = _FallbackSrtModule()
