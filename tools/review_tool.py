"""Customer review sentiment and product suitability scoring."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)
POSITIVE = {"good", "great", "excellent", "strong", "love", "fast", "reliable", "comfortable", "praise", "popular", "responsive", "long"}
NEGATIVE = {"poor", "bad", "short", "limited", "slow", "noise", "noisy", "mixed", "weak", "average", "concern", "criticism", "issue"}


def analyze_reviews(product: dict[str, Any], use_case: str = "") -> dict[str, Any]:
    text = str(product.get("review_summary", "")).strip()
    if not text:
        return {"sentiment": "unknown", "score": 0.0, "summary": "No review summary is available."}
    try:
        from config import settings
        if settings.openai_api_key:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            response = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=settings.openai_api_key).invoke([
                SystemMessage(content="Analyze this customer review summary. Return concise JSON with sentiment (positive, mixed, or negative), score from 0 to 1, and one-sentence summary. Do not infer unsupported facts."),
                HumanMessage(content=f"Use case: {use_case}\nReview summary: {text}"),
            ])
            import json
            result = json.loads(response.content)
            return {"sentiment": result["sentiment"], "score": float(result["score"]), "summary": str(result["summary"])}
    except Exception:
        logger.exception("LLM review analysis unavailable; using local sentiment scoring")
    tokens = re.findall(r"[a-z]+", text.casefold())
    positive = sum(token in POSITIVE for token in tokens)
    negative = sum(token in NEGATIVE for token in tokens)
    score = (positive - negative) / max(positive + negative, 1)
    sentiment = "positive" if score > 0.2 else "negative" if score < -0.2 else "mixed"
    return {"sentiment": sentiment, "score": round(score, 2), "summary": text}


def product_rating_score(product: dict[str, Any], requirements: dict[str, Any] | None = None) -> float:
    """Combine catalog rating, RAM fit, battery, and review sentiment into a 0-100 score."""
    requirements = requirements or {}
    rating_score = max(0.0, min(5.0, float(product.get("rating", 0)))) * 12
    desired = int(re.search(r"\d+", str(requirements.get("preferred_ram", ""))).group()) if re.search(r"\d+", str(requirements.get("preferred_ram", ""))) else 0
    actual_match = re.search(r"\d+", str(product.get("ram", "")))
    ram_score = 15 if desired and actual_match and int(actual_match.group()) >= desired else 7 if not desired else 0
    battery_match = re.search(r"\d+(?:\.\d+)?", str(product.get("battery_life", "")))
    battery_score = min(float(battery_match.group()), 10) if battery_match else 0
    sentiment = analyze_reviews(product, str(requirements.get("use_case", "")))
    review_score = max(0.0, min(1.0, (sentiment["score"] + 1) / 2)) * 10
    return round(min(100.0, rating_score + ram_score + battery_score + review_score), 2)
