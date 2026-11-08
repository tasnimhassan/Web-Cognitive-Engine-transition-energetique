"""Etape 7 - Analyse exploratoire du corpus (statistiques pour le tableau de bord)."""
import json
import re
from collections import Counter

from src.config import PROCESSED_DIR

# Famille de source deduite du nom de fichier
FAMILIES = [("banque_des_territoires", "Presse spécialisée"), ("rte_", "RTE"), ("ademe_", "ADEME"),
            ("negawatt_", "Associations"), ("sdlc_", "Associations"), ("ritimo_", "Associations"),
            ("attac_", "Associations"), ("france_renouvelables", "Filières EnR"), ("ser_", "Filières EnR"),
            ("ufe_", "Filières EnR"), ("ppe3_", "Analyses PPE3"), ("cour_comptes", "Cour des comptes"),
            ("an_", "Assemblée nationale"), ("wiki_", "Wikipédia"), ("cde_", "Presse spécialisée")]

# Mots-cles strategiques de la transition energetique (expressions regulieres)
KEYWORDS = {
    "nucléaire": r"nucl[ée]aire", "éolien": r"[ée]olien", "solaire": r"solaire|photovolta",
    "hydraulique": r"hydrauliq|hydro[ée]lectri|barrage", "renouvelable": r"renouvelable|\bEnR\b",
    "électrification": r"[ée]lectrification|[ée]lectrifier", "PPE": r"\bPPE\d?\b",
    "stockage": r"stockage|batteries?", "hydrogène": r"hydrog[èe]ne", "biomasse": r"biomasse|biogaz|biom[ée]thane",
    "prix et aides": r"\bprix\b|\bco[uû]ts?\b|subvention|\baides?\b", "climat": r"climat|carbone|CO2|[ée]missions",
    "sobriété": r"sobri[ée]t[ée]|efficacit[ée] [ée]nerg[ée]tique",
}
_KW_RE = {k: re.compile(p, re.IGNORECASE) for k, p in KEYWORDS.items()}


def family_of(filename: str) -> str:
    for key, name in FAMILIES:
        if (key in filename) if key == "banque_des_territoires" else filename.startswith(key):
            return name
    return "Autres"


def count_keywords(text: str) -> dict:
    return {k: len(rx.findall(text)) for k, rx in _KW_RE.items()}


def histogram(values: list[int], width: int = 50, top: int = 550) -> list[dict]:
    bins = [0] * (top // width + 1)
    for v in values:
        bins[min(v // width, len(bins) - 1)] += 1
    out = []
    for i, c in enumerate(bins):
        label = f"{i * width}+" if i == len(bins) - 1 else f"{i * width}-{(i + 1) * width - 1}"
        out.append({"label": label, "value": c})
    return out


def pca_2d(vectors):
    """Projection en 2 dimensions (ACP) pour visualiser les passages. Retourne (points 0..1, variance expliquee)."""
    import numpy as np
    X = np.asarray(vectors, dtype=float)
    X = X - X.mean(axis=0)
    _, S, Vt = np.linalg.svd(X, full_matrices=False)
    P = X @ Vt[:2].T
    mn, mx = P.min(axis=0), P.max(axis=0)
    P = (P - mn) / np.where(mx - mn == 0, 1, mx - mn)
    var = (S ** 2) / (S ** 2).sum()
    return P.round(4).tolist(), [round(float(v), 3) for v in var[:2]]


def build_analytics(docs: list[dict], chunks: list[dict], vectors=None) -> dict:
    """docs : {source_file, format, n_chars, text} ; chunks : {text, source_file, page}."""
    n_chars = sum(d["n_chars"] for d in docs)
    fmt_count, fmt_chars, fam_count = Counter(), Counter(), Counter()
    for d in docs:
        fmt_count[d["format"].upper()] += 1
        fmt_chars[d["format"].upper()] += d["n_chars"]
        fam_count[family_of(d["source_file"])] += 1

    per_doc = {d["source_file"]: count_keywords(d["text"]) for d in docs}
    keywords = []
    for k in KEYWORDS:
        by_doc = sorted(((f, c[k]) for f, c in per_doc.items() if c[k] > 0), key=lambda x: -x[1])
        keywords.append({"label": k, "value": sum(c for _, c in by_doc), "docs": len(by_doc),
                         "top": [{"file": f, "count": c} for f, c in by_doc[:8]]})
    keywords.sort(key=lambda x: -x["value"])

    sizes = [len(c["text"]) for c in chunks]
    result = {
        "totals": {"documents": len(docs), "chunks": len(chunks), "chars": n_chars,
                   "avg_chunk": round(sum(sizes) / len(sizes), 1) if sizes else 0},
        "formats": [{"label": k, "value": v, "chars": fmt_chars[k]} for k, v in fmt_count.most_common()],
        "families": [{"label": k, "value": v} for k, v in fam_count.most_common()],
        "volume": [{"label": d["source_file"], "value": d["n_chars"]}
                   for d in sorted(docs, key=lambda d: -d["n_chars"])[:12]],
        "chunk_hist": histogram(sizes),
        "keywords": keywords,
        "pca": None,
    }
    if vectors is not None and len(vectors) >= 3:
        pts, var = pca_2d(vectors)
        result["pca"] = {"variance": var, "points": [
            {"x": p[0], "y": p[1], "family": family_of(c["source_file"]), "file": c["source_file"], "page": c["page"]}
            for p, c in zip(pts, chunks)]}
    return result


_cache: dict = {}


def clear_cache():
    _cache.clear()


def get_analytics(refresh: bool = False) -> dict:
    if _cache and not refresh:
        return _cache["data"]
    from src.vectorstore import get_collection
    docs = []
    for f in sorted(PROCESSED_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        docs.append({"source_file": d["source_file"], "format": d["format"], "n_chars": d["n_chars"],
                     "text": " ".join(p["text"] for p in d["pages"])})
    data = get_collection().get(include=["documents", "metadatas", "embeddings"])
    chunks = [{"text": t, "source_file": m["source_file"], "page": m["page"]}
              for t, m in zip(data["documents"], data["metadatas"])]
    emb = data.get("embeddings")
    result = build_analytics(docs, chunks, emb if emb is not None and len(emb) else None)
    _cache["data"] = result
    return result
