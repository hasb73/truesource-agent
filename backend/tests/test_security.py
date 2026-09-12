from backend.app.security import redact_value
from backend.app.security import get_actor


class DummyRequest:
    def __init__(self, headers):
        self.headers = headers


def test_redact_value_masks_sensitive_strings():
    payload = {
        "token": "api_key=secret-token",
        "nested": [
            "AKIA1234567890ABCDEF",
            "postgres://admin:pass123@example.internal/app",
        ],
    }

    redacted = redact_value(payload)

    assert redacted["token"] == "[REDACTED]"
    assert redacted["nested"][0] == "[REDACTED]"
    assert redacted["nested"][1] == "[REDACTED]"


def test_get_actor_uses_demo_headers(monkeypatch):
    monkeypatch.setenv("DEV_AUTH_ROLE", "reviewer")

    actor = get_actor(DummyRequest({"X-Demo-User": "Riley", "X-Demo-Tenant": "tenant-a"}))

    assert actor["id"] == "Riley"
    assert actor["name"] == "Riley"
    assert actor["role"] == "reviewer"
    assert actor["tenant_id"] == "tenant-a"


def test_get_actor_defaults_when_headers_missing():
    actor = get_actor(DummyRequest({}))

    assert actor["id"] == "demo-reviewer"
    assert actor["name"] == "Demo Reviewer"
