"""Product comparison formatting for UI and report export."""

import pandas as pd

COMPARISON_FIELDS = {
    "Product": "product_name",
    "Brand": "brand",
    "Price (INR)": "price",
    "Processor": "processor",
    "RAM": "ram",
    "Storage": "storage",
    "Battery": "battery_life",
    "Rating": "rating",
    "Stock": "stock",
}


def compare_products(products: list[dict]) -> pd.DataFrame:
    if not products:
        return pd.DataFrame(columns=COMPARISON_FIELDS)
    missing = [field for field in ("product_name", "price") if any(field not in product for product in products)]
    if missing:
        raise ValueError(f"Products are missing required fields: {', '.join(missing)}")
    rows = [{label: product.get(key, "Not specified") for label, key in COMPARISON_FIELDS.items()} for product in products]
    return pd.DataFrame(rows)
