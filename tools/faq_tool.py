"""FAQ retrieval using persistent Chroma embeddings with an offline fallback."""

import hashlib
import logging
import math
import re
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)
_VECTOR_SIZE = 384


def _embedding(text: str) -> list[float]:
    vector = [0.0] * _VECTOR_SIZE
    for token in re.findall(r"[a-z0-9]+", text.casefold()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % _VECTOR_SIZE
        vector[index] += 1.0 if digest[4] % 2 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _load_chunks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]


def _chroma_search(question: str, chunks: list[str], persist_path: Path, top_k: int) -> list[str]:
    import chromadb

    client = chromadb.PersistentClient(path=str(persist_path))
    collection = client.get_or_create_collection("product_faqs", metadata={"hnsw:space": "cosine"})
    ids = [f"faq-{index}" for index in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks, embeddings=[_embedding(chunk) for chunk in chunks])
    results = collection.query(query_embeddings=[_embedding(question)], n_results=min(top_k, len(chunks)))
    return (results.get("documents") or [[]])[0]


def _keyword_search(question: str, chunks: list[str], top_k: int) -> list[str]:
    terms = set(re.findall(r"[a-z0-9]+", question.casefold()))
    ranked = sorted(chunks, key=lambda chunk: len(terms & set(re.findall(r"[a-z0-9]+", chunk.casefold()))), reverse=True)
    return ranked[:top_k]


def retrieve_faq(question: str, faq_path: str | Path | None = None, top_k: int = 3) -> dict[str, Any]:
    path = Path(faq_path or settings.faq_path)
    if not path.exists():
        return {"answer": "FAQ information is currently unavailable.", "sources": [], "error": "FAQ file not found"}
    try:
        chunks = _load_chunks(path)
        try:
            relevant = _chroma_search(question, chunks, settings.chroma_path, top_k)
            source = "chroma"
        except Exception:
            logger.exception("Chroma retrieval failed; using keyword FAQ matching")
            relevant = _keyword_search(question, chunks, top_k)
            source = "keyword fallback"
        context = "\n".join(relevant)
        answer = context
        if settings.openai_api_key and context:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage, SystemMessage
                response = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=settings.openai_api_key).invoke([
                    SystemMessage(content="Answer only from the supplied product FAQ context. State when the context does not contain the answer."),
                    HumanMessage(content=f"FAQ context:\n{context}\n\nQuestion: {question}"),
                ])
                answer = str(response.content)
            except Exception:
                logger.exception("LLM FAQ answer failed; returning retrieved FAQ excerpts")
        return {"answer": answer, "sources": relevant, "retrieval": source}
    except Exception as error:
        logger.exception("FAQ retrieval failed")
        return {"answer": "FAQ information could not be retrieved right now.", "sources": [], "error": str(error)}
