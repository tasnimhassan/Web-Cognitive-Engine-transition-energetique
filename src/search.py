"""Etape 5 - Recherche semantique : question -> vecteur -> Top-K chunks (similarite cosinus)."""
from src import config


def search(question: str, k: int = config.TOP_K, min_score: float = config.MIN_SCORE) -> list[dict]:
    from src.embeddings import embed          # imports tardifs : modules lourds
    from src.vectorstore import get_collection

    col = get_collection()
    total = col.count()
    if total == 0:
        return []
    res = col.query(query_embeddings=embed([question]).tolist(), n_results=min(k, total),
                    include=["documents", "metadatas", "distances"])
    passages = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        score = round(1 - dist, 3)            # distance cosinus -> similarite cosinus
        if score >= min_score:
            passages.append({"score": score, "source_file": meta["source_file"], "title": meta.get("title", ""),
                             "page": meta["page"], "text": text})
    return passages                            # deja tries du plus proche au plus eloigne
