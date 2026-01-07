#!/bin/bash
# Run local MCP gateway server and test showcase against it

set -e  # Exit on error

echo "==================================================================="
echo "Starting Local MCP Gateway Server for Showcase Testing"
echo "==================================================================="

# Start the gateway server in the background
echo "Starting gateway server on port 8000..."
uv run fastmcp run src/lifesciences_mcp/servers/gateway.py --port 8000 &
GATEWAY_PID=$!

echo "Gateway server PID: $GATEWAY_PID"
echo "Waiting 5 seconds for server to initialize..."
sleep 5

# Test if server is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Gateway server is running"
else
    echo "⚠️  Health check endpoint not available (may be normal for MCP servers)"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "==================================================================="
    echo "Shutting down gateway server..."
    echo "==================================================================="
    kill $GATEWAY_PID 2>/dev/null || true
    wait $GATEWAY_PID 2>/dev/null || true
    echo "✅ Server stopped"
}

trap cleanup EXIT INT TERM

# Run the showcase against local endpoint
echo ""
echo "==================================================================="
echo "Running Showcase Against Local Gateway"
echo "==================================================================="
export MCP_ENDPOINT="http://localhost:8000/mcp"
uv run python scripts/showcase_nsclc_v2_fastmcp.py

echo ""
echo "==================================================================="
echo "Showcase Complete!"
echo "==================================================================="
