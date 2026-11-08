"""Etape 4 - Orchestration : processed JSON -> chunks -> embeddings -> ChromaDB."""
import json
import time
from pathlib import Path

from src.chunking import chunk_document
from src.config import CHUNK_OVERLAP, CHUNK_SIZE, PROCESSED_DIR
from src.embeddings import embed
from src.vectorstore import add_chunks, get_collection


def index_directory(processed_dir: Path = PROCESSED_DIR, reset: bool = True,
                    chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> dict:
    t0 = time.time()
    col = get_collection(reset=reset)
    all_chunks, n_docs = [], 0
    for f in sorted(processed_dir.glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        all_chunks.extend(chunk_document(doc, chunk_size, overlap))
        n_docs += 1
    if all_chunks:
        vectors = embed([c["text"] for c in all_chunks])
        add_chunks(col, all_chunks, vectors)
    lengths = [len(c["text"]) for c in all_chunks] or [0]
    return {"status": "ok", "documents_indexed": n_docs, "chunks_indexed": len(all_chunks),
            "avg_chunk_chars": round(sum(lengths) / len(lengths), 1),
            "chunk_size": chunk_size, "overlap": overlap,
            "total_in_db": col.count(), "duration_s": round(time.time() - t0, 2)}
