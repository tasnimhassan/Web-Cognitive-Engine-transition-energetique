"""Compte les documents de data/raw par format. Usage : python -m scripts.check_corpus"""
from collections import Counter

from src.config import RAW_DIR

files = [p for p in RAW_DIR.iterdir() if p.suffix.lower() in {".pdf", ".html", ".htm", ".docx", ".txt"}]
c = Counter(p.suffix.lower() for p in files)
print(f"{len(files)} documents :", dict(c))
print("OK (30-50)" if 30 <= len(files) <= 50 else "ATTENTION : hors de la plage 30-50")
