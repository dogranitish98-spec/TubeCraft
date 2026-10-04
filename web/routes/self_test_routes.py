"""TubeCraft self-test endpoints.

Two paths are deliberately separated:
- local: no API quota, proves FFmpeg/media path and basic runtime health;
- live: creates a real tiny Agnes generation task when a provider key exists.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse

from core.config import (
    DURATION_FRAME_MAP,
    VIDEO_25_DURATIONS,
    get_api_key,
    get_selected_models,
    get_working_dir,
    is_v25_video_model,
)
from core.self_test import self_test_workspace
from core.task_manager import TaskManager
from web import helpers

router = APIRouter(tags=["self-test"])

LIVE_PROMPT = (
    "A cinematic lighthouse on a rocky ocean coast at sunset, realistic moving water, "
    "warm golden light, slow camera push toward the lighthouse, photorealistic, no text."
)


def _valid_live_duration() -> int:
    model = get_selected_models().get("video") or ""
    choices = VIDEO_25_DURATIONS if is_v25_video_model(model) else list(DURATION_FRAME_MAP.keys())
    return min(choices)


@router.get("/api/self-test")
async def self_test() -> dict:
    result = self_test_workspace(os.getcwd())
    result["provider"] = {
        "api_key_configured": bool(get_api_key()),
        "live_capable": bool(get_api_key()),
    }
    return result


@router.post("/api/self-test/live")
async def start_live_self_test() -> dict:
    api_key = get_api_key()
    if not api_key:
        return JSONResponse(
            {
                "ok": False,
                "stage": "provider_auth",
                "error_code": "AGNES_API_KEY_MISSING",
                "message": "Configure an Agnes API key before running the live generation test.",
                "live_capable": False,
            },
            status_code=412,
            headers={"Cache-Control": "no-store"},
        )

    # Reuse the production route implementation so the self-test cannot diverge
    # from the actual user generation path.
    from web.routes.task_creation_routes import create_simple_task

    duration = _valid_live_duration()
    result = await create_simple_task(
        prompt=LIVE_PROMPT,
        mode="t2v",
        duration=duration,
        video_width=1280,
        video_height=720,
        seed=17,
        negative_prompt="text, watermark, distortion, low quality",
        system_prompt="",
        reference_image=None,
        end_frame_image=None,
        video_size="720P",
    )
    return {
        "ok": True,
        "stage": "queued",
        "task_id": result["task_id"],
        "dir_name": result["dir_name"],
        "duration": duration,
        "prompt": LIVE_PROMPT,
    }


@router.get("/api/self-test/live/{task_id}")
async def live_self_test_status(task_id: str) -> dict:
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Self-test task not found")
    result = {
        "ok": True,
        "task_id": task_id,
        "status": state.status,
        "current_step": state.current_step,
        "current_progress": state.current_progress,
        "current_message": state.current_message,
        "final_video_file": state.final_video_file,
        "error_traceback": (state.error_traceback or "")[-5000:],
        "active": False,
    }
    if state.final_video_file:
        path = Path(state.final_video_file)
        if not path.is_absolute():
            path = Path(get_working_dir()) / dir_name / path
        result["final_video_exists"] = path.is_file()
        if path.is_file():
            from core.self_test import probe_video
            result["media_probe"] = probe_video(str(path))
    return result
