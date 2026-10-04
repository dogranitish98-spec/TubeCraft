# TubeCraft PWA Gap-Fix Report

## Fixed in this revision

1. **Installed-PWA navigation** — progress pages no longer open popup/new tabs on compact screens or standalone display mode.
2. **iOS installation guidance** — Safari users now get an Add to Home Screen instruction instead of waiting for the unsupported `beforeinstallprompt` event.
3. **PWA update lifecycle** — the app detects a waiting service worker and exposes an explicit update action.
4. **Service-worker cache hygiene** — API endpoints, uploads, and generated/audio/video media are never cached; old caches are removed by version.
5. **Offline resilience** — navigation falls back to the cached app shell/offline page; runtime assets use same-origin caching only.
6. **Security headers** — baseline MIME-sniffing, framing, referrer, and permissions headers are added without breaking the existing inline theme bootstrap.
7. **Config privacy** — `/api/config` is explicitly `no-store` because it contains mutable configuration and a masked API-key prefix.
8. **Source/build consistency** — PWA assets live in `frontend/public`; the build script now installs dependencies, builds the source of truth, and verifies the resulting artifacts.
9. **Language metadata** — the HTML document now advertises English by default, matching the app's fallback language.

## Remaining architectural gaps

- Agnes is still the generation engine; TubeCraft does not yet have a separate provider adapter/registry abstraction.
- Long-form continuity/checkpoint orchestration is largely provided by Agnes task pipelines rather than a TubeCraft-owned project model.
- There is no browser-only FFmpeg pipeline; final composition remains server-side, which is intentional for Android/PWA reliability.
- Full production build/test execution requires installing the project's Python and Node dependencies on a connected development machine.


## Aggressive hardening pass
- Added bounded transient retry budget for provider 5xx/network failures, independent of the normal retry-attempt cap. Default: 900 seconds; set `AGNES_VIDEO_TRANSIENT_RETRY_SECONDS=0` for legacy behavior.
- Protected `/api/metrics` when `TUBECRAFT_ACCESS_TOKEN` is configured.
- Made PWA static assets network-first with cached fallback so new hashed bundles are not pinned indefinitely by an unchanged service-worker version.
- Added actionable `/api/health` readiness/dependency checks (workspace, FFmpeg, API-key presence, upload policy) without making external provider calls.
- Authentication status responses are explicitly `no-store`.
- Kept API/media responses outside the service-worker cache.
