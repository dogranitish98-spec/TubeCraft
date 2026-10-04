# TubeCraft Studio — Aggressive Hardening Pass

## Implemented

- Added a deterministic local media self-test that creates a real MP4 with FFmpeg and validates it with FFprobe.
- Added `GET /api/self-test` for local readiness and media verification.
- Added `POST /api/self-test/live` to submit a real minimal Agnes generation job when an API key is configured.
- Added `GET /api/self-test/live/{task_id}` to poll the real job and validate the resulting MP4 with FFprobe.
- Added a professional in-app Self-test & diagnostics panel with a separate real-generation action.
- Added actionable 412 response when live generation cannot run because `AGNES_API_KEY` is missing.
- Improved `/api/health` to report core readiness versus full readiness and expose TTS dependency state.
- Added provider configuration visibility without exposing the key itself.
- Added offline compatibility shims for `edge-tts`, `srt`, and local tenacity usage so incomplete/offline dependency environments fail gracefully instead of crashing the entire app at import time.
- Changed the `core` package to lazy-load public exports so lightweight diagnostics do not import every media subsystem.
- Added deterministic startup smoke-test gates to `start.sh` and `start.bat`.
- Hardened the service worker to cache the TubeCraft shell assets required by offline startup, including the self-test UI.
- Kept API/media responses out of the service-worker cache.
- Synchronized runtime PWA assets between `static/` and `frontend/public/` so a future frontend build does not regress the shipped PWA.
- Added regression tests for self-test endpoints, real MP4 validation, readiness semantics, live-test precondition handling, and PWA shell caching.

## Verification performed here

- Python compile check: PASS
- JavaScript syntax check: PASS (`professional-shell.js`, `pwa-runtime.js`, `self-test-ui.js`)
- Manifest JSON validation: PASS
- FastAPI import: PASS (77 routes loaded)
- `/api/health`: PASS (200)
- `/api/self-test`: PASS (200)
- Deterministic FFmpeg MP4 generation: PASS
- FFprobe validation: PASS (H.264, 640x360, 2.0s)
- PWA + access-control + self-test regression suite: **30 passed** with `PYTHONPATH=.`

## Live AI generation status

A real Agnes generation still requires a valid `AGNES_API_KEY` and network access to the configured provider. The project now has a real live test path that reports this as a concrete precondition instead of pretending an AI video was generated.

## Frontend production build

A full Vite/Vue production rebuild was not performed in this environment because the uploaded project has no installed frontend dependency tree and external package installation is unavailable here. The existing compiled frontend remains intact, while source and public assets were updated in parallel.
