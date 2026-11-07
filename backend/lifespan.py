import os
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, Request
from fasttext import load_model   
from pydantic import BaseModel, ConfigDict
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config.model_config import model_endpoint, MODEL_MAP
from langchain.agents import create_agent
from prompt.system_prompt import ReadOnly
from tools.tools_handling import tool_call
from tools.rag_agent_tool import create_rag_tool
from dotenv import load_dotenv
from config.logging_handler import get_logger


#override=True gives the os set variable absolute priority
load_dotenv(override=True)


class AppStateContext(BaseModel):
    #takes all sorts of datatypes eg. connection pool etc..
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    agent_lookup: Any = None
    tools: Any = None
    pool: Any = None #AsyncConnectionPool
    checkpointer: Any = None #AsyncPostgresSaver
    lang_model: Any = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    log = get_logger("app.lifespan")
    log.info("Db connection starting up..")

    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL must be configured before starting the application.")

    pool = AsyncConnectionPool(     
        db_url,
        name="Pool-connection",
        kwargs={"row_factory": dict_row},    #improves how i can access database row[id] instead row[0]
        min_size=1,  #keep 1 connection warm
        max_size=10, #never more than 10
        max_waiting=5,
        max_lifetime=3600.0,
        reconnect_timeout=2.0,
        open=False,
    )

    try:
        await pool.open()
        log.info("connection pool status: open")
        
        # Create checkpointer with pool (connection stays alive via pool)
        checkpointer = AsyncPostgresSaver(conn=pool)  # type: ignore
        log.info("checkpointer connection successful")

        tools = await tool_call()
        tools.append(create_rag_tool())

        sys_prompt = ReadOnly()
        agent_lookup = {}
        
        for tier in MODEL_MAP:
            endpoint = model_endpoint(tier)
            if endpoint is None:
                raise RuntimeError(f"No model endpoint configured for tier {tier.value}.")
            
            log.info("creating agent..")
            
            agent = create_agent(
                endpoint,
                tools,
                checkpointer=checkpointer,
                system_prompt=sys_prompt.prompt,
            )
            agent_lookup[tier] = agent

        log.info("loading language model..")
        
        lang_model_path = os.getenv("LANG_MODEL")
        if not lang_model_path:
            raise RuntimeError("LANG_MODEL must be configured before starting the application.")
        
        lang_model = load_model(lang_model_path)

        state_container = AppStateContext(
            lang_model=lang_model,
            tools=tools,
            agent_lookup=agent_lookup,
            pool=pool,
            checkpointer=checkpointer,
        )
        
        yield {"context": state_container}
        
    finally:
        log.info("checkpointer connection shutting down..")
        
        if not pool.closed:
            await pool.close()
            log.info("connection pool status: closed")
            
def get_appctx(request: Request) -> AppStateContext:
    """Dependency provider to safely access app state."""
    return request.state.context



