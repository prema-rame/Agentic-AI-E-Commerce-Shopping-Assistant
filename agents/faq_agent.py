"""FAQ RAG agent."""

from tools.faq_tool import retrieve_faq


def faq_agent(question: str) -> dict:
    return retrieve_faq(question)
