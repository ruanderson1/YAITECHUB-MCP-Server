import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = PROJECT_ROOT / "app" / "data" / "inventory.json"


def test_stdio_inventory_flow() -> None:
    async def run_test() -> None:
        inventory: list[dict[str, Any]] = json.loads(
            INVENTORY_PATH.read_text(encoding="utf-8")
        )
        product = inventory[0]
        transport = StdioTransport(
            command=sys.executable,
            args=["-m", "app.server", "--transport", "stdio"],
            cwd=str(PROJECT_ROOT),
            keep_alive=False,
        )

        async with Client(transport) as client:
            tools = await client.list_tools()
            tool_names = {tool.name for tool in tools}

            assert {"get_product", "get_stock"} <= tool_names

            result = await client.call_tool("get_stock", {"name": product["name"]})

            assert result.data.quantity == product["quantity"]

    asyncio.run(run_test())
