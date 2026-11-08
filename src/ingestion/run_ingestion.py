"""Etape 2 - Pipeline d'ingestion : data/raw -> data/processed (JSON + Markdown)."""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from src.config import PROCESSED_DIR, RAW_DIR
from src.ingestion.cleaning import clean_text
from src.ingestion.parsers import PARSERS

log = logging.getLogger("ingestion")


def doc_id_for(path: Path) -> str:
    return hashlib.md5(path.name.encode()).hexdigest()[:10]


def ingest_file(path: Path) -> dict:
    parser = PARSERS[path.suffix.lower()]
    title, pages = parser(path)
    cleaned = [{"page": p["page"], "text": clean_text(p["text"])} for p in pages]
    cleaned = [p for p in cleaned if p["text"]]
    return {
        "doc_id": doc_id_for(path),
        "source_file": path.name,
        "format": path.suffix.lower().lstrip("."),
        "title": (title or path.stem).strip(),
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
        "n_pages": len(cleaned),
        "n_chars": sum(len(p["text"]) for p in cleaned),
        "pages": cleaned,
    }


def to_markdown(doc: dict) -> str:
    head = (f"---\ntitle: {doc['title']}\nsource_file: {doc['source_file']}\n"
            f"format: {doc['format']}\ningested_at: {doc['ingested_at']}\n---\n\n")
    body = "\n\n".join(f"<!-- page {p['page']} -->\n{p['text']}" for p in doc["pages"])
    return head + body + "\n"


def run_ingestion(raw_dir: Path = RAW_DIR, out_dir: Path = PROCESSED_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    ok, errors, empty = [], [], []
    for path in sorted(raw_dir.iterdir()):
        if path.suffix.lower() not in PARSERS:
            continue
        try:
            doc = ingest_file(path)
            if doc["n_chars"] == 0:
                empty.append(path.name)      # ex: PDF scanne sans couche texte
                continue
            (out_dir / f"{path.stem}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            (out_dir / f"{path.stem}.md").write_text(to_markdown(doc), encoding="utf-8")
            ok.append({"file": path.name, "format": doc["format"], "pages": doc["n_pages"], "chars": doc["n_chars"]})
        except Exception as e:                 # un fichier casse ne doit pas bloquer le corpus
            log.exception("Echec sur %s", path.name)
            errors.append({"file": path.name, "error": str(e)})
    return {"processed": len(ok), "empty": empty, "errors": errors, "documents": ok}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = run_ingestion()
    print(f"{r['processed']} documents traites, {len(r['empty'])} vides, {len(r['errors'])} erreurs")
    for e in r["errors"]:
        print("  ERREUR", e)
