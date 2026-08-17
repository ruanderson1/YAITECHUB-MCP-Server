"""Configure and run the Inventory MCP server."""

import argparse

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from app.tools.inventory import get_product, get_stock

SSE_HOST = "127.0.0.1"
SSE_PORT = 8000

mcp = FastMCP("Inventory MCP")

mcp.tool(
    get_product,
    description=(
        "Use this tool to retrieve the complete data of a product by name, "
        "including its price and stock quantity."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
)
mcp.tool(
    get_stock,
    description=(
        "Use this tool to retrieve only the current stock quantity of a product "
        "by name."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
)


def main() -> None:
    """Parse command-line options and run the selected MCP transport."""
    parser = argparse.ArgumentParser(description="Run the inventory MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse"),
        default="sse",
        help="MCP transport to use (default: sse).",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=SSE_HOST, port=SSE_PORT)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
