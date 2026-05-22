"""
MCP Server component that provides web scrapping tools via FastMCP.
"""
import os
import sys
from typing import Literal

from fastmcp import FastMCP
from bs4 import BeautifulSoup
import requests

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

mcp = FastMCP("stocks")


@mcp.tool()
def web_scrapping(url: str) -> dict:
    """
    Web scraping related to the url.

    Args:
        url: User url

    Returns:
        Dictionary containing web scraping results
    """
    logger.info(f"Web scraping related to the url {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements to clean text
        for script in soup(["script", "style"]):
            script.decompose()

        # Get plain text
        text = soup.get_text()

        # Clean text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        scrape_result = {
            "success": True,
            "markdown": clean_text,
            "html": html_content[:20000]  # Truncate html to avoid token limits
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        scrape_result = {
            "success": False,
            "error": str(e),
            "markdown": "",
            "html": ""
        }

    logger.info(f"Web scraping result: {scrape_result}")

    return scrape_result


def run_server(host: str = "127.0.0.1", port: int = 7860, transport: Literal["stdio", "sse", "streamable-http"] = "sse") -> None:
    """
    Run the MCP mcp_server with specified transport, host and port.
    
    Args:
        host: Host address to bind the mcp_server
        port: Port number to listen on
        transport: Transport protocol ("sse" or "stdio")
    """
    logger.info(f"Starting MCP mcp_server on {host}:{port} with {transport} transport...")
    mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    run_server()
