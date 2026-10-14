"""LangGraph orchestration for the multi-agent shopping workflow."""

import logging
from typing import Any

from agents.budget_agent import budget_agent
from agents.comparison_agent import comparison_agent
from agents.faq_agent import faq_agent
from agents.inventory_agent import inventory_agent
from agents.recommendation_agent import recommendation_agent
from agents.search_agent import extract_requirements, search_agent
from database import check_inventory
from state import ShoppingState
from tools.cart_tool import add_to_cart

logger = logging.getLogger(__name__)


def search_products_node(state: ShoppingState) -> dict[str, Any]:
    requirements = extract_requirements(state.get("customer_requirement", ""), float(state.get("budget", 0)), state.get("preferred_ram", ""), state.get("category", "Laptop"))
    try:
        products = search_agent(requirements)
    except Exception as error:
        logger.exception("Product search failed")
        return {**requirements, "products": [], "error": str(error), "status": "error"}
    return {**requirements, "products": products, "status": "search_complete" if products else "no_products"}


def compare_products_node(state: ShoppingState) -> dict[str, Any]:
    return {"comparison": comparison_agent(state.get("products", []))}


def check_inventory_node(state: ShoppingState) -> dict[str, Any]:
    from agents.inventory_agent import inventory_agent
    inventory = inventory_agent(state.get("products", []))
    available = [product for product in state.get("products", []) if inventory.get(product["product_id"], {}).get("available")]
    return {"inventory": inventory, "available_products": available}


def validate_budget_node(state: ShoppingState) -> dict[str, Any]:
    eligible = budget_agent(state.get("available_products", []), float(state.get("budget", 0)))
    status = "ready_to_recommend" if eligible else "out_of_stock" if state.get("products") else "no_products"
    return {"eligible_products": eligible, "status": status}


def retrieve_faqs_node(state: ShoppingState) -> dict[str, Any]:
    product = state["eligible_products"][0]
    question = f"{state.get('customer_requirement', '')} {product.get('product_name', '')} programming machine learning battery warranty"
    result = faq_agent(question)
    return {"faq_answers": [result]}


def generate_recommendation_node(state: ShoppingState) -> dict[str, Any]:
    requirements = {key: state.get(key, "") for key in ("category", "preferred_ram", "use_case")}
    product, reviews, reason = recommendation_agent(state.get("eligible_products", []), requirements)
    status = "awaiting_confirmation" if product else state.get("status", "no_products")
    return {"recommended_product": product, "review_analysis": reviews, "recommendation_reason": reason, "status": status, "confirmation_requested": bool(product)}


def cart_confirmation_node(state: ShoppingState) -> dict[str, Any]:
    if not state.get("confirmed", False):
        return {"status": "awaiting_confirmation", "cart": None}
    return {"selected_product_id": state.get("selected_product_id") or (state.get("recommended_product") or {}).get("product_id", "")}


def add_to_cart_node(state: ShoppingState) -> dict[str, Any]:
    selected_id = state.get("selected_product_id", "")
    product = next((item for item in state.get("eligible_products", []) if item["product_id"] == selected_id), None)
    if not product:
        return {"status": "cart_error", "error": "Select an in-stock, within-budget product before adding to cart."}
    try:
        if not check_inventory(selected_id).get("available"):
            return {"status": "cart_error", "error": "This product is no longer in stock."}
        cart = add_to_cart(selected_id, confirmed=True, user_id=state.get("user_id", "guest"))
        return {"cart": cart, "status": "cart_created"}
    except Exception as error:
        logger.exception("Cart creation failed")
        return {"status": "cart_error", "error": str(error)}


def _after_search(state: ShoppingState) -> str:
    return "compare_products" if state.get("products") else "generate_recommendation"


def _after_budget(state: ShoppingState) -> str:
    return "retrieve_faqs" if state.get("eligible_products") else "generate_recommendation"


def _after_confirmation(state: ShoppingState) -> str:
    return "add_to_cart" if state.get("confirmed") else "__end__"


def build_graph():
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as error:
        raise RuntimeError("LangGraph is required. Install dependencies with `pip install -r requirements.txt`.") from error
    workflow = StateGraph(ShoppingState)
    workflow.add_node("search_products", search_products_node)
    workflow.add_node("compare_products", compare_products_node)
    workflow.add_node("check_inventory", check_inventory_node)
    workflow.add_node("validate_budget", validate_budget_node)
    workflow.add_node("retrieve_faqs", retrieve_faqs_node)
    workflow.add_node("generate_recommendation", generate_recommendation_node)
    workflow.add_node("cart_confirmation", cart_confirmation_node)
    workflow.add_node("add_to_cart", add_to_cart_node)
    workflow.add_edge(START, "search_products")
    workflow.add_conditional_edges("search_products", _after_search, {"compare_products": "compare_products", "generate_recommendation": "generate_recommendation"})
    workflow.add_edge("compare_products", "check_inventory")
    workflow.add_edge("check_inventory", "validate_budget")
    workflow.add_conditional_edges("validate_budget", _after_budget, {"retrieve_faqs": "retrieve_faqs", "generate_recommendation": "generate_recommendation"})
    workflow.add_edge("retrieve_faqs", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "cart_confirmation")
    workflow.add_conditional_edges("cart_confirmation", _after_confirmation, {"add_to_cart": "add_to_cart", "__end__": END})
    workflow.add_edge("add_to_cart", END)
    return workflow.compile()


def run_shopping_workflow(state: ShoppingState) -> ShoppingState:
    return build_graph().invoke(state)
