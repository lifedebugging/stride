import os
import uvicorn
import asyncio

from pydantic import BaseModel

# from error_handler import retry_with_backoffs
from config.model_config import log_routing_decision
from fastapi import FastAPI, Depends, Header
from fastapi.responses import StreamingResponse
from collections.abc import AsyncIterator

from  backend.lifespan import get_appctx, lifespan, AppStateContext
from backend.decision_logic import Decision_logic
from backend.chat_history import router as chat_history_router, store_chat_message
from utils.google_auth import user_scoped_thread_id, verify_google_credential
# from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
# from logging_handler import setup_logging, get_logger
from config.logging_handler import get_logger 
from dotenv import load_dotenv

load_dotenv(override=True)

log = get_logger("main")
# structured query
class Query(BaseModel):
    query: str
    thread_id: str 


app = FastAPI(lifespan=lifespan)
app.include_router(chat_history_router)


#handler
@app.post("/route")
async def handler(query: Query,
                  authorization: str | None = Header(default=None),
                  ctx: AppStateContext = Depends(get_appctx),   #telling the router it's dependency
                  ):
    identity = verify_google_credential(authorization)
    chat_id = query.thread_id
    checkpoint_thread_id = user_scoped_thread_id(identity.subject, chat_id)
    query = query.model_copy(
        update={"thread_id": checkpoint_thread_id}
    )
    await store_chat_message(
        ctx.pool, identity, chat_id, "user", query.query
    )

    async def stream_and_save() -> AsyncIterator[str]:
        response_parts = []
        async for chunk in main(query, ctx):
            response_parts.append(chunk)
            yield chunk

        response = "".join(response_parts)
        if response:
            await store_chat_message(
                ctx.pool, identity, chat_id, "assistant", response
            )

    return StreamingResponse(stream_and_save(), media_type="text/plain")

 
async def main(query : Query,  ctx: AppStateContext) -> AsyncIterator[str]:
    decision = await Decision_logic(query.query, ctx)
     
    tier = log_routing_decision(decision)
    # for tool in tools:
    #     print(f"Tools available: {tool.name}")

    agent_call = ctx.agent_lookup[tier]
    
    async for event in agent_call.astream_events({"messages" : [("human", query.query)]},
                                                    {"configurable": {"thread_id": query.thread_id}}, 
                                                    version="v2",
                                                    ):
            
        if event["event"] == "on_chat_model_stream":
            yield event["data"]["chunk"].text
    
             
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    is_dev = os.getenv("ENV", "production").lower() == "development"

    try:
        uvicorn.run(
            "agent:app",
            host=host,
            port=port,
            reload=is_dev,
        )
    except Exception as e:
        log.exception("An error occurred while starting the server: %s", e)

