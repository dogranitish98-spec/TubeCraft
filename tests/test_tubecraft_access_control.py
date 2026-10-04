from starlette.requests import Request

from web.access_control import extract_access_token, require_access_token


def _request(method: str, path: str, headers=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": raw,
        "client": ("127.0.0.1", 1234),
        "server": ("127.0.0.1", 8765),
    }
    return Request(scope)


def test_extract_access_token_bearer():
    req = _request("POST", "/api/config", {"Authorization": "Bearer abc123"})
    assert extract_access_token(req) == "abc123"


def test_mutation_requires_token(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("POST", "/api/tasks/creative")
    blocked = require_access_token(req)
    assert blocked is not None
    assert blocked.status_code == 401


def test_correct_token_allows_mutation(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("POST", "/api/tasks/creative", {"X-TubeCraft-Access-Token": "secret-token"})
    blocked = require_access_token(req)
    assert blocked is None


def test_get_requests_remain_readable(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("GET", "/api/video/abc")
    blocked = require_access_token(req)
    assert blocked is None


def test_metrics_requires_token_when_configured(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("GET", "/api/metrics")
    blocked = require_access_token(req)
    assert blocked is not None
    assert blocked.status_code == 401


def test_metrics_accepts_correct_token(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("GET", "/api/metrics", {"Authorization": "Bearer secret-token"})
    assert require_access_token(req) is None


def test_sensitive_task_metadata_is_protected(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("GET", "/api/tasks/abc")
    blocked = require_access_token(req)
    assert blocked is not None
    assert blocked.status_code == 401


def test_media_file_endpoint_remains_readable(monkeypatch):
    monkeypatch.setenv("TUBECRAFT_ACCESS_TOKEN", "secret-token")
    req = _request("GET", "/api/tasks/abc/artifacts/def/file")
    assert require_access_token(req) is None
