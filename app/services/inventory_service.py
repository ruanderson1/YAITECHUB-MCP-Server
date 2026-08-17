"""Load inventory data and implement product lookup business rules."""

import json
from pathlib import Path

from app.schemas.inventory import Product, Stock


class ProductNotFoundError(LookupError):
    """Raised when a product is not present in the inventory."""


class InventoryService:
    """Provide read-only, case-insensitive access to an inventory file."""

    def __init__(self, inventory_path: Path | None = None) -> None:
        """Load and validate products from ``inventory_path`` or packaged data."""
        path = inventory_path or Path(__file__).parents[1] / "data" / "inventory.json"
        self._products = self._load_products(path)

    @staticmethod
    def _load_products(path: Path) -> list[Product]:
        """Deserialize an inventory JSON file into validated product models."""
        with path.open(encoding="utf-8") as inventory_file:
            data = json.load(inventory_file)

        return [Product.model_validate(item) for item in data]

    def get_product(self, name: str) -> Product:
        """Find a product by name, ignoring case and surrounding whitespace."""
        stripped_name = name.strip()
        normalized_name = stripped_name.casefold()

        for product in self._products:
            if product.name.casefold() == normalized_name:
                return product

        raise ProductNotFoundError(f"Product not found: {stripped_name}")

    def get_stock(self, name: str) -> Stock:
        """Return only the current quantity for a named product."""
        product = self.get_product(name)
        return Stock(quantity=product.quantity)
