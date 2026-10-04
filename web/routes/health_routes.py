"""3.2 可观测与运维：/api/health（探活）+ /api/metrics（运行指标）。

- ``GET /api/health``：轻量探活（Docker HEALTHCHECK / compose 健康检查用），
  不带业务语义、不触达任何外部依赖。
- ``GET /api/metrics``：限速器统计、并发信号量利用率、活跃/排队任务分布。
"""
import logging
import os
import shutil

from fastapi import APIRouter

from web import app_state

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/health")
async def health():
    """Actionable readiness probe without making external provider calls."""
    ffmpeg = None
    try:
        from core.compositor.ffmpeg_tool import resolve_binary
        ffmpeg = resolve_binary("ffmpeg")
    except Exception:
        ffmpeg = shutil.which("ffmpeg")

    try:
        from core.config import APP_VERSION, get_settings
        settings = get_settings()
        api_key_configured = bool(os.environ.get("AGNES_API_KEY", "").strip()) or bool(
            getattr(settings, "agnes_api_key", "")
        )
        max_upload_mb = int(getattr(settings, "tubecraft_max_upload_mb", 100))
    except Exception:
        APP_VERSION = "unknown"
        api_key_configured = bool(os.environ.get("AGNES_API_KEY", "").strip())
        max_upload_mb = int(os.environ.get("TUBECRAFT_MAX_UPLOAD_MB", "100"))

    try:
        from core.audio.edge_tts_compat import AVAILABLE as edge_tts_available
    except Exception:
        edge_tts_available = False

    checks = {
        "workspace": os.path.isdir(os.path.join(os.getcwd(), "resource")),
        "ffmpeg": bool(ffmpeg),
        "api_key_configured": api_key_configured,
        "upload_limit_mb": max_upload_mb > 0,
        "tts_dependency": bool(edge_tts_available),
    }
    # API-key absence prevents real AI generation, but must not make the local PWA
    # itself unusable; the UI can surface this explicitly as "provider not configured".
    core_ready = checks["workspace"] and checks["ffmpeg"] and checks["upload_limit_mb"]
    fully_ready = core_ready and checks["tts_dependency"] and checks["api_key_configured"]
    status = "ready" if fully_ready else ("degraded" if core_ready else "unavailable")
    return {
        "ok": True,
        "service": "tubecraft-studio-engine",
        "status": status,
        "ready": core_ready,
        "fully_ready": fully_ready,
        "version": APP_VERSION,
        "checks": checks,
        "ffmpeg": ffmpeg or None,
    }


@router.get("/api/metrics")
async def metrics():
    """运行指标（限速器统计 + 并发利用率 + 活跃任务分布）。"""
    limiter_stats: dict = {}
    video_limiter_stats: dict = {}
    try:
        from core.api.rate_limiter import get_rate_limiter, get_video_submit_limiter
        limiter_stats = get_rate_limiter().stats
        video_limiter_stats = get_video_submit_limiter().stats
    except Exception as e:
        logger.warning(f"[Metrics] limiter stats unavailable: {e}")

    sem = app_state.get_semaphore()
    return {
        "ok": True,
        "rate_limiter": limiter_stats,
        "video_limiter": video_limiter_stats,
        "concurrency": {
            "current_weight": sem.current,
            "max_weight": sem.max_weight,
            "usage_pct": (
                round(sem.current / sem.max_weight * 100, 1)
                if sem.max_weight
                else 0.0
            ),
        },
        "tasks": {
            "active": len(app_state.active_pipelines),
            "queued": len(app_state._queued_tasks),
            "active_ids": sorted(app_state.active_pipelines.keys()),
        },
    }
