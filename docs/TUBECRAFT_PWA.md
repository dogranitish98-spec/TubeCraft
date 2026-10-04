# TubeCraft Studio PWA

TubeCraft Studio is the user-facing PWA shell around the existing Agnes video-generation engine.

## Local run

1. Python 3.10+ and FFmpeg are required by the manual backend path.
2. Configure the existing Agnes API key through the app or environment.
3. Run `./start.sh` (or Docker/npm using the repository's existing launchers).
4. Open `http://localhost:8765` in Chrome/Edge on desktop or Android.
5. Use the in-app **Install TubeCraft** action when the browser exposes it. On iOS Safari, use **Share → Add to Home Screen**.

## PWA behavior

- Installable standalone web app
- Android/Chrome install prompt
- iOS Add-to-Home-Screen guidance
- Offline app-shell fallback
- Versioned service-worker cache with update action
- API, uploads, and generated media are never cached
- Same-origin runtime assets are cached safely
- Existing Agnes task polling remains authoritative
- Existing video generation backend remains unchanged

## Architecture

`TubeCraft PWA → existing Agnes FastAPI routes → existing generation pipelines → FFmpeg/output artifacts`

The browser does not run Python or FFmpeg. The PWA is the single user-facing application; Agnes remains the backend generation engine.
