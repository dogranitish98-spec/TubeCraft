from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_has_installable_metadata():
    data = json.loads((ROOT / "static/manifest.webmanifest").read_text())
    assert data["name"] == "TubeCraft Studio"
    assert data["id"] == "/"
    assert data["start_url"] == "/"
    assert data["scope"] == "/"
    assert data["display"] == "standalone"
    assert len(data["icons"]) >= 2


def test_service_worker_never_caches_api_or_media_and_caches_only_known_static_assets():
    js = (ROOT / "static/sw.js").read_text()
    assert "url.pathname.startsWith('/api/')" in js
    assert "static/generated" in js
    assert "isCacheableStatic" in js
    assert "request.mode === 'navigate'" in js


def test_pwa_runtime_bootstraps_before_vue_in_shipped_index():
    html = (ROOT / "static/index.html").read_text()
    runtime = html.index('src="/static/pwa-runtime.js"')
    bundle = html.index('src="/static/assets/index-KzCkI4Os.js"')
    assert runtime < bundle


def test_upload_limits_are_configurable():
    text = (ROOT / "web/upload_limits.py").read_text()
    assert "TUBECRAFT_MAX_UPLOAD_MB" in (ROOT / ".env.example").read_text()
    assert "413" in text


def test_service_worker_prefers_network_for_static_asset_updates():
    js = (ROOT / "static/sw.js").read_text()
    assert "fetch(request, { cache: 'no-store' })" in js
    assert "caches.match(request).then(cached => cached || caches.match('/offline.html'))" in js


def test_transient_retry_budget_is_configurable():
    config = (ROOT / "core/config.py").read_text()
    env = (ROOT / ".env.example").read_text()
    assert "agnes_video_transient_retry_seconds" in config
    assert "AGNES_VIDEO_TRANSIENT_RETRY_SECONDS=900" in env


def test_security_middleware_protects_metrics_and_auth_is_no_store():
    access = (ROOT / "web/access_control.py").read_text()
    auth = (ROOT / "web/routes/auth_routes.py").read_text()
    assert "PROTECTED_READ_PATHS" in access
    assert '"/api/metrics"' in access
    assert "Cache-Control" in auth


def test_health_reports_readiness_checks():
    health = (ROOT / "web/routes/health_routes.py").read_text()
    assert '"ready"' in health
    assert '"ffmpeg"' in health
    assert '"api_key_configured"' in health


def test_upload_limits_support_stream_to_disk():
    text = (ROOT / "web/upload_limits.py").read_text()
    assert "save_upload_limited" in text
    assert "os.replace(tmp_path, destination)" in text


def test_auth_check_has_bruteforce_throttle():
    text = (ROOT / "web/routes/auth_routes.py").read_text()
    assert "_FAILURE_LIMIT = 5" in text
    assert "Retry-After" in text


def test_upstream_401_has_key_rotation_and_actionable_diagnostic():
    text = (ROOT / "core/api/agnes_video.py").read_text()
    assert 'if resp.status_code == 401' in text
    assert 'Verify that the configured Agnes API key is valid' in text
    assert 'ring.rotate()' in text


def test_server_retry_progress_is_structured():
    api = (ROOT / "core/api/agnes_video.py").read_text()
    pipe = (ROOT / "core/pipelines/__init__.py").read_text()
    i18n = (ROOT / "core/i18n_backend.py").read_text()
    assert 'progress_callback("server_retry"' in api
    assert 'progress.video.server_retry' in pipe
    assert 'progress.video.server_retry' in i18n


def test_dependency_bounds_avoid_known_moviepy_pillow_conflict():
    req = (ROOT / "requirements.txt").read_text()
    assert "moviepy>=2.0.0,<3.0.0" in req
    assert "Pillow>=9.0.0,<12.0.0" in req
