# Rapport de recette - WebCognitive Engine

Date : 08/11/2026 18:07  |  Top-K : 5  |  LLM : teste

**Resultat global : 3/4 controles reussis**

## Controles

| Controle | Statut | Detail |
|---|---|---|
| Corpus de 30 a 50 documents | OK | 39 documents |
| Au moins 3 formats differents | OK | docx, html, pdf, txt |
| Documents nettoyes (data/processed) | OK | 39 JSON |
| API en marche (/health) | ECHEC | injoignable (HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded with url: /health (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=8000): Failed to establish a new connection: [WinError 10061] Aucune connexion n’a pu être établie car l’ordinateur cible l’a expressément refusée"))). Lance : python -m uvicorn src.api:app |
