# Spécification technique — WebCognitive Engine

## 1. Chaîne de traitement
| Étape | Module | Entrée → sortie |
|---|---|---|
| Ingestion | `src/ingestion/` | `data/raw/*` → `data/processed/*.json` et `*.md` |
| Chunking | `src/chunking.py` | texte d'une page → passages de ≤ 500 caractères, chevauchement de 100 |
| Embeddings | `src/embeddings.py` | passages → vecteurs de 384 dimensions, normalisés |
| Stockage | `src/vectorstore.py` | vecteurs + texte + métadonnées → ChromaDB (cosinus) |
| Recherche | `src/search.py` | question → Top-K passages (score = 1 − distance cosinus) |
| RAG | `src/rag.py` | passages + question → prompt strict → Ollama → réponse + sources |
| Analyse | `src/analytics.py` | corpus et base → statistiques JSON |

## 2. Formats de données
**Document nettoyé** (`data/processed/<nom>.json`) : `doc_id`, `source_file`, `format`, `title`, `ingested_at`, `n_pages`, `n_chars`, `pages[{page, text}]`.

**Passage indexé** : identifiant `<doc_id>::p<page>::c<n>`, texte, métadonnées `source_file`, `title`, `format`, `page`, `chunk_index`, `doc_id`.

## 3. Choix de conception
| Paramètre | Valeur | Justification |
|---|---|---|
| Taille des passages | 500 caractères | une idée par passage, contexte suffisant |
| Chevauchement | 100 caractères | éviter de couper une idée |
| Coupure | fin de phrase, sinon espace | passages lisibles |
| Modèle d'embeddings | all-MiniLM-L6-v2 | léger, local, 384 dimensions |
| Mesure de proximité | similarité cosinus | vecteurs normalisés |
| Top-K | 5 | équilibre contexte / durée de génération |
| Seuil de pertinence | 0,20 | ignorer les passages sans rapport ; sans passage, le LLM n'est pas appelé |
| LLM | llama3.2:3b via Ollama | tourne sans GPU ; remplaçable par variable d'environnement |
| Température | 0,1 | réponses factuelles et stables |

**Prompt système** : répondre uniquement à partir du contexte fourni, répondre « Je ne sais pas… » si l'information est absente, ne rien inventer,
citer les passages par leur numéro `[n]`, répondre en français.

## 4. API
| Méthode et route | Corps / paramètres | Réponse |
|---|---|---|
| `POST /index` | `reset`, `run_ingestion`, `chunk_size`, `overlap` | rapport d'ingestion et d'indexation |
| `GET /stats` | — | `n_chunks`, `n_documents`, liste des fichiers |
| `POST /search` | `question`, `k`, `min_score` | `results[{score, source_file, page, text}]` |
| `POST /chat` | `question`, `k`, `min_score` | `answer`, `sources[{n, score, source_file, page, text}]`, `model` |
| `POST /chat/stream` | idem | lignes JSON : `sources`, `token`, `done` ou `error` |
| `GET /analytics` | `refresh` | totaux, formats, familles, mots-clés, histogramme, ACP |
| `GET /llm/status` | — | `ollama`, `model`, `model_available` |

## 5. Tableau de bord
Statistiques calculées côté serveur (`src/analytics.py`) : répartition par format et par famille de source (déduite du nom de fichier),
fréquence de 13 mots-clés par expressions régulières, 12 plus gros documents, histogramme des tailles de passages, projection ACP (SVD de numpy) des vecteurs.
Les graphiques sont dessinés en JavaScript/SVG, sans bibliothèque externe.

## 6. Qualité
- **Tests unitaires** (`tests/`) : nettoyage, chunking, RAG (avec faux Ollama), analytics.
- **Évaluation** (`scripts/evaluate.py`) : la bonne source figure-t-elle dans le Top-K ?
- **Recette** (`scripts/recette.py`) : corpus, API, base, dataviz, interface, Ollama, questions de validation ; rapport dans `docs/rapport_recette.md`.

## 7. Sécurité et confidentialité
Aucune donnée n'est envoyée vers un service externe. L'interface construit l'affichage avec `textContent` (pas de HTML injecté depuis les documents ou les réponses).
L'API n'est pas authentifiée : elle est prévue pour un usage local (`127.0.0.1`).
