# TubeCraft Studio — GitHub → Vercel → PWA

## What this repository is

TubeCraft Studio is the installable PWA/web interface. The video-generation engine remains Agnes, deployed as a persistent backend.

This split is intentional: Vercel is excellent for the PWA shell and HTTP routing, while long-running video jobs need a persistent engine/runtime. Vercel supports FastAPI and long-running functions, but Agnes currently relies on in-process task state and a writable workspace, so the production-safe path is to keep the engine persistent and point the PWA at it.

## 1. Put the project on GitHub

Create a new repository and upload the **contents of this folder** (not the outer ZIP folder).

Do not upload:
- `.env`
- `.agnes_config/`
- `.working_dir/`
- API keys or tokens
- `node_modules/`
- Python virtual environments

The included `.gitignore` and `.vercelignore` cover the common local/runtime paths.

## 2. Deploy the PWA to Vercel

Import the GitHub repository into Vercel.

Recommended project settings:
- Framework: Other / auto-detected static output
- Build command: use the repository Vercel configuration (it runs the Vue/Vite production build)
- Output directory: `static`
- Install command: leave default

Then add this Production environment variable:

`TUBECRAFT_BACKEND_URL=https://YOUR-AGNES-BACKEND.example.com`

Redeploy after saving the environment variable.

The Vercel configuration rewrites `/api/*` to the Agnes backend, so the browser keeps using same-origin `/api` URLs.

## 3. Keep the Agnes engine persistent

Run the same repository on a persistent machine/server using the existing startup path, Docker setup, or another supported deployment.

Configure the engine there with its own `AGNES_API_KEY`, `TUBECRAFT_ACCESS_TOKEN` and writable workspace.

Do not put `AGNES_API_KEY` into the public PWA build or any `VITE_*` variable.

## 4. Verify the deployment

Open:
- `/`
- `/manifest.webmanifest`
- `/sw.js`
- `/icon-192.png`
- `/icon-512.png`

Then check:
1. Install TubeCraft from the browser's install prompt.
2. Open TubeCraft in standalone mode.
3. Confirm the engine/health status is reachable.
4. Run the in-app self test.
5. Submit the 5-second live generation test only after the Agnes backend is configured.

## 5. App identity

The PWA name is:
- Full name: `TubeCraft Studio`
- Short name: `TubeCraft`
- Description: `AI video production workspace powered by the Agnes video engine.`

The repository includes:
- `icon.png` 1024×1024
- `icon-512.png`
- `icon-192.png`
- `apple-touch-icon.png`
- `favicon.ico`
- `manifest.webmanifest`
- root-scope service worker
- install/update handling

## Important deployment note

A Vercel-hosted PWA is not the same thing as a persistent video worker. The PWA can be fully deployed and installed from Vercel while Agnes remains the generation engine. This avoids silently losing long-running jobs because a serverless invocation ended or its instance was recycled.
