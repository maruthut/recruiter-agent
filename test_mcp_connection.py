"""
DEPRECATED: This test file is for stdio mode MCP connection which has been removed.
Please use test_mcp_http.py for testing Streamable HTTP MCP connections.

This file is kept for reference only.
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_connection():
    """Test connection to MCP server and list available tools."""
    
    # Load MCP configuration
    with open('mcp.json', 'r') as f:
        mcp_config = json.load(f)
    
    server_config = mcp_config['mcpServers']['default-server']
    command = server_config['command']
    args = server_config['args']
    env = server_config.get('env', {})
    
    print(f"Connecting to MCP server...")
    print(f"Command: {command}")
    print(f"Args: {args}")
    print(f"Env: {env}")
    print("-" * 80)
    
    try:
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("✅ Successfully connected to MCP server!")
                print("-" * 80)
                
                # List available tools
                print("Listing available tools...")
                result = await session.list_tools()
                
                print(f"\n📋 Found {len(result.tools)} tools:")
                print("-" * 80)
                
                for tool in result.tools:
                    print(f"\n🔧 Tool: {tool.name}")
                    print(f"   Description: {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        print(f"   Input Schema: {json.dumps(tool.inputSchema, indent=2)}")
                
                print("-" * 80)
                print("✅ Test completed successfully!")
                
    except Exception as e:
        print(f"❌ Error connecting to MCP server:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
