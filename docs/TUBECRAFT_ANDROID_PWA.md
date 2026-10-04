# TubeCraft on Android as a PWA

## Important architecture

TubeCraft is the browser/PWA client. The Agnes Python + FFmpeg service remains the generation engine. Android does not run the Python backend inside the browser.

### Same-machine / local development

On a computer, start Agnes and open `http://localhost:8765` in Chrome. Install from the browser menu.

### Android phone connecting to a computer on the same Wi-Fi

Use the computer's LAN address, for example `https://your-hostname.example` in production. A plain `http://192.168.x.x:8765` origin is not a secure context on most Android browsers, so service-worker installation may be blocked. For a real installable Android PWA, expose the backend through HTTPS.

### Production

Deploy the existing Agnes service behind HTTPS and a reverse proxy. The PWA uses the same origin, so `/api/*`, `/static/*`, `/sw.js`, and `/manifest.webmanifest` remain simple same-origin requests.

## Data safety

The service worker intentionally does not cache `/api/*` or generated video files. Task status and generation results stay authoritative on the Agnes backend.
