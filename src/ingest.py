"""
Chunk raw documents and embed them into a local Chroma vector store.

Usage:
    python src/ingest.py
"""
import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "nutrition_docs"

CHUNK_SIZE = 800       # characters, adjust after inspecting typical fact-sheet length
CHUNK_OVERLAP = 100


def load_documents() -> list[dict]:
    docs = []
    for json_path in RAW_DIR.rglob("*.json"):
        docs.append(json.loads(json_path.read_text(encoding="utf-8")))
    return docs


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Simple sliding-window chunker. Swap for heading-aware chunking if the
    source has clear section structure (WHO fact sheets often do — see README)."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


def main():
    documents = load_documents()
    print(f"Loaded {len(documents)} source documents")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=embed_fn
    )

    ids, texts, metadatas = [], [], []
    processed = []

    for doc in documents:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['slug']}-{i}"
            ids.append(chunk_id)
            texts.append(chunk)
            metadatas.append({
                "title": doc["title"],
                "url": doc["url"],
                "source": doc["source"],
                "category": doc["category"],
                "chunk_index": i,
            })
        processed.append({"slug": doc["slug"], "num_chunks": len(chunks)})

    if ids:
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)

    (PROCESSED_DIR / "ingest_summary.json").write_text(
        json.dumps(processed, indent=2), encoding="utf-8"
    )
    print(f"Embedded {len(ids)} chunks into Chroma collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
