"""Etape 2 - Nettoyage et normalisation du texte (regex)."""
import re
import unicodedata

LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl",
             "\u2019": "'", "\u2018": "'", "\u00a0": " ", "\u202f": " ", "\u200b": ""}
PAGE_NUMBER_RE = re.compile(r"^\s*(?:page\s*)?\d{1,4}(?:\s*(?:/|sur|of)\s*\d{1,4})?\s*$", re.I)
BULLET_RE = re.compile(r"^\s*(?:[-\u2022*\u25cf]|\d+[.)]|[a-z][.)])\s+")


def fix_encoding(text: str) -> str:
    """Corrige le mojibake classique (UTF-8 lu comme latin-1 : 'Ã©' -> 'é')."""
    if re.search(r"Ã[\x80-\xbf]|Â[\x80-\xbf]|â€", text):
        try:
            return text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            try:
                return text.encode("cp1252").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                return text
    return text


def remove_page_numbers(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if not PAGE_NUMBER_RE.match(l))


def clean_text(text: str) -> str:
    """Pipeline de nettoyage complet. Retourne des paragraphes propres separes par une ligne vide."""
    if not text:
        return ""
    text = fix_encoding(text)
    text = unicodedata.normalize("NFC", text)
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)   # caracteres de controle
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = remove_page_numbers(text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)                   # cesures : "infor-\nmation"
    text = re.sub(r"[ \t]+", " ", text)                             # espaces multiples
    text = re.sub(r" *\n *", "\n", text)

    paragraphs = []
    for block in re.split(r"\n{2,}", text):
        lines = [l for l in block.split("\n") if l.strip()]
        merged = ""
        for line in lines:
            if not merged:
                merged = line
            elif BULLET_RE.match(line):                              # on garde les puces separees
                paragraphs.append(merged)
                merged = line
            else:                                                    # fusion des sauts de ligne intempestifs
                merged += " " + line
        if merged.strip():
            paragraphs.append(merged.strip())
    return "\n\n".join(paragraphs)
