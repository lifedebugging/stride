import asyncio
import os
from pathlib import Path
from typing import Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.error_handler import retry_with_backoff
from config.logging_handler import get_logger


log = get_logger("tool_handler")


@retry_with_backoff()
async def tool_call():
    connections: dict[str, Any] = {
        "get_time": {
            "transport": "stdio",
            "command": "python",
        "args": [str(Path(__file__).resolve().parent / "time_tool.py")],
            },
        
        "rag_subagent": {
            "transport": "http",
            "url": os.environ["RAG_SUBAGENT_MCP_URL"],
        }
    }
    try:
        client = MultiServerMCPClient(connections)
        
    except Exception as e:
        log.exception(f"Tool Connection failed : {e}")
        raise RuntimeError("Tool connection failed. Please try again later.")
    
    if client:
        tools = await client.get_tools()
        print(tools)
        return tools
    else:
        log.warning("server is running but couldn't fetch the tools, check your server file.")


print(asyncio.run(tool_call()))
