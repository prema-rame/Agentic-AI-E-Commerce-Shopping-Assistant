"""Validate that a product does not exceed a customer's budget."""

from typing import Any


def validate_budget(product: dict[str, Any], budget: float) -> dict[str, Any]:
    if budget <= 0:
        raise ValueError("Budget must be greater than zero")
    price = float(product["price"])
    return {"within_budget": price <= budget, "price": price, "budget": float(budget), "difference": float(budget - price)}
