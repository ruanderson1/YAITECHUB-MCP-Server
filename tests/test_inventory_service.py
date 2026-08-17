import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.inventory_service import InventoryService, ProductNotFoundError


@pytest.fixture
def inventory_path(tmp_path: Path) -> Path:
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps(
            [
                {"name": "Notebook", "quantity": 8, "price": 3499.90},
                {"name": "Mouse", "quantity": 25, "price": 89.90},
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def inventory_service(inventory_path: Path) -> InventoryService:
    return InventoryService(inventory_path)


def test_get_existing_product(inventory_service: InventoryService) -> None:
    product = inventory_service.get_product("Notebook")

    assert product.name == "Notebook"
    assert product.quantity == 8
    assert product.price == 3499.90


def test_get_product_ignores_surrounding_spaces(
    inventory_service: InventoryService,
) -> None:
    product = inventory_service.get_product("  Mouse  ")

    assert product.name == "Mouse"


def test_get_product_is_case_insensitive(inventory_service: InventoryService) -> None:
    product = inventory_service.get_product("notebook")

    assert product.name == "Notebook"


def test_get_missing_product(inventory_service: InventoryService) -> None:
    with pytest.raises(ProductNotFoundError, match="Product not found: Monitor"):
        inventory_service.get_product("Monitor")


def test_get_stock(inventory_service: InventoryService) -> None:
    stock = inventory_service.get_stock("Mouse")

    assert stock.quantity == 25


def test_invalid_inventory_record_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid-inventory.json"
    path.write_text(
        json.dumps([{"name": "Mouse", "quantity": -1, "price": 89.90}]),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        InventoryService(path)
