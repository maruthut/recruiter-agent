# MCP Streamable HTTP Setup Guide

## Overview
The HR Recruiter Agent uses **Streamable HTTP** transport for MCP (Model Context Protocol) communication with JSON-RPC 2.0 protocol.

## Architecture

### Streamable HTTP Transport
The HTTP mode uses the MCP **Streamable HTTP** transport protocol:
- **Protocol**: JSON-RPC 2.0 over HTTP POST
- **Session Management**: Uses `mcp-session-id` header for stateful communication
- **Response Format**: Server-Sent Events (SSE) with `event: message` and `data: {...}` format
- **Endpoint**: Single POST endpoint that handles all JSON-RPC methods

### Protocol Flow
```
1. Client → POST /mcp (initialize request)
   Server → 200 OK with mcp-session-id header + SSE stream
   
2. Client → POST /mcp (notifications/initialized notification, no id field)
   Server → 202 Accepted
   
3. Client → POST /mcp (tools/list request with session ID)
   Server → 200 OK with tools array
   
4. Client → POST /mcp (tools/call request with session ID)
   Server → 200 OK with tool results
```

## Environment Variables

### Required Configuration
```bash
# MCP server endpoint
MCP_HTTP_URL=http://localhost:5002/mcp

# Google API Key for Gemini
GOOGLE_API_KEY=your_api_key_here
```

## Key Implementation Details

### 1. Initialization Handshake
The MCP protocol requires a two-step initialization:
```python
# Step 1: Send initialize request
init_result = await send_jsonrpc("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
        "name": "hr-agent",
        "version": "1.0.0"
    }
})

# Step 2: Send initialized notification (without id field!)
await send_jsonrpc("notifications/initialized", {}, is_notification=True)
```

**Critical**: The `notifications/initialized` message MUST be sent as a notification (no `id` field in JSON-RPC) to complete the handshake. Without this, subsequent requests will fail with:
```
WARNING:root:Failed to validate request: Received request before initialization was complete
```

### 2. Session Management
```python
# Capture session ID from initialize response headers
if 'mcp-session-id' in response.headers:
    session_id = response.headers['mcp-session-id']

# Include session ID in all subsequent requests
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "mcp-session-id": session_id
}
```

### 3. SSE Response Parsing
Even for single-shot requests, the server responds with SSE format:
```python
# Parse SSE stream
for line in response.text.split('\n'):
    if line.startswith('data: '):
        data = line[6:]  # Remove 'data: ' prefix
        result = json.loads(data)
        return result
```

### 4. JSON-RPC Message Format

**Request (with id)**:
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}
```

**Notification (without id)**:
```json
{
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
    "params": {}
}
```

## Testing

### Test HTTP Connection
```bash
python test_mcp_http.py
```

Expected output:
```
✅ MCP session initialized
✅ Sent initialized notification
✅ Tools discovered: [rank_resumes_mcp, fetch_job_description_mcp, analyze_resume_mcp]
✅ Tool result: {...}
✅ HTTP MCP connection test PASSED
```

### Test Agent
```bash
# Windows PowerShell
python hr_agent.py "Analyze resumes for software_engineer.txt"

# Linux/Mac
python hr_agent.py "Analyze resumes for software_engineer.txt"
```

## Troubleshooting

### Error: "Received request before initialization was complete"
**Cause**: Missing or incorrect `notifications/initialized` notification
**Solution**: Ensure `notifications/initialized` is sent as a notification (no `id` field)

### Error: "Invalid request parameters" (-32602)
**Cause**: Either initialization not complete or incorrect parameter format
**Solution**: 
1. Verify initialization handshake is complete
2. Check that parameters match tool's `inputSchema`

### Error: HTTP 406 Not Acceptable
**Cause**: Missing Accept header
**Solution**: Include both content types: `"Accept": "application/json, text/event-stream"`

### Error: Connection refused
**Cause**: MCP server not running or wrong URL
**Solution**: 
1. Verify MCP server is running
2. Check `MCP_HTTP_URL` matches server address
3. Test with: `curl -X POST http://localhost:5002/mcp`

## Performance Considerations

- **Latency**: HTTP overhead and SSE parsing add minimal latency
- **Scalability**: HTTP mode enables distributed deployment and load balancing
- **Reliability**: Session management ensures stateful communication across requests

## Dependencies

The agent requires the `httpx` library for HTTP communication:
```bash
pip install httpx
```

## Code Structure

### Main Implementation: `hr_agent.py`
- `discover_and_invoke_tool()`: Main function for MCP tool discovery and invocation using Streamable HTTP

### Testing: `test_mcp_http.py`
- Tests HTTP connection, initialization, tool discovery, and invocation
- Validates SSE response parsing
- Tests session management

## References

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
