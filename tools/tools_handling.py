from langchain_mcp_adapters.client import MultiServerMCPClient
from pathlib import Path
from error_handler import retry_with_backoff
from logging_handler import get_logger
import asyncio
import sys


log = get_logger("tool_handler")
@retry_with_backoff()
async def tool_call():
    tools = []
    try:
        client = MultiServerMCPClient({
            "get_time": {
                "transport": "stdio",
                "command": "python",
                "args": [str(Path(r"D:/Documents/Project_x/mcp_tool.py"))],
                },
            "rag_subagent":{
                "transport": "http",
                "url": "http://localhost:8000/mcp"
                }
            })
        
    except Exception as e:
        log.exception("Tool's broken")

    if client:
        tools = await client.get_tools()
        return tools
    else:
        log.warning("server is running but couldn't fetch the tools, check your server file.")


# print(asyncio.run(tool_call()))

