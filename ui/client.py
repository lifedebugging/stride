import time
from urllib.parse import quote

import requests
from config.logging_handler import get_logger
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()
log = get_logger("client.response")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    thread_id: str


def proxy_history_request(path: str, authorization: str | None):
    upstream_response = None
    try:
        upstream_response = requests.get(
            f"http://127.0.0.1:8001{path}",
            headers={"Authorization": authorization} if authorization else {},
            timeout=(5, 30),
        )
        if upstream_response.status_code in (401, 404, 503):
            status_code = upstream_response.status_code
            raise HTTPException(
                status_code=status_code,
                detail={
                    401: "Google sign-in is required or has expired.",
                    404: "Chat not found.",
                    503: "Google sign-in is temporarily unavailable.",
                }[status_code],
            )
        upstream_response.raise_for_status()
        return upstream_response.json()
    except HTTPException:
        raise
    except requests.RequestException as exc:
        log.exception("chat history request failed")
        raise HTTPException(
            status_code=502,
            detail="Backend service unavailable",
        ) from exc
    finally:
        if upstream_response is not None:
            upstream_response.close()


def stream_response(upstream_response: requests.Response):
    start = time.perf_counter()
    try:
        for chunk in upstream_response.iter_content(chunk_size=None):
            if chunk:
                yield chunk
        log.info("response complete, %.2f", time.perf_counter() - start)
    except requests.RequestException:
        log.exception("response interrupted")
        raise
    finally:
        upstream_response.close()


@app.post("/chat")
def chat_endpoint(
    payload: ChatRequest,
    authorization: str | None = Header(default=None),
):
    upstream_response = None
    try:
        upstream_response = requests.post(
            "http://127.0.0.1:8001/route",
            json=payload.model_dump(),
            headers={"Authorization": authorization} if authorization else {},
            stream=True,
            timeout=(5, None),
        )
        if upstream_response.status_code in (401, 503):
            status_code = upstream_response.status_code
            upstream_response.close()
            raise HTTPException(
                status_code=status_code,
                detail=(
                    "Google sign-in is required or has expired."
                    if status_code == 401
                    else "Google sign-in is temporarily unavailable."
                ),
            )
        upstream_response.raise_for_status()
    except HTTPException:
        raise
    except requests.RequestException as exc:
        if upstream_response is not None:
            upstream_response.close()
        log.exception("backend request failed")
        raise HTTPException(
            status_code=502,
            detail="Backend service unavailable",
        ) from exc

    return StreamingResponse(
        stream_response(upstream_response),
        media_type="text/plain",
    )


@app.get("/chats")
def list_chats(authorization: str | None = Header(default=None)):
    return proxy_history_request("/chats", authorization)


@app.get("/chats/{chat_id}")
def get_chat(
    chat_id: str,
    authorization: str | None = Header(default=None),
):
    return proxy_history_request(
        f"/chats/{quote(chat_id, safe='')}",
        authorization,
    )
