from langchain_mcp_adapters.client import MultiServerMCPClient
from pathlib import Path
from config.error_handler import retry_with_backoff
from config.logging_handler import get_logger
import asyncio
import sys
from typing import Any


log = get_logger("tool_handler")
@retry_with_backoff()
async def tool_call():
    tools = []
    connections: dict[str, Any] = {
        "get_time": {
            "transport": "stdio",
            "command": "python",
        "args": [str(Path("gettime_tool.py"))],
            },
        
        "rag_subagent":{
            "transport": "http",
            "url": "http://localhost:8000/mcp"
            }
        }
    try:
        client = MultiServerMCPClient(connections)
        
    except Exception as e:
        log.exception(f"Tool Connection failed : {e}")
        raise RuntimeError("Tool connection failed. Please try again later.")
    
    if client:
        tools = await client.get_tools()
        return tools
    else:
        log.warning("server is running but couldn't fetch the tools, check your server file.")


print(asyncio.run(tool_call()))

