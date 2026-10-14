"""Recommendation and customer review analysis agents."""

from typing import Any

from tools.review_tool import analyze_reviews, product_rating_score


def recommendation_agent(products: list[dict[str, Any]], requirements: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], str]:
    if not products:
        return None, {}, "No matching in-stock product satisfies the selected category and budget."
    analyses = {product["product_id"]: analyze_reviews(product, str(requirements.get("use_case", ""))) for product in products[:8]}
    ranked = sorted(products, key=lambda product: (
        product_rating_score(product, requirements),
        float(product.get("rating", 0)),
        -float(product.get("price", 0)),
    ), reverse=True)
    best = ranked[0]
    ram = str(best.get("ram", "unspecified RAM"))
    battery = str(best.get("battery_life", "unspecified battery life"))
    sentiment = analyses.get(best["product_id"], {}).get("sentiment", "mixed")
    reason = (
        f"{best['product_name']} best balances the requested {requirements.get('category', 'product').lower()} "
        f"requirements with {ram}, {battery} estimated battery life, a {best.get('rating', 0):.1f}/5 catalog rating, "
        f"and {sentiment} customer-review feedback. It is within budget and currently in stock."
    )
    best = dict(best)
    best["recommendation_score"] = product_rating_score(best, requirements)
    return best, analyses, reason
