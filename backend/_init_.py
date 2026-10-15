from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, Request
from fasttext import load_model
from pydantic import BaseModel, ConfigDict
from psycopg_pool import AsyncConnectionPool, PoolTimeout, PoolClosed, TooManyRequests  #use too many requests
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from model_config import model_endpoint,  MODEL_MAP
from langchain.agents import create_agent
from system_prompt import ReadOnly
from tools_handling import tool_call
from pathlib import Path
from dotenv import load_dotenv
from logging_handler import get_logger
import os

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
    
    # db setup for short term memory
    # Create pool once at startup
    log = get_logger("app.lifespan")
    log.info("Db connection starting up..")
    try:
        pool = AsyncConnectionPool(
        os.getenv("DB_URL"),
        name = "Pool-connection",
        min_size= 1,    #always keep 1 connection warm
        max_size= 10,   #never more than 10
        max_waiting = 5,
        max_lifetime = 3600.0,
        reconnect_timeout=2.0,
        )
        
        # check open() perhaps use with statement 
        await pool.open()
        log.info("connection pool status: open")
    # ALSO check for this 
    except PoolTimeout:
        log.exception("The pool couldn't provide a connection in acceptable time.")
        
    
    # Create checkpointer with pool (connection stays alive via pool)
    checkpointer = AsyncPostgresSaver(pool)
    # Setup once   - pool handles reconnections
    await checkpointer.setup()
    log.info("checkpointer connection successful")
    # async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
    #await checkpointer.setup()

    #tool call 
    async def get_tools():
        cached_tools = await tool_call()
        return cached_tools
        
    tools= await get_tools()
    
    sys_prompt = ReadOnly()
    
    agent_lookup = {}
    for tier, config in MODEL_MAP.items():
        endpoint = model_endpoint(tier)
        raw_prompt_string = sys_prompt.prompt
        
        log.info("creating agent..")
        agent = create_agent(
            endpoint,
            tools,
            checkpointer = checkpointer,
            system_prompt= raw_prompt_string,
            )
        agent_lookup[tier] = agent
        
    #loading fasttext langdetect model (requires to load only once)
    log.info("loading language model..")
    lang_model= load_model(os.getenv("LANG_MODEL"))
    
    # Instantiate the container
    state_container = AppStateContext(
        lang_model=lang_model,
        tools=tools,
        agent_lookup=agent_lookup,
        pool=pool,
        checkpointer=checkpointer,
    )
    
    # this Yield the context container directly to FastAPI
    try:
        yield {"context": state_container}
    
    finally:
        log.info("checkpointer connection shutting down..")
        # lastly safe application shutdown cleanup
        try:
            await pool.close()
            log.info("connection pool status: closed")
        except PoolClosed:
            log.exception("Attempt to get a connection from a closed pool.")
            
def get_ctx(request: Request) -> AppStateContext:
    """Dependency provider to safely access app state."""
    return request.state.context


    
   