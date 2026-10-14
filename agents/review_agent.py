"""Customer review sentiment agent."""

from tools.review_tool import analyze_reviews


def review_agent(product: dict, use_case: str = "") -> dict:
    return analyze_reviews(product, use_case)
