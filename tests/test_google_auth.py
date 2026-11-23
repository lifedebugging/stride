import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from google.auth.exceptions import TransportError

from ui import client as client_module
from utils import google_auth


def test_thread_ids_are_scoped_to_google_subject():
    assert google_auth.user_scoped_thread_id("user-1", "thread-1") != (
        google_auth.user_scoped_thread_id("user-2", "thread-1")
    )


def test_google_credential_verification_returns_subject_and_checks_audience(
    monkeypatch,
):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "configured-client-id")
    verified = {}

    def fake_verify(token, request, audience):
        verified.update(token=token, audience=audience)
        return {
            "sub": "google-user-123",
            "email": "user@example.com",
            "email_verified": True,
        }

    monkeypatch.setattr(google_auth, "verify_oauth2_token", fake_verify)

    subject = google_auth.verify_google_credential("Bearer signed-token")

    assert subject.subject == "google-user-123"
    assert subject.email == "user@example.com"
    assert verified == {
        "token": "signed-token",
        "audience": "configured-client-id",
    }


def test_google_credential_verification_rejects_missing_bearer_token(monkeypatch):
    def unexpected_verification(*args, **kwargs):
        pytest.fail("Google verifier should not be called without a bearer token")

    monkeypatch.setattr(google_auth, "verify_oauth2_token", unexpected_verification)

    with pytest.raises(HTTPException) as error:
        google_auth.verify_google_credential(None)

    assert error.value.status_code == 401


def test_google_credential_verification_rejects_invalid_token(monkeypatch):
    def reject_token(*args, **kwargs):
        raise ValueError("invalid signature")

    monkeypatch.setattr(google_auth, "verify_oauth2_token", reject_token)

    with pytest.raises(HTTPException) as error:
        google_auth.verify_google_credential("Bearer invalid-token")

    assert error.value.status_code == 401


def test_google_credential_verification_requires_google_subject(monkeypatch):
    monkeypatch.setattr(
        google_auth,
        "verify_oauth2_token",
        lambda *args, **kwargs: {"aud": "configured-client-id"},
    )

    with pytest.raises(HTTPException) as error:
        google_auth.verify_google_credential("Bearer signed-token")

    assert error.value.status_code == 401


def test_google_credential_verification_fails_closed_when_google_is_unavailable(
    monkeypatch,
):
    def unavailable(*args, **kwargs):
        raise TransportError("Google is unavailable")

    monkeypatch.setattr(google_auth, "verify_oauth2_token", unavailable)

    with pytest.raises(HTTPException) as error:
        google_auth.verify_google_credential("Bearer signed-token")

    assert error.value.status_code == 503


def test_chat_proxy_forwards_bearer_token_and_preserves_auth_rejection(monkeypatch):
    calls = []

    class UnauthorizedResponse:
        status_code = 401

        def close(self):
            pass

    monkeypatch.setattr(
        client_module.requests,
        "post",
        lambda *args, **kwargs: calls.append(kwargs) or UnauthorizedResponse(),
    )
    response = TestClient(client_module.app).post(
        "/chat",
        json={"query": "hello", "thread_id": "thread-1"},
        headers={"Authorization": "Bearer signed-token"},
    )

    assert response.status_code == 401
    assert calls[0]["headers"] == {"Authorization": "Bearer signed-token"}


def test_chat_history_proxy_forwards_bearer_token(monkeypatch):
    calls = []

    class HistoryResponse:
        status_code = 200

        def json(self):
            return [{"chat_id": "chat-1", "title": "My chat"}]

        def raise_for_status(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        client_module.requests,
        "get",
        lambda url, **kwargs: calls.append((url, kwargs)) or HistoryResponse(),
    )
    response = TestClient(client_module.app).get(
        "/chats",
        headers={"Authorization": "Bearer signed-token"},
    )

    assert response.status_code == 200
    assert response.json() == [{"chat_id": "chat-1", "title": "My chat"}]
    assert calls[0][0] == "http://127.0.0.1:8001/chats"
    assert calls[0][1]["headers"] == {"Authorization": "Bearer signed-token"}
