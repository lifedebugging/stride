import asyncio
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from logging_handler import get_logger

app = Server("first-server")

log = get_logger("mcp/datetime")

#the Discovery 
@app.list_tools()
async def list_my_tools():
    return [
        Tool(
            name = "get_datetime",
            description="Returns current date and time with accuracy",
            inputSchema={"types" : "object", "properties": {}},
            )
        ]

# the Logic (The Switchboard)
@app.call_tool()
async def execute_tool(name):
    if name == "get_datetime":
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return [TextContent(type="text", 
                                text = f"The time is {current_datetime}"
                            )]
        except Exception as e:
            log.error("datetime tool not working", error=str(e))
            
    else:
    # Always handle the "unknown tool" case
        log.error(ValueError(f"Tool not found : {name}"))

#the Transport (The Pipes)
async def main():
    #1. (The stdio pipes)
    try:
        async with stdio_server() as (read, write):
            # 2. Start the brain (The server)
            await app.run(read, 
                        write, 
                        app.create_initialization_options(), # These are the handshake settings
                        )
    except Exception as e:
        log.error("tool server startup failed", error=str(e))
        
if __name__ == "__main__":
    asyncio.run(main())

