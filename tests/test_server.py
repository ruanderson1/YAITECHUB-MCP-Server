import asyncio
import sys
from unittest.mock import Mock

import pytest

from app.server import SSE_HOST, SSE_PORT, main, mcp


def test_inventory_tools_are_registered() -> None:
    get_product_tool = asyncio.run(mcp.get_tool("get_product"))
    get_stock_tool = asyncio.run(mcp.get_tool("get_stock"))

    assert get_product_tool is not None
    assert get_stock_tool is not None


def test_server_runs_sse_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock()
    monkeypatch.setattr(mcp, "run", run)
    monkeypatch.setattr(sys, "argv", ["app.server"])

    main()

    run.assert_called_once_with(transport="sse", host=SSE_HOST, port=SSE_PORT)


def test_server_runs_with_stdio_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = Mock()
    monkeypatch.setattr(mcp, "run", run)
    monkeypatch.setattr(sys, "argv", ["app.server", "--transport", "stdio"])

    main()

    run.assert_called_once_with(transport="stdio")


def test_server_runs_sse_on_configured_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = Mock()
    monkeypatch.setattr(mcp, "run", run)
    monkeypatch.setattr(sys, "argv", ["app.server", "--transport", "sse"])

    main()

    run.assert_called_once_with(transport="sse", host=SSE_HOST, port=SSE_PORT)
