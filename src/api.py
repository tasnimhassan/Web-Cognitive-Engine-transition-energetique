"""API REST FastAPI (etapes 4-7).  Lancer : python -m uvicorn src.api:app --reload
Interface de chat : http://127.0.0.1:8000/     Documentation : http://127.0.0.1:8000/docs"""
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src import config
from src.analytics import clear_cache, get_analytics
from src.config import CHUNK_OVERLAP, CHUNK_SIZE, ROOT
from src.ingestion.run_ingestion import run_ingestion
from src.pipeline import index_directory
from src.rag import LLMUnavailable, answer, llm_status, stream_answer
from src.search import search
from src.vectorstore import stats

app = FastAPI(title="WebCognitive Engine", version="0.7.0")
STATIC_DIR = ROOT / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- Etape 6 : interface ----------
@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


# ---------- Etape 4 : indexation ----------
class IndexRequest(BaseModel):
    reset: bool = Field(True, description="Vider la base avant d'indexer")
    run_ingestion: bool = Field(True, description="Relancer le parsing de data/raw avant l'indexation")
    chunk_size: int = Field(CHUNK_SIZE, ge=100, le=3000)
    overlap: int = Field(CHUNK_OVERLAP, ge=0, le=1000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index")
def index(req: IndexRequest = IndexRequest()):
    """Pipeline complet : lecture -> nettoyage -> chunking -> embeddings -> ChromaDB."""
    if req.overlap >= req.chunk_size:
        raise HTTPException(400, "overlap doit etre inferieur a chunk_size")
    report = {}
    if req.run_ingestion:
        ing = run_ingestion()
        report["ingestion"] = {k: ing[k] for k in ("processed", "empty", "errors")}
    report["indexation"] = index_directory(reset=req.reset, chunk_size=req.chunk_size, overlap=req.overlap)
    clear_cache()                       # le tableau de bord sera recalcule
    return report


@app.get("/stats")
def get_stats():
    return stats()


# ---------- Etape 5 : recherche semantique et RAG ----------
class SearchRequest(BaseModel):
    question: str = Field(..., min_length=3)
    k: int = Field(config.TOP_K, ge=1, le=20)
    min_score: float = Field(config.MIN_SCORE, ge=0.0, le=1.0)


class ChatRequest(SearchRequest):
    pass


@app.post("/search")
def semantic_search(req: SearchRequest):
    """Recherche semantique seule : Top-K chunks par similarite cosinus."""
    return {"question": req.question, "results": search(req.question, req.k, req.min_score)}


@app.get("/debug/search")
def debug_search(q: str, k: int = 3):
    return [{"score": p["score"], "source": p["source_file"], "page": p["page"], "text": p["text"]}
            for p in search(q, k, min_score=0.0)]


@app.post("/chat")
def chat(req: ChatRequest):
    """RAG complet : reponse du LLM local + sources (fichier, page)."""
    try:
        return answer(req.question, req.k, req.min_score)
    except LLMUnavailable as e:
        raise HTTPException(503, str(e))


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """RAG en flux (NDJSON) : une ligne JSON par evenement (sources, token, done, error)."""
    def gen():
        for event in stream_answer(req.question, req.k, req.min_score):
            yield json.dumps(event, ensure_ascii=False) + "\n"
    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.get("/llm/status")
def get_llm_status():
    return llm_status()


# ---------- Etape 7 : tableau de bord ----------
@app.get("/analytics")
def analytics(refresh: bool = False):
    """Statistiques du corpus (formats, familles, mots-cles, tailles des passages, carte ACP)."""
    return get_analytics(refresh)
