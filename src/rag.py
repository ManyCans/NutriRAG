"""
Retrieval + generation over the nutrition document collection.
"""
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from src.observability import traced, new_request_id

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "nutrition_docs"

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME, embedding_function=_embed_fn
)


@traced("retrieve")
def retrieve(query: str, k: int = 3) -> list[dict]:
    """Return top-k chunks with their metadata for a query."""
    results = _collection.query(query_texts=[query], n_results=k)
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append({"text": doc, "metadata": meta, "distance": dist})
    return hits


@traced("build_context")
def build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a context block with source attribution."""
    parts = []
    for h in hits:
        parts.append(f"[Source: {h['metadata']['title']} — {h['metadata']['url']}]\n{h['text']}")
    return "\n\n---\n\n".join(parts)


SYSTEM_PROMPT = """You are a nutrition information assistant. Answer using ONLY
the provided context from public health sources (WHO, USDA). Always:
- Provide answer in professional manner
- If the context doesn't contain the answer, say so plainly instead of guessing
"""


def answer_query(query: str, llm_call_fn, k: int = 3, chat_history: list = []) -> dict:
    """
    llm_call_fn: a function(system_prompt, user_prompt, chat_history) -> str
    """
    new_request_id()
    hits = retrieve(query, k=k)
    print(f"Embedding retrieved hits: {hits}")
    context = build_context(hits)
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
    answer = llm_call_fn(SYSTEM_PROMPT, user_prompt, chat_history)
    return {
        "answer": answer,
        "sources": [h["metadata"]["url"] for h in hits],
    }
