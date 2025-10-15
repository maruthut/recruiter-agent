# MCP HTTP Mode Implementation

## Overview

The HR Recruiter AI Agent now supports **dual MCP communication modes**:
- **Stdio Mode** (existing): Docker container with stdio communication
- **HTTP Mode** (new): Direct HTTP REST API communication

## Implementation Details

### Environment Variables

Added two new environment variables to control MCP communication:

```env
MCP_MODE=stdio          # "stdio" or "http"
MCP_HTTP_URL=http://localhost:5001/api/mcp/  # HTTP endpoint
```

### Architecture Changes

#### 1. Configuration Loading
- **Stdio Mode**: Loads `mcp.json` configuration file
- **HTTP Mode**: Uses `MCP_HTTP_URL` environment variable
- **Validation**: Ensures correct configuration based on selected mode

#### 2. Tool Discovery & Invocation
- **Unified Interface**: `discover_and_invoke_tool()` chooses mode automatically
- **Stdio Implementation**: `_discover_and_invoke_tool_stdio()`
- **HTTP Implementation**: `_discover_and_invoke_tool_http()`

### HTTP Mode Implementation

#### Tool Discovery
```python
tools_url = f"{MCP_HTTP_URL.rstrip('/')}/tools"
async with session.get(tools_url) as response:
    tools_data = await response.json()
    _mcp_tools_cache = tools_data.get('tools', [])
```

#### Tool Invocation
```python
invoke_url = f"{MCP_HTTP_URL.rstrip('/')}/tools/{tool_name}/invoke"
async with session.post(invoke_url, json=kwargs) as response:
    result_data = await response.json()
    return json.loads(result_data['result']['content'][0]['text'])
```

### Dependencies

Added `aiohttp==3.9.1` for asynchronous HTTP communication.

### Error Handling

- **Mode Validation**: Ensures `MCP_MODE` is either "stdio" or "http"
- **HTTP Errors**: Handles connection failures, invalid responses
- **Dependency Checks**: Validates aiohttp availability for HTTP mode
- **Graceful Fallback**: Clear error messages for configuration issues

## Usage Examples

### Stdio Mode (Default)
```env
MCP_MODE=stdio
# Requires mcp.json configuration
```

### HTTP Mode
```env
MCP_MODE=http
MCP_HTTP_URL=http://localhost:5001/api/mcp/
```

## Testing

### HTTP Mode Test Script
Created `test_mcp_http.py` to verify HTTP connectivity:

```bash
python tests/test_mcp_http.py
```

Tests:
- HTTP connection to MCP server
- Tool discovery via `/tools` endpoint
- Tool invocation via `/tools/{name}/invoke` endpoint
- Response parsing and validation

## API Endpoints Expected

The HTTP mode expects the MCP server to provide these REST endpoints:

### GET `/tools`
Returns available tools:
```json
{
  "tools": [
    {"name": "rank_resumes_mcp", "description": "..."},
    {"name": "fetch_job_description_mcp", "description": "..."},
    {"name": "analyze_resume_mcp", "description": "..."}
  ]
}
```

### POST `/tools/{tool_name}/invoke`
Invokes a specific tool with arguments:
```json
// Request
{
  "job_description": "...",
  "resumes": ["...", "..."]
}

// Response
{
  "result": {
    "content": [
      {"text": "{\"candidates\": [...]}"}  // JSON string in text field
    ]
  }
}
```

## Backward Compatibility

- **Existing Stdio Mode**: Fully preserved and working
- **Default Behavior**: Still uses stdio mode if `MCP_MODE` not specified
- **Configuration Files**: `mcp.json` still required for stdio mode
- **API**: No changes to agent tool interfaces

## Benefits

### HTTP Mode Advantages
- **No Docker Dependency**: Direct HTTP calls to MCP server
- **Easier Deployment**: No container management required
- **Better Monitoring**: Standard HTTP logging and debugging
- **Scalability**: Can load balance multiple MCP server instances
- **Firewall Friendly**: Standard HTTP ports (80/443)

### Stdio Mode Advantages
- **Proven Working**: Tested and verified with Docker container
- **Security**: Isolated container environment
- **Protocol Compliance**: Full MCP stdio protocol support

## Configuration Examples

### Development (HTTP Mode)
```env
MCP_MODE=http
MCP_HTTP_URL=http://localhost:5001/api/mcp/
```

### Production (Stdio Mode)
```env
MCP_MODE=stdio
# Uses mcp.json configuration
```

## Troubleshooting

### HTTP Mode Issues
- **"aiohttp not installed"**: Run `pip install aiohttp`
- **"HTTP 404"**: Check MCP_HTTP_URL and server endpoints
- **"Connection refused"**: Ensure MCP server is running on specified port
- **"Invalid response format"**: Verify API response structure matches expectations

### Mode Selection Issues
- **"Invalid MCP_MODE"**: Must be exactly "stdio" or "http"
- **Missing configuration**: Ensure appropriate config for selected mode

## Future Enhancements

- **Health Checks**: Automatic MCP server health monitoring
- **Retry Logic**: Automatic retry on HTTP failures
- **Authentication**: Support for authenticated HTTP endpoints
- **Metrics**: HTTP request/response metrics collection
- **Load Balancing**: Multiple MCP server endpoint support

## Files Modified

1. **hr_agent.py**: Added HTTP mode support and dual communication logic
2. **requirements.txt**: Added aiohttp dependency
3. **README.md**: Updated configuration and troubleshooting sections
4. **test_mcp_http.py**: New HTTP mode test script

## Testing Status

- ✅ **Stdio Mode**: Working (existing functionality preserved)
- ✅ **HTTP Mode**: Implemented and ready for testing
- ✅ **Mode Selection**: Environment variable validation working
- ✅ **Error Handling**: Comprehensive error messages implemented
- ✅ **Documentation**: Complete setup and troubleshooting guides

## Next Steps

1. **Test HTTP Mode**: Run `python test_mcp_http.py` with your MCP server
2. **Update .env**: Add `MCP_MODE=http` and `MCP_HTTP_URL` for HTTP testing
3. **Verify Endpoints**: Ensure MCP server provides expected REST API
4. **Production Deployment**: Choose appropriate mode based on infrastructure

---

**Implementation Date:** October 14, 2025  
**Status:** Complete ✅  
**Backward Compatibility:** Maintained  
**New Features:** HTTP MCP communication mode
