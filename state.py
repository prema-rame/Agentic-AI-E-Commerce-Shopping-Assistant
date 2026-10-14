"""LangGraph state shared by shopping agents."""

from typing import Any, TypedDict


class ShoppingState(TypedDict, total=False):
    customer_requirement: str
    budget: float
    preferred_ram: str
    category: str
    use_case: str
    user_id: str
    products: list[dict[str, Any]]
    comparison: list[dict[str, Any]]
    inventory: dict[str, dict[str, Any]]
    eligible_products: list[dict[str, Any]]
    faq_answers: list[dict[str, str]]
    review_analysis: dict[str, dict[str, Any]]
    recommended_product: dict[str, Any] | None
    recommendation_reason: str
    confirmation_requested: bool
    confirmed: bool
    selected_product_id: str
    cart: dict[str, Any] | None
    error: str
    status: str
