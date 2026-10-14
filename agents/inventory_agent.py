"""Inventory agent filters unavailable products and exposes stock counts."""

from pathlib import Path
from typing import Any

from tools.inventory_tool import check_inventory


def inventory_agent(products: list[dict[str, Any]], database_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    return {product["product_id"]: check_inventory(product["product_id"], database_path) for product in products}
