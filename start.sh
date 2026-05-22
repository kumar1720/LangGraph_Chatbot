#!/bin/sh

# Start Search MCP Server in the background
echo "Starting Search MCP Server on port 7861..."
python -m app.mcp_server.search_server > search_server.log 2>&1 &

# Start Web Scraping MCP Server in the background
echo "Starting Web Scraping MCP Server on port 7860..."
python -m app.mcp_server.web_scrapping_server > scraping_server.log 2>&1 &

# Start FastAPI server in the foreground
echo "Starting FastAPI Server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
