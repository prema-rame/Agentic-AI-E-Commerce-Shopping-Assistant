"""SQLite-backed inventory availability checks."""

from pathlib import Path
from typing import Any

from database import check_inventory as _check_inventory


def check_inventory(product_id: str, database_path: str | Path | None = None) -> dict[str, Any]:
    return _check_inventory(product_id, database_path)
