#!/usr/bin/env python3
"""
Test script for MCP HTTP mode connection and tool discovery.
"""

import os
import json
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", "http://localhost:5002/mcp")

async def test_mcp_http_connection():
    """Test MCP Streamable HTTP connection using JSON-RPC 2.0 over HTTP POST."""
    try:
        import httpx
        import json

        logger.info(f"Testing MCP Streamable HTTP transport: {MCP_HTTP_URL}")

        message_id = [1]
        session_id = [None]

        async def send_jsonrpc(method: str, params=None, is_notification=False):
            """Send a JSON-RPC 2.0 message via HTTP POST."""
            msg = {
                "jsonrpc": "2.0",
                "method": method
            }
            
            # Notifications don't have an id field
            if not is_notification:
                msg["id"] = message_id[0]
                message_id[0] += 1
            
            # Only include params if explicitly provided and not None
            if params is not None:
                msg["params"] = params

            logger.info(f"Sending: {method} ({'notification' if is_notification else 'request'})")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            # Add session ID to subsequent requests
            if session_id[0]:
                headers["mcp-session-id"] = session_id[0]
                logger.info(f"Using session ID: {session_id[0]}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    MCP_HTTP_URL,
                    json=msg,
                    headers=headers,
                    timeout=30.0
                )
                
                logger.info(f"Response: HTTP {response.status_code}")
                
                # Capture session ID from first response
                if not session_id[0] and 'mcp-session-id' in response.headers:
                    session_id[0] = response.headers['mcp-session-id']
                    logger.info(f"✅ Captured session ID: {session_id[0]}")
                
                if response.status_code != 200:
                    logger.error(f"Error: {response.text}")
                    return None

                # Check if response is SSE or JSON
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    logger.info("Received SSE stream response")
                    # Parse SSE events
                    result = None
                    for line in response.text.split('\n'):
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            try:
                                result = json.loads(data)
                                break
                            except:
                                continue
                    if not result:
                        logger.error("No valid JSON data in SSE stream")
                        return None
                else:
                    result = response.json()

                if 'error' in result:
                    logger.error(f"MCP error: {result['error']}")
                    return None

                return result

        # Initialize
        init_result = await send_jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })

        if not init_result:
            return False

        logger.info("✅ MCP session initialized")

        # Send initialized notification to complete the handshake
        try:
            await send_jsonrpc("notifications/initialized", {}, is_notification=True)
            logger.info("✅ Sent initialized notification")
        except Exception as e:
            logger.debug(f"Initialized notification handling: {e}")

        # Try to discover tools
        try:
            tools_result = await send_jsonrpc("tools/list")
            if tools_result:
                tools = tools_result.get('result', {}).get('tools', [])
                logger.info(f"✅ Tools discovered: {json.dumps(tools, indent=2)}")
                tool_names = [t.get('name') for t in tools]
            else:
                raise Exception("No result from tools/list")
        except Exception as e:
            logger.warning(f"Tool discovery failed: {e}, using known tools")
            tool_names = ['rank_resumes_mcp', 'fetch_job_description_mcp', 'analyze_resume_mcp']
        
        logger.info(f"✅ Available tools: {tool_names}")

        # Test rank_resumes_mcp
        if 'rank_resumes_mcp' in tool_names:
            logger.info("Testing rank_resumes_mcp tool...")

            test_args = {
                "job_description": "Software Engineer position requiring Python, ML, and web development skills.",
                "resume_texts": [
                    "Alice Johnson: Python developer with 5 years experience in Flask, Django, and machine learning.",
                    "Bob Smith: Web developer with JavaScript and basic Python knowledge."
                ],
                "resume_filenames": [
                    "alice_johnson.pdf",
                    "bob_smith.pdf"
                ]
            }

            invoke_result = await send_jsonrpc("tools/call", {
                "name": "rank_resumes_mcp",
                "arguments": test_args
            })

            if not invoke_result:
                return False

            result = invoke_result.get('result', {})
            logger.info(f"✅ Tool result: {json.dumps(result, indent=2)}")

        return True

    except ImportError as e:
        logger.error(f"❌ Import error: {e}. Install with: pip install httpx")
        return False
    except Exception as e:
        import traceback
        logger.error(f"❌ HTTP connection test failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    except Exception as e:
        logger.error(f"❌ HTTP connection test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("=" * 60)
    print("MCP HTTP Mode Connection Test")
    print("=" * 60)

    success = await test_mcp_http_connection()

    print("=" * 60)
    if success:
        print("✅ HTTP MCP connection test PASSED")
        print("HTTP mode is ready to use!")
    else:
        print("❌ HTTP MCP connection test FAILED")
        print("Check your MCP server and MCP_HTTP_URL configuration")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())