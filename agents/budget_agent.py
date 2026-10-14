"""Budget validation agent."""

from tools.budget_tool import validate_budget


def budget_agent(products: list[dict], budget: float) -> list[dict]:
    return [product for product in products if validate_budget(product, budget)["within_budget"]]
