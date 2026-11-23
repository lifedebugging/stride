import hashlib
import logging
import os
from dataclasses import dataclass

from fastapi import HTTPException
from google.auth.exceptions import TransportError
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token

DEFAULT_GOOGLE_CLIENT_ID = (
    "946934091029-n1scrsb53sps38n8vqi2uinh97orf7f0.apps.googleusercontent.com"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str


def user_scoped_thread_id(subject: str, thread_id: str) -> str:
    return hashlib.sha256(f"{subject}:{thread_id}".encode("utf-8")).hexdigest()


def verify_google_credential(authorization: str | None) -> GoogleIdentity:
    parts = authorization.split() if authorization else []
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Google sign-in is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    client_id = os.getenv("GOOGLE_CLIENT_ID", DEFAULT_GOOGLE_CLIENT_ID).strip()
    if not client_id:
        logger.error("Google sign-in is not configured.")
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is temporarily unavailable.",
        )

    try:
        claims = verify_oauth2_token(
            parts[1],
            Request(),
            audience=client_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail="Google sign-in is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except TransportError as exc:
        logger.exception("Google credential verification is unavailable.")
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is temporarily unavailable.",
        ) from exc

    subject = claims.get("sub")
    email = claims.get("email")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(email, str)
        or not email
        or claims.get("email_verified") is not True
    ):
        raise HTTPException(
            status_code=401,
            detail="Google sign-in is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return GoogleIdentity(subject=subject, email=email)
