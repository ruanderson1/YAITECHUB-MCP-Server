import json
from pathlib import Path
from typing import Any

import pytest

import app.tools.inventory as inventory_tools
from app.services.inventory_service import InventoryService


@pytest.fixture
def inventory_service(tmp_path: Path) -> InventoryService:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            [
                {"name": "Notebook", "quantity": 8, "price": 3499.90},
                {"name": "Mouse", "quantity": 25, "price": 89.90},
            ]
        ),
        encoding="utf-8",
    )
    return InventoryService(inventory_path)


@pytest.fixture(autouse=True)
def use_test_inventory(
    monkeypatch: pytest.MonkeyPatch,
    inventory_service: InventoryService,
) -> None:
    monkeypatch.setattr(inventory_tools, "_inventory_service", inventory_service)


def test_get_product_returns_complete_product() -> None:
    result = inventory_tools.get_product("notebook")

    assert result.model_dump() == {
        "name": "Notebook",
        "quantity": 8,
        "price": 3499.90,
    }


def test_get_stock_returns_quantity() -> None:
    result = inventory_tools.get_stock("  MOUSE  ")

    assert result.model_dump() == {"quantity": 25}


def test_get_product_returns_predictable_error_when_missing() -> None:
    result = inventory_tools.get_product("Monitor")

    assert result.model_dump() == {
        "error": "product_not_found",
        "message": "Product not found: Monitor",
    }


def test_get_stock_returns_predictable_error_when_missing() -> None:
    result = inventory_tools.get_stock("Monitor")

    assert result.model_dump() == {
        "error": "product_not_found",
        "message": "Product not found: Monitor",
    }


@pytest.mark.parametrize(
    "tool", [inventory_tools.get_product, inventory_tools.get_stock]
)
def test_tools_reject_empty_product_name(tool: Any) -> None:
    with pytest.raises(ValueError, match="Product name must not be empty"):
        tool("   ")


@pytest.mark.parametrize(
    "tool", [inventory_tools.get_product, inventory_tools.get_stock]
)
def test_tools_reject_non_string_product_name(tool: Any) -> None:
    with pytest.raises(TypeError, match="Product name must be a string"):
        tool(123)
