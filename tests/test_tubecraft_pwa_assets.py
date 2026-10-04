from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_pwa_manifest_is_valid_and_installable():
    manifest = json.loads((ROOT / "frontend/public/manifest.webmanifest").read_text())
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert {i["sizes"] for i in manifest["icons"]} >= {"192x192", "512x512"}


def test_pwa_runtime_and_service_worker_are_shipped():
    runtime = (ROOT / "frontend/public/pwa-runtime.js").read_text()
    sw = (ROOT / "frontend/public/sw.js").read_text()
    assert "serviceWorker.register('/sw.js'" in runtime
    assert "SKIP_WAITING" in runtime
    assert "SKIP_WAITING" in sw
    assert "/api/" in sw
    assert "static/generated" in sw


def test_server_pwa_routes_exist():
    server = (ROOT / "server.py").read_text()
    for route in ['"/manifest.webmanifest"', '"/sw.js"', '"/offline.html"', '"/icon-192.png"', '"/icon-512.png"']:
        assert route in server


def test_built_shell_references_runtime():
    html = (ROOT / "static/index.html").read_text()
    assert "/static/pwa-runtime.js" in html
