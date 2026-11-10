import os
import uvicorn
import asyncio

from pydantic import BaseModel

# from error_handler import retry_with_backoffs
from config.model_config import log_routing_decision
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from collections.abc import AsyncIterator

from  backend.lifespan import get_appctx, lifespan, AppStateContext
from backend.decision_logic import Decision_logic
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

#handler
@app.post("/route")
async def handler(query: Query, 
                  ctx: AppStateContext = Depends(get_appctx),   #telling the router it's dependency
                  ):
    
    # StreamingResponse for streaming output
    return StreamingResponse(main(query, ctx), 
                            media_type="text/plain",
                            )

 
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
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8001"))
    try:
        uvicorn.run("main:app", host=host, port=port, reload=True)
    except Exception as e:
        log.exception(f"an error occurred: {e}") 

