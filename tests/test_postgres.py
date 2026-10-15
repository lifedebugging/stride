import sys
import os
import pytest
# Adds the parent directory to the Python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _init_ import AppStateContext 
from langchain_core.messages import HumanMessage
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import uuid

@pytest.mark.asyncio
async def test_checkpointer_with_uuid():
    
    db_url = os.getenv("DB_URL")
    
    async with AsyncConnectionPool(
        db_url,
        min_size=1,
        max_size=2,
        open=False # We let the async context manager open it
    ) as pool:
        await pool.open()
        
        checkpointer = AsyncPostgresSaver(pool)
        
        await checkpointer.setup()
        
        config= {"configurable": {"thread_id" : str(uuid.uuid4())}}
        
        app_context = AppStateContext()
        checkpointer = app_context.checkpointer
        checkpointer.setup()
        state = checkpointer.aget_tuple(config)
        
        state.aput_writes(
            config=state.config,
            writes = [("messages", [HumanMessage(content = "test", id = config)])],
            task_id = "test_task_1",
            task_path = ""
            )
        
        updated = checkpointer.aget_tuple(config)
        
        assert updated is not None, "Async checkpointer failed to retrieve state"
        print("Async Database Check: PASSED ✅") 

if __name__ == "__main__":
    test = test_checkpointer_with_uuid()
    print(test)
    
