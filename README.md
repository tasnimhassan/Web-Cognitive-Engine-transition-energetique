# WebCognitive Engine

Assistant conversationnel **100 % local** pour interroger un corpus de documents sur **la transition énergétique en France**.
Les documents hétérogènes (PDF, HTML, Word, TXT) sont nettoyés, découpés en passages, transformés en vecteurs, puis interrogés
en langage naturel. Les réponses sont générées par un modèle de langage local (Ollama) **uniquement à partir des documents**,
avec la source de chaque information (fichier et page).

> Projet individuel — M2 THYP 2026/2027 — cours *Techniques Informatiques et Web*
> Auteur : Tesline HASSAN OKIEH

## Fonctionnalités
- **Ingestion** de PDF, pages HTML, documents Word et fichiers texte (extraction, nettoyage par expressions régulières, export JSON/Markdown).
- **Recherche sémantique** : passages de 500 caractères (chevauchement 100), embeddings `all-MiniLM-L6-v2` (384 dimensions), base vectorielle ChromaDB.
- **RAG local** : les 5 passages les plus proches (similarité cosinus) sont donnés à un LLM via Ollama, avec une consigne stricte
  (« réponds uniquement avec le contexte, sinon dis que tu ne sais pas »).
- **Interface web** : chat avec réponse en flux, sources cliquables (fichier, page, pertinence, extrait).
- **Tableau de bord** : formats, familles de sources, mots-clés stratégiques, volumes, taille des passages, carte ACP des passages.
- **API REST** (FastAPI) documentée automatiquement sur `/docs`.
- **Recette automatisée** : `scripts/recette.py` vérifie toute la chaîne et génère un rapport.

## Architecture
```
data/raw ──► parsing + nettoyage ──► data/processed (JSON + Markdown)
 (45 sources)   src/ingestion/                  │
                                     chunking (500 / 100) + embeddings (384 dim.)
                                                ▼
 Navigateur ◄──► FastAPI (src/api.py) ◄──► ChromaDB (data/chroma)
 (static/index.html)     │
                         └── recherche Top-K ──► prompt strict ──► Ollama (LLM local)
```

| Module | Rôle |
|---|---|
| `src/ingestion/` | lecture des 4 formats, nettoyage, export |
| `src/chunking.py`, `src/embeddings.py` | découpage avec chevauchement, vecteurs |
| `src/vectorstore.py`, `src/pipeline.py` | ChromaDB et indexation |
| `src/search.py`, `src/rag.py` | recherche Top-K, prompt, appel à Ollama |
| `src/analytics.py` | statistiques du tableau de bord |
| `src/api.py` | routes REST et service de l'interface |
| `static/index.html` | chat et tableau de bord (HTML, CSS, JavaScript) |
| `scripts/` | téléchargement du corpus, évaluation, recette |

## Corpus
Thème unique : **la transition énergétique et le système électrique français** (production, scénarios, PPE3, financement des énergies renouvelables, débats).
Sources : RTE, ADEME, négaWatt, Sauvons le Climat, Cour des comptes, Assemblée nationale, presse spécialisée, Wikipédia.
La liste complète (45 sources) est dans `corpus/sources.csv` ; les fichiers sont téléchargés par `scripts/fetch_corpus.py`
(les `.docx` et `.txt` sont obtenus par conversion de pages web). Certains sites bloquent le téléchargement automatique :
lors de ma recette, **39 documents** ont été récupérés et indexés (22 PDF, 7 HTML, 6 TXT, 4 DOCX), soit **2 019 passages**.

## Prérequis
- Windows, macOS ou Linux, **Python 3.12** recommandé (3.14 fonctionne sur ma machine)
- 8 Go de RAM conseillés, ~5 Go d'espace disque
- [Ollama](https://ollama.com/download) (LLM local)
- Git

## Installation pas à pas
**Windows (PowerShell)**
```powershell
git clone <URL-du-depot> webcognitive
cd webcognitive
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
**macOS / Linux**
```bash
git clone <URL-du-depot> webcognitive && cd webcognitive
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Modèle de langage (une seule fois)**
```bash
ollama pull llama3.2:3b
```
Autre modèle : `OLLAMA_MODEL=mistral` (variable d'environnement, ex. `$env:OLLAMA_MODEL="mistral"` sous PowerShell).

## Lancement
```powershell
python -m scripts.fetch_corpus      # télécharge les documents dans data/raw/
python -m scripts.check_corpus      # vérifie : 30 à 50 documents
python -m uvicorn src.api:app --reload
```
1. Ouvrir **http://127.0.0.1:8000/docs**, lancer **POST /index** (environ 3 minutes la première fois : le modèle d'embeddings se télécharge).
2. Ouvrir **http://127.0.0.1:8000/** : chat et onglet « Analyse du corpus ». Les deux voyants du haut doivent être verts.

## Utilisation
- **Chat** : poser une question, lire la réponse (citations `[1]`, `[2]`) et cliquer sur une source pour voir l'extrait exact.
  Si l'information n'est pas dans le corpus, le système répond « Je ne sais pas ».
- **Analyse du corpus** : vue d'ensemble ; cliquer sur un mot-clé pour voir les documents où il est le plus présent.
- Exemples : *Que prévoit la PPE3 pour l'éolien terrestre ?* — *Que reproche la Cour des comptes au soutien aux énergies renouvelables ?*

## API REST
| Route | Rôle |
|---|---|
| `GET /` | interface web |
| `POST /index` | ingestion + indexation complète du corpus |
| `GET /stats` | état de la base (passages, documents) |
| `POST /search` | recherche sémantique Top-K |
| `POST /chat` | réponse RAG complète avec sources |
| `POST /chat/stream` | réponse RAG en flux (NDJSON) |
| `GET /analytics` | statistiques du tableau de bord |
| `GET /llm/status` | état d'Ollama et du modèle |
| `GET /health`, `GET /debug/search` | santé de l'API, test rapide de recherche |

## Tests et validation
```powershell
python -m pytest -q                  # tests unitaires (nettoyage, chunking, RAG, analytics)
python -m scripts.evaluate           # la bonne source est-elle dans le Top-K ?
python -m scripts.recette            # recette complète -> docs/rapport_recette.md
```
La recette utilise les questions de `docs/validation_questions.json` (dont une question hors corpus qui doit être refusée).

## Dépannage
| Problème | Solution |
|---|---|
| `python` introuvable | réinstaller Python en cochant « Add python.exe to PATH », rouvrir le terminal |
| `Activate.ps1` refusé | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip` ne se lance pas | utiliser `python -m pip ...` |
| `DLL load failed` (numpy, chromadb) | installer le *Visual C++ Redistributable* ; vérifier la stratégie de sécurité Windows (Smart App Control) |
| `ollama` non reconnu dans VS Code | fermer et rouvrir VS Code après l'installation d'Ollama |
| Voyant Ollama rouge | lancer Ollama puis `ollama pull llama3.2:3b` |
| Base vide (0 passage) | lancer `POST /index` puis actualiser la page |
| Réponses lentes | choisir 3 passages, modèle plus petit (`llama3.2:1b`), poser une question de test avant la démo |

## Limites connues
- Le modèle d'embeddings `all-MiniLM-L6-v2` est surtout entraîné sur l'anglais ; `paraphrase-multilingual-MiniLM-L12-v2` peut mieux convenir au français (à changer dans `src/config.py`, puis relancer `POST /index`).
- Un petit LLM local peut être imprécis ; la qualité dépend des passages retrouvés.
- Pas d'OCR : les PDF scannés sans texte sont ignorés. Pas de mémoire de conversation ni d'authentification.

## Documentation complémentaire
- [`docs/manuel_utilisateur.md`](docs/manuel_utilisateur.md) — utiliser l'application
- [`docs/specification_technique.md`](docs/specification_technique.md) — choix techniques et formats de données
- [`docs/cadrage.md`](docs/cadrage.md) — cadrage, corpus, audit
- `docs/rapport_recette.md` — généré par `scripts/recette.py`

## Outils libres utilisés
Python, pdfplumber, BeautifulSoup, python-docx, sentence-transformers (Hugging Face), ChromaDB, FastAPI, Uvicorn, Ollama (Llama 3.2), Git.
Les documents du corpus restent la propriété de leurs auteurs ; seules leurs adresses sont fournies.
