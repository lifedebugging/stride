import sys
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
            "command": sys.executable,
            "args": ["-u",
                    str(Path(__file__).resolve().parent / "time_mcp.py")],
            },
        
        "rag_subagent": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-u",
                    str(Path(__file__).resolve().parent / "rag_mcp.py")],
        }
    }
    try:
        client = MultiServerMCPClient(connections)
        tools = await client.get_tools()
    except Exception as e:
        log.exception(f"Tool discovery failed: {e}")
        raise RuntimeError("Tool discovery failed. Please check the MCP server logs.") from e

    if not tools:
        raise RuntimeError("MCP servers returned no tools.")

    return tools
