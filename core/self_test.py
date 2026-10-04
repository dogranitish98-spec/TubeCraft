"""Deterministic local/self-hosted health and media verification helpers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any


def resolve_ffprobe() -> str | None:
    return shutil.which("ffprobe")


def resolve_ffmpeg() -> str | None:
    try:
        from core.compositor.ffmpeg_tool import resolve_binary
        return resolve_binary("ffmpeg")
    except Exception:
        return shutil.which("ffmpeg")


def probe_video(path: str) -> dict[str, Any]:
    ffprobe = resolve_ffprobe()
    if not ffprobe:
        return {"ok": False, "error": "ffprobe is not available"}
    if not os.path.isfile(path):
        return {"ok": False, "error": "video file does not exist"}
    cmd = [
        ffprobe, "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or "ffprobe failed")[-1200:]}
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "ffprobe returned invalid JSON"}
    streams = data.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    duration_raw = (data.get("format") or {}).get("duration")
    try:
        duration = float(duration_raw or 0)
    except (ValueError, TypeError):
        duration = 0.0
    ok = bool(video and duration > 0 and video.get("width") and video.get("height"))
    return {
        "ok": ok,
        "duration_seconds": round(duration, 3),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "codec": video.get("codec_name") if video else None,
        "format": (data.get("format") or {}).get("format_name"),
        "size_bytes": os.path.getsize(path),
        "error": "" if ok else "invalid or empty video stream",
    }


def create_synthetic_video(output_path: str, duration: int = 2) -> dict[str, Any]:
    """Generate a real, playable local MP4 without any AI/API dependency."""
    ffmpeg = resolve_ffmpeg()
    if not ffmpeg:
        return {"ok": False, "stage": "ffmpeg", "error": "ffmpeg is not available"}
    duration = max(1, min(int(duration), 5))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp.mp4")
    if tmp.exists():
        tmp.unlink()
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=24",
        "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000",
        "-t", str(duration), "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-movflags", "+faststart", str(tmp),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return {"ok": False, "stage": "ffmpeg", "error": str(exc)}
    if proc.returncode != 0 or not tmp.exists():
        return {"ok": False, "stage": "ffmpeg", "error": (proc.stderr or "ffmpeg failed")[-1600:]}
    os.replace(tmp, output)
    probe = probe_video(str(output))
    probe.update({"ok": bool(probe.get("ok")), "stage": "media_validation", "path": str(output)})
    return probe


def self_test_workspace(base_dir: str) -> dict[str, Any]:
    work = Path(base_dir) / ".tubecraft_self_test"
    work.mkdir(parents=True, exist_ok=True)
    output = work / f"synthetic_{uuid.uuid4().hex[:10]}.mp4"
    synthetic = create_synthetic_video(str(output), duration=2)
    return {
        "ok": bool(synthetic.get("ok")),
        "workspace": str(work),
        "checks": {
            "workspace": work.is_dir(),
            "ffmpeg": bool(resolve_ffmpeg()),
            "ffprobe": bool(resolve_ffprobe()),
            "synthetic_mp4": synthetic,
        },
    }
