"""Etape 5 - Pipeline RAG : Top-K chunks -> prompt strict -> LLM local (Ollama)."""
import json
from typing import Iterator

from src import config
from src.search import search

SYSTEM_PROMPT = (
    "Tu es un assistant specialise dans la transition energetique en France. "
    "A partir uniquement du contexte textuel fourni ci-dessous, reponds precisement a la question de l'utilisateur. "
    "Si la reponse n'y est pas, reponds exactement : "
    "\"Je ne sais pas : l'information n'est pas dans les documents du corpus.\" "
    "N'invente aucun chiffre ni aucune date. "
    "Cite les passages utilises avec leur numero entre crochets, par exemple [1]. "
    "Reponds en francais, de facon concise."
)
NO_ANSWER = "Je ne sais pas : l'information n'est pas dans les documents du corpus."


class LLMUnavailable(Exception):
    """Ollama est eteint, injoignable ou le modele n'est pas installe."""


def build_messages(question: str, passages: list[dict]) -> list[dict]:
    context = "\n\n".join(f"[{i}] (source : {p['source_file']}, page {p['page']})\n{p['text']}"
                          for i, p in enumerate(passages, 1))
    user = f"CONTEXTE :\n{context}\n\nQUESTION : {question}\n\nREPONSE (avec citations [n]) :"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def _call_ollama(messages: list[dict], stream: bool):
    import requests
    try:
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", stream=stream, timeout=(5, 600),
                          json={"model": config.OLLAMA_MODEL, "messages": messages, "stream": stream,
                                "options": {"temperature": 0.1, "num_ctx": 4096}})
    except requests.exceptions.ConnectionError:
        raise LLMUnavailable("Ollama ne repond pas. Lance l'application Ollama puis reessaie.")
    if r.status_code == 404:
        raise LLMUnavailable(f"Modele '{config.OLLAMA_MODEL}' introuvable. Installe-le : ollama pull {config.OLLAMA_MODEL}")
    r.raise_for_status()
    return r


def _sources(passages: list[dict]) -> list[dict]:
    return [{"n": i, **p} for i, p in enumerate(passages, 1)]


def answer(question: str, k: int = config.TOP_K, min_score: float = config.MIN_SCORE) -> dict:
    passages = search(question, k, min_score)
    if not passages:                                  # rien de pertinent : on n'appelle pas le LLM
        return {"question": question, "answer": NO_ANSWER, "sources": [], "model": None}
    r = _call_ollama(build_messages(question, passages), stream=False)
    text = r.json()["message"]["content"].strip()
    return {"question": question, "answer": text, "sources": _sources(passages), "model": config.OLLAMA_MODEL}


def stream_answer(question: str, k: int = config.TOP_K, min_score: float = config.MIN_SCORE) -> Iterator[dict]:
    """Evenements : sources -> token* -> done (ou error)."""
    passages = search(question, k, min_score)
    yield {"type": "sources", "sources": _sources(passages)}
    if not passages:
        yield {"type": "token", "text": NO_ANSWER}
        yield {"type": "done"}
        return
    try:
        r = _call_ollama(build_messages(question, passages), stream=True)
        for line in r.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield {"type": "token", "text": token}
            if chunk.get("done"):
                break
        yield {"type": "done"}
    except LLMUnavailable as e:
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        yield {"type": "error", "message": f"Erreur pendant la generation : {e}"}


def llm_status() -> dict:
    import requests
    try:
        tags = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=3).json().get("models", [])
        names = [m["name"] for m in tags]
        wanted = config.OLLAMA_MODEL
        ok = any(n == wanted or n == wanted + ":latest" for n in names)
        return {"ollama": True, "model": config.OLLAMA_MODEL, "model_available": ok, "installed": names}
    except Exception:
        return {"ollama": False, "model": config.OLLAMA_MODEL, "model_available": False, "installed": []}
