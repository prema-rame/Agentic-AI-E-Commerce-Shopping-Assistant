"""Catalog search with deterministic budget, category, RAM, and use-case ranking."""

import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import settings


def _ram_gb(value: Any) -> int:
    match = re.search(r"(\d+)\s*gb", str(value), re.IGNORECASE)
    return int(match.group(1)) if match else 0


def search_products(
    budget: float,
    use_case: str = "",
    preferred_ram: str = "",
    category: str = "Laptop",
    catalog_path: str | Path | None = None,
    include_out_of_stock: bool = True,
) -> list[dict[str, Any]]:
    if budget <= 0:
        raise ValueError("Budget must be greater than zero")
    path = Path(catalog_path or settings.product_catalog_path)
    if not path.exists():
        raise FileNotFoundError(f"Product catalog not found: {path}")
    products = pd.read_csv(path).fillna("")
    if category:
        products = products[products["category"].str.casefold() == category.casefold()]
    products = products[pd.to_numeric(products["price"], errors="coerce") <= budget]
    if not include_out_of_stock:
        products = products[pd.to_numeric(products["stock"], errors="coerce") > 0]
    if products.empty:
        return []

    desired_ram = _ram_gb(preferred_ram)
    terms = {term.casefold() for term in re.findall(r"[a-zA-Z0-9]+", use_case) if len(term) > 2}

    def ranking(row: pd.Series) -> tuple[float, float, float]:
        ram = _ram_gb(row.get("ram", ""))
        ram_match = 1 if desired_ram and ram >= desired_ram else 0
        searchable = " ".join(str(row.get(field, "")) for field in ("product_name", "processor", "description", "review_summary")).casefold()
        relevance = sum(1 for term in terms if term in searchable)
        rating = float(row.get("rating", 0) or 0)
        return (ram_match, relevance, rating)

    records = products.to_dict(orient="records")
    records.sort(key=ranking, reverse=True)
    return records
