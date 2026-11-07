import sys
from pathlib import Path
from typing import Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.error_handler import retry_with_backoff
from config.logging_handler import get_logger


log = get_logger("tool_handler")


@retry_with_backoff()
async def tool_call():
    project_root = Path(__file__).resolve().parent.parent
    connections: dict[str, Any] = {
        "get_time": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-u", "-m", "tools.time_mcp"],
            "cwd": str(project_root),
            },
    }
    try:
        client = MultiServerMCPClient(connections)
        tools = await client.get_tools()
    except Exception as e:
        log.exception(f"Tool discovery failed {e}")
        raise

    if not tools:
        raise RuntimeError("MCP servers returned no tools.")

    return tools
