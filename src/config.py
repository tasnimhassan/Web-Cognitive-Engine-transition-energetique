"""Configuration centrale du projet WebCognitive Engine."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CHROMA_DIR = ROOT / "data" / "chroma"

# Etape 3 : chunking / embeddings
CHUNK_SIZE = 500        # caracteres
CHUNK_OVERLAP = 100     # caracteres
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions
# Alternative multilingue (meilleure pour le francais) :
# "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Etape 4 : base vectorielle
COLLECTION_NAME = "webcognitive"

# Etape 5 : RAG local (Ollama)
import os
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")   # ou "mistral" si ton PC est assez puissant
TOP_K = 5               # nombre de passages envoyes au LLM
MIN_SCORE = 0.20        # similarite cosinus minimale (en dessous : passage ignore)
