"""Confirmation-gated cart creation."""

from pathlib import Path
from typing import Any

from database import create_cart


def add_to_cart(product_id: str, confirmed: bool, user_id: str = "guest", quantity: int = 1, database_path: str | Path | None = None) -> dict[str, Any]:
    if not confirmed:
        raise PermissionError("Customer confirmation is required before adding to cart")
    return create_cart(product_id, user_id=user_id, quantity=quantity, database_path=database_path)
