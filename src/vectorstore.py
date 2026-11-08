"""Etape 4 - Base vectorielle ChromaDB persistante."""
import chromadb

from src.config import CHROMA_DIR, COLLECTION_NAME

_client = None


def get_collection(reset: bool = False):
    global _client
    if _client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if reset:
        try:
            _client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return _client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def add_chunks(collection, chunks: list[dict], vectors, batch: int = 256) -> None:
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        collection.upsert(ids=[c["id"] for c in part],
                          documents=[c["text"] for c in part],
                          metadatas=[c["metadata"] for c in part],
                          embeddings=[v.tolist() for v in vectors[i:i + batch]])


def stats() -> dict:
    col = get_collection()
    data = col.get(include=["metadatas"])
    files = sorted({m["source_file"] for m in data["metadatas"]})
    return {"collection": COLLECTION_NAME, "n_chunks": col.count(), "n_documents": len(files), "documents": files}
