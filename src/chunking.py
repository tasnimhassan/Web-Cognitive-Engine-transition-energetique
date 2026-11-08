"""Etape 3 - Chunking avec chevauchement, coupe aux frontieres de phrases/mots."""
from src.config import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if overlap >= size:
        raise ValueError("overlap doit etre < size")
    text = text.strip()
    n, start, chunks = len(text), 0, []
    while start < n:
        end = min(start + size, n)
        if end < n:
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind("? "), window.rfind("! "), window.rfind("\n"))
            if cut < size * 0.5:
                cut = window.rfind(" ")
            if cut > 0:
                end = start + cut + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        nxt = end - overlap
        if nxt <= start:
            nxt = end
        else:                                  # on se recale sur un debut de mot
            sp = text.find(" ", nxt, end)
            if sp != -1:
                nxt = sp + 1
        start = nxt
    return chunks


def chunk_document(doc: dict, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Decoupe page par page pour conserver le numero de page dans les metadonnees."""
    out = []
    for page in doc["pages"]:
        for i, c in enumerate(chunk_text(page["text"], size, overlap)):
            out.append({
                "id": f"{doc['doc_id']}::p{page['page']}::c{i}",
                "text": c,
                "metadata": {"source_file": doc["source_file"], "title": doc["title"],
                             "format": doc["format"], "page": page["page"],
                             "chunk_index": i, "doc_id": doc["doc_id"]},
            })
    return out
