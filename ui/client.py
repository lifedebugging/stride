import time

import requests
from config.logging_handler import get_logger
from fastapi import FastAPI, HTTPException
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
def chat_endpoint(payload: ChatRequest):
    upstream_response = None
    try:
        upstream_response = requests.post(
            "http://127.0.0.1:8001/route",
            json=payload.model_dump(),
            stream=True,
            timeout=(5, None),
        )
        upstream_response.raise_for_status()
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
