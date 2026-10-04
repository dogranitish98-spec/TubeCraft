from pathlib import Path
import json, re, sys

root = Path(__file__).resolve().parents[1]
required = [
    'vercel.mjs',
    '.vercelignore',
    '.env.vercel.example',
    'static/index.html',
    'static/manifest.webmanifest',
    'static/sw.js',
    'static/icon-192.png',
    'static/icon-512.png',
    'static/apple-touch-icon.png',
    'static/favicon.ico',
    'README_GITHUB_FIRST.md',
    'GITHUB_VERCEL_DEPLOY.md',
]
missing=[str(p) for p in required if not (root/p).exists()]
if missing:
    print('MISSING:', *missing, sep='\n- ')
    sys.exit(1)
manifest=json.loads((root/'static/manifest.webmanifest').read_text())
assert manifest['name']=='TubeCraft Studio'
assert manifest['short_name']=='TubeCraft'
assert manifest['scope']=='/'
assert manifest['display']=='standalone'
for icon in manifest['icons']:
    assert (root/'static'/icon['src'].lstrip('/')).exists()
html=(root/'static/index.html').read_text()
for token in ['/manifest.webmanifest','/apple-touch-icon.png','TubeCraft Studio']:
    assert token in html, token
runtime=(root/'static/pwa-runtime.js').read_text()
assert "serviceWorker.register('/sw.js'" in runtime
assert (root/'frontend'/'vite.vercel.config.ts').exists()
print('TubeCraft Vercel/PWA release check: PASS')
