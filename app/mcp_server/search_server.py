"""
MCP Server component that provides web search tools via FastMCP.
"""
import os
import sys
from typing import Literal

from fastmcp import FastMCP
from duckduckgo_search import DDGS

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

mcp = FastMCP("search")


@mcp.tool()
def search(query: str) -> dict:
    """
    Search related to the query.

    Args:
        query: User query

    Returns:
        Dictionary containing search results
    """
    logger.info(f"Fetched news for {query}")

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
        formatted_results = [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "content": r.get("body", "")
            }
            for r in results
        ]
        response = {"results": formatted_results}

    logger.info(f"Fetched results for {response}")

    return response



def run_server(host: str = "127.0.0.1", port: int = 7861, transport: Literal["stdio", "sse", "streamable-http"] = "sse") -> None:
    """
    Run the MCP mcp_server with specified transport, host, and port.

    Args:
        host: Host address to bind the mcp_server
        port: Port number to listen on
        transport: Transport protocol ("sse" or "stdio")
    """
    logger.info(f"Starting MCP mcp_server on {host}:{port} with {transport} transport...")
    mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    run_server()
