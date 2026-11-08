"""Telecharge les documents de corpus/sources.csv vers data/raw/.

- .pdf / .html : sauvegarde brute du fichier telecharge.
- .txt / .docx : la page web est telechargee, son texte principal est extrait,
  puis enregistre au format demande (conversion).
Usage : python -m scripts.fetch_corpus
"""
import csv
import sys
import tempfile
from pathlib import Path

import requests

from src.config import ROOT, RAW_DIR

HEADERS = {"User-Agent": "Mozilla/5.0 (projet universitaire WebCognitive; contact etudiant)"}


def html_to_text(content: bytes) -> tuple[str, str]:
    from src.ingestion.parsers import parse_html
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp.write(content)
    try:
        title, pages = parse_html(Path(tmp.name))
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    text = "\n".join(p["text"] for p in pages)
    return title, text


def save(dest: Path, content: bytes, url: str) -> None:
    ext = dest.suffix.lower()
    if ext in (".pdf", ".html", ".htm"):
        dest.write_bytes(content)
        return
    title, text = html_to_text(content)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if ext == ".txt":
        dest.write_text(f"{title}\nSource : {url}\n\n" + "\n".join(lines), encoding="utf-8")
    elif ext == ".docx":
        import docx
        d = docx.Document()
        d.core_properties.title = title
        d.add_heading(title, level=1)
        d.add_paragraph(f"Source : {url}")
        for l in lines:
            d.add_paragraph(l)
        d.save(str(dest))
    else:
        raise ValueError(f"extension non geree : {ext}")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    with open(ROOT / "corpus" / "sources.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dest = RAW_DIR / row["filename"]
            if dest.exists():
                print("deja present:", dest.name)
                ok += 1
                continue
            try:
                r = requests.get(row["url"], headers=HEADERS, timeout=60)
                r.raise_for_status()
                save(dest, r.content, row["url"])
                print("OK  ", dest.name)
                ok += 1
            except Exception as e:
                print("FAIL", row["filename"], "-", e, file=sys.stderr)
                fail += 1
    print(f"\n{ok} documents disponibles, {fail} echecs")


if __name__ == "__main__":
    main()
