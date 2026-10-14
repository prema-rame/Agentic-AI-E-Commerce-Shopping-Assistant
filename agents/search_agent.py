"""Natural-language requirement extraction and product search agent."""

import re
from typing import Any

from tools.product_search_tool import search_products


def extract_requirements(request: str, budget: float, preferred_ram: str = "", category: str = "Laptop") -> dict[str, Any]:
    if not request or not request.strip():
        raise ValueError("Shopping requirement cannot be empty")
    if budget <= 0:
        raise ValueError("Budget must be greater than zero")
    text = request.strip()
    lowered = text.casefold()
    category_terms = {"mobile": "Mobile", "phone": "Mobile", "smartphone": "Mobile", "tablet": "Tablet", "laptop": "Laptop"}
    inferred_category = next((value for term, value in category_terms.items() if term in lowered), category)
    ram_match = re.search(r"\b(\d+)\s*gb\s*(?:ram)?\b", text, re.IGNORECASE)
    if ram_match and not preferred_ram:
        preferred_ram = f"{ram_match.group(1)}GB"
    use_case = text
    return {"customer_requirement": text, "budget": float(budget), "preferred_ram": preferred_ram, "category": inferred_category, "use_case": use_case}


def search_agent(requirements: dict[str, Any]) -> list[dict[str, Any]]:
    return search_products(
        budget=float(requirements["budget"]),
        use_case=str(requirements.get("use_case", "")),
        preferred_ram=str(requirements.get("preferred_ram", "")),
        category=str(requirements.get("category", "Laptop")),
    )
