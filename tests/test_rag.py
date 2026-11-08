from src import rag


def test_build_messages_numbers_passages_and_strict_prompt():
    passages = [{"source_file": "a.pdf", "page": 3, "text": "Le solaire progresse."},
                {"source_file": "b.html", "page": 1, "text": "L'eolien recule."}]
    msgs = rag.build_messages("Quoi ?", passages)
    assert msgs[0]["role"] == "system" and "uniquement" in msgs[0]["content"]
    user = msgs[1]["content"]
    assert "[1] (source : a.pdf, page 3)" in user and "[2] (source : b.html, page 1)" in user
    assert "QUESTION : Quoi ?" in user


def test_no_passage_means_no_llm_call(monkeypatch):
    monkeypatch.setattr(rag, "search", lambda *a, **k: [])
    monkeypatch.setattr(rag, "_call_ollama", lambda *a, **k: (_ for _ in ()).throw(AssertionError("LLM appele")))
    out = rag.answer("Capitale de l'Australie ?")
    assert out["answer"] == rag.NO_ANSWER and out["sources"] == []
    events = list(rag.stream_answer("Capitale de l'Australie ?"))
    assert [e["type"] for e in events] == ["sources", "token", "done"]


def test_stream_emits_error_when_ollama_down(monkeypatch):
    monkeypatch.setattr(rag, "search", lambda *a, **k: [{"source_file": "a.pdf", "page": 1, "text": "x", "score": 0.5}])
    def boom(*a, **k): raise rag.LLMUnavailable("Ollama ne repond pas")
    monkeypatch.setattr(rag, "_call_ollama", boom)
    events = list(rag.stream_answer("q ?"))
    assert events[0]["type"] == "sources" and events[-1] == {"type": "error", "message": "Ollama ne repond pas"}
