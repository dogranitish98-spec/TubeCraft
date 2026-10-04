# TubeCraft Studio + Agnes — Aggressive Gap Audit

Date: 2026-10-04

## What this pass targeted

This pass was intentionally broader than the initial PWA conversion. It looked at PWA update correctness, LAN security, upload memory behavior, dependency consistency, upstream Agnes failure modes, health/readiness reporting, task metadata exposure, and the current Agnes GitHub issue pattern.

## High-impact fixes applied

### 1. Transient Agnes video failures no longer burn through the small attempt counter immediately
`core/api/agnes_video.py` now has a bounded wall-clock retry track for transient provider 5xx/network failures, independent from the legacy `max_retries` attempt quota. Default budget: 900 seconds. Set `AGNES_VIDEO_TRANSIENT_RETRY_SECONDS=0` to restore legacy behavior.

This specifically addresses the current Agnes reference/keyframe-fallback 503 failure pattern while keeping an explicit upper bound.

### 2. HTTP 401 is now treated as an authentication/configuration problem
When multiple Agnes keys are configured, a submit-side 401 rotates to the next key. With a single key, the failure now explicitly tells the user to verify the API key and selected Agnes API domain instead of surfacing a generic server error.

### 3. Retry state is visible to the pipeline/frontend
A structured `progress.video.server_retry` status is emitted for transient provider retries, so the user can see that the task is still actively recovering rather than appearing frozen.

### 4. Uploads are streamed to disk
Reference/artifact uploads now use `save_upload_limited()` and an atomic temp-file replace instead of reading the entire upload into Python memory first. The configured upload limit still returns HTTP 413 when exceeded.

### 5. Sensitive metadata is protected when the optional TubeCraft access token is enabled
The token now gates:
- `/api/config`
- `/api/config/keys`
- `/api/config/text-providers`
- `/api/tasks*` metadata/checkpoint/diagnostic endpoints
- `/api/gallery` metadata
- `/api/metrics`
- workspace/concurrency metadata

Direct media/file endpoints remain readable so native video/image elements and downloads continue to work.

### 6. Access-token brute-force protection was added
`/api/auth/check` now throttles invalid token probes to five failures per minute per client address and returns `Retry-After` on HTTP 429.

### 7. Authentication status is explicitly non-cacheable
`/api/auth/status` and `/api/auth/check` return `Cache-Control: no-store` so a browser/PWA cannot reuse stale auth state.

### 8. PWA hashed assets now update correctly
The service worker prefers the network for cacheable hashed JS/CSS assets and uses the cache as the offline fallback. This prevents an unchanged service-worker version from pinning an old bundle indefinitely after a deployment.

### 9. Health endpoint now reports readiness/dependency state
`/api/health` reports FFmpeg availability, workspace presence, API-key configuration presence, upload-policy validity, version, and a `ready/degraded` state without making an external provider call.

### 10. Dependency compatibility was tightened
The project required `moviepy<3`, while the previous unbounded Pillow requirement permitted a version that breaks the installed MoviePy 2.2.x dependency constraint. `requirements.txt` now pins Pillow to `<12`.

## Verification performed

Targeted regression suite:

- 25 hardening/PWA tests passed.
- Python `compileall` passed for the touched backend modules and `server.py`.
- A full application pytest run remains blocked in this environment because the uploaded repository dependency set is incomplete here (`edge_tts` is not installed).
- `pip check` also exposed the pre-existing local environment mismatch: MoviePy 2.2.1 requires Pillow <12 while this runtime currently has Pillow 12.3.0. The repository requirement was corrected accordingly; the environment was not mutated just to manufacture a green dependency check.
- The frontend production build was not claimed as verified because `npm ci` could not complete within the execution environment and no `frontend/node_modules` tree was available.

## Remaining architectural gaps

### A. TubeCraft is still an Agnes-centered application shell, not yet the full provider-neutral TubeCraft engine
The next architectural layer should be:

`TubeCraft Project → Long-form Script Planner → Scene/Continuity Manager → VideoProvider → AgnesPlugin/other providers → Checkpointed Render Queue → FFmpeg → Timeline → Export`

The current hardening makes the existing Agnes application safer and more robust, but it does not claim that the complete provider-neutral long-form editor/orchestrator has been implemented.

### B. Long-form continuity is still not a first-class TubeCraft data model
A production TubeCraft implementation still needs persistent scene state for characters, locations, visual style, prior/final frames, camera intent, narration, subtitle alignment, provider job IDs, and scene checkpoints.

### C. PWA cannot generate while disconnected from the engine
Offline support is intentionally app-shell/offline-state support, not fake generation. New generation still requires a reachable engine/provider.

### D. Access token storage remains browser local storage
This is acceptable for a local/LAN single-user deployment but is weaker than an HttpOnly, Secure, SameSite session model for a public internet deployment. A future remote-hosted deployment should use a real session/auth layer plus CSRF protection.

### E. Current Agnes upstream issues can still fail even with local retries
The application cannot make a provider-side 503 or invalid provider credential magically succeed. The goal of this pass is bounded recovery, better diagnostics, and preserved task state rather than pretending the provider is always available.
