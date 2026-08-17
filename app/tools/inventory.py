"""Expose read-only inventory operations as MCP-compatible functions."""

from pydantic import BaseModel

from app.schemas.inventory import Product, Stock
from app.services.inventory_service import InventoryService, ProductNotFoundError


class ToolError(BaseModel):
    """Stable error payload returned for expected inventory lookup failures."""

    error: str
    message: str


def _validate_product_name(name: str) -> None:
    """Reject product names that cannot produce a meaningful lookup."""
    if not isinstance(name, str):
        raise TypeError("Product name must be a string")
    if not name.strip():
        raise ValueError("Product name must not be empty")


_inventory_service = InventoryService()


def get_product(name: str) -> Product | ToolError:
    """Return product details or a predictable not-found error payload."""
    _validate_product_name(name)

    try:
        return _inventory_service.get_product(name)
    except ProductNotFoundError as error:
        return ToolError(error="product_not_found", message=str(error))


def get_stock(name: str) -> Stock | ToolError:
    """Return the available quantity or a predictable not-found error payload."""
    _validate_product_name(name)

    try:
        return _inventory_service.get_stock(name)
    except ProductNotFoundError as error:
        return ToolError(error="product_not_found", message=str(error))
