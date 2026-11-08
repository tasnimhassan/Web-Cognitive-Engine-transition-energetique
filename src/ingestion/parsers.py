"""Etape 2 - Parseurs par format. Chaque parseur renvoie une liste de pages {page, text}."""
import re
from collections import Counter
from pathlib import Path


def _strip_repeated_lines(pages: list[str], edge: int = 3, ratio: float = 0.5) -> list[str]:
    """Supprime les en-tetes/pieds de page : lignes (en haut/bas de page) repetees sur > ratio des pages."""
    if len(pages) < 4:
        return pages
    norm = lambda l: re.sub(r"\d+", "#", l.strip().lower())
    counter = Counter()
    for p in pages:
        lines = [l for l in p.split("\n") if l.strip()]
        for l in set(map(norm, lines[:edge] + lines[-edge:])):
            counter[l] += 1
    frequent = {l for l, c in counter.items() if c / len(pages) > ratio and l}
    out = []
    for p in pages:
        lines = p.split("\n")
        idx = [i for i, l in enumerate(lines) if l.strip()]
        edges = set(idx[:edge] + idx[-edge:])
        out.append("\n".join(l for i, l in enumerate(lines) if not (i in edges and norm(l) in frequent)))
    return out


def parse_pdf(path: Path) -> tuple[str, list[dict]]:
    import pdfplumber
    raw_pages = []
    with pdfplumber.open(path) as pdf:
        title = (pdf.metadata or {}).get("Title") or path.stem
        for page in pdf.pages:
            raw_pages.append(page.extract_text() or "")
    pages = _strip_repeated_lines(raw_pages)
    return title, [{"page": i + 1, "text": t} for i, t in enumerate(pages)]


def parse_html(path: Path) -> tuple[str, list[dict]]:
    from bs4 import BeautifulSoup
    raw = path.read_bytes()
    soup = BeautifulSoup(raw, "lxml")   # BeautifulSoup detecte l'encodage
    title = soup.title.get_text(strip=True) if soup.title else path.stem
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside",
                     "form", "iframe", "svg", "button"]):
        tag.decompose()
    for tag in soup.find_all(attrs={"class": re.compile(r"(cookie|banner|advert|ads?-|menu|sidebar|breadcrumb)", re.I)}):
        tag.decompose()
    main = (soup.find(id="mw-content-text") or soup.find("article")
            or soup.find("main") or soup.body or soup)
    text = main.get_text("\n")
    return title, [{"page": 1, "text": text}]


def parse_docx(path: Path) -> tuple[str, list[dict]]:
    import docx
    d = docx.Document(str(path))
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    title = d.core_properties.title or path.stem
    return title, [{"page": 1, "text": "\n\n".join(parts)}]


def parse_txt(path: Path) -> tuple[str, list[dict]]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.stem, [{"page": 1, "text": raw.decode(enc)}]
        except UnicodeDecodeError:
            continue
    return path.stem, [{"page": 1, "text": raw.decode("utf-8", errors="ignore")}]


PARSERS = {".pdf": parse_pdf, ".html": parse_html, ".htm": parse_html,
           ".docx": parse_docx, ".txt": parse_txt}
