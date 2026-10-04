# TubeCraft Studio

Professional installable PWA front-end for AI video production, with Agnes as the persistent generation engine.

**Primary deployment:** GitHub → Vercel (PWA) → persistent Agnes backend.

## Why it is split this way

The PWA can be served globally from Vercel. The Agnes engine owns API credentials, FFmpeg, task state, media workspaces, retries, and video generation. The browser talks to `/api/*`; Vercel rewrites those requests to `TUBECRAFT_BACKEND_URL`.

This avoids exposing provider keys to the browser and avoids treating a serverless request as a durable video worker.

See `GITHUB_VERCEL_DEPLOY.md` for the exact deployment steps.
