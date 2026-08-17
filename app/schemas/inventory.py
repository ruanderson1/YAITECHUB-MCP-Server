"""Pydantic models that define the inventory data contracts."""

from typing import Annotated

from pydantic import BaseModel, Field


class Product(BaseModel):
    """Complete, validated representation of an inventory product."""

    name: Annotated[str, Field(min_length=1)]
    quantity: Annotated[int, Field(ge=0)]
    price: Annotated[float, Field(ge=0)]


class Stock(BaseModel):
    """Validated stock quantity returned by the stock lookup tool."""

    quantity: Annotated[int, Field(ge=0)]
