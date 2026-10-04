#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

command -v node >/dev/null || { echo "Node.js 18+ is required" >&2; exit 1; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 1; }
node -e 'const v=process.versions.node.split(".").map(Number); if(v[0]<18) process.exit(1)'

npm ci --no-audit --no-fund
npm run build
cd "$ROOT"

for f in manifest.webmanifest sw.js pwa-runtime.js offline.html icon-192.png icon-512.png; do
  test -f "frontend/public/$f" || { echo "Missing frontend/public/$f" >&2; exit 1; }
  test -f "static/$f" || { echo "Missing static/$f" >&2; exit 1; }
done

grep -q 'static/assets/' static/index.html || { echo "Built index is missing hashed assets" >&2; exit 1; }

echo "TubeCraft PWA build + artifact verification complete."
