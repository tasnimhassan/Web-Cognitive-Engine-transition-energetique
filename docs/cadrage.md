# Etape 1 - Cadrage, corpus et strategie d'ingestion

## 1. Perimetre fonctionnel (cahier des charges synthetique)
**Projet** : WebCognitive Engine - assistant conversationnel local sur la **transition energetique en France**
(production, consommation, EnR, scenarios, politiques publiques).
**Theme unique** : la transition energetique et le systeme electrique francais.
**Utilisateur cible** : etudiant, analyste ou citoyen qui cherche un chiffre ou une position sourcee.

| Besoin | Description | Etape |
|---|---|---|
| F1 | Ingerer PDF, HTML, DOCX, TXT | 2 |
| F2 | Nettoyer et normaliser le texte | 2 |
| F3 | Decouper en chunks + embeddings locaux | 3 |
| F4 | Stocker en base vectorielle + API d'indexation | 4 |
| F5 | Recherche semantique + RAG local (Ollama) | 5 |
| F6 | Interface chat + dataviz | 6-7 |

**Contraintes** : 100 % local, outils libres, aucune API cloud payante, tracabilite (fichier + page).
**Hors perimetre** : OCR de PDF scannes, authentification, multi-utilisateurs.

## 2. Corpus (45 documents, theme unique)
Inventaire complet dans `corpus/sources.csv` (45 sources distinctes) :

| Format | Nb | Contenu |
|---|---|---|
| PDF | 25 | bilans RTE 2025 (national + regions), Bilan previsionnel 2025, ADEME, negaWatt, Sauvons le Climat, Cour des comptes europeenne, documents parlementaires |
| HTML | 8 | articles juridiques et presse sur la PPE3 et sur le rapport 2026 de la Cour des comptes |
| DOCX | 6 | articles de presse / fiches Connaissance des Energies, convertis en Word |
| TXT | 6 | 5 pages Wikipedia (transition, politique energetique, eolien, solaire, nucleaire) + une question ecrite a l'Assemblee |

Theme : transition energetique en France (production, scenarios, PPE3, financement des EnR, debats).
Les sources couvrent des points de vue varies (organismes officiels, filieres, associations, Cour des comptes).

```bash
python -m scripts.fetch_corpus    # telecharge et convertit (docx/txt) vers data/raw/
python -m scripts.check_corpus    # verifie le nombre de documents par format
```
Les DOCX et TXT sont **generes par conversion de pages web** (le script extrait le texte principal).
Si votre enseignant veut des Word "natifs", redigez-en quelques-uns vous-meme (fiches de synthese).
Les liens peuvent changer : un echec est affiche, remplacez alors la source dans le CSV.
Les 5 pages Wikipedia ont des titres a verifier.

## 3. Audit visuel AVANT le code (obligatoire)
Ouvrir chaque document : texte selectionnable (pas un scan), contenu riche, pas de doublon.
Questions de validation (chiffres lus dans les fiches RTE 2025, **a verifier vous-meme dans le PDF** et completer avec page exacte) :

| # | Question | Fichier | Page | Reponse attendue (a confirmer) |
|---|---|---|---|---|
| 1 | Quelle a ete la consommation d'electricite en Nouvelle-Aquitaine en 2025 ? | rte_fiche_presse_nouvelle_aquitaine_2025.pdf | _ | 42,3 TWh (+1 %) |
| 2 | Quelle puissance solaire est installee en Nouvelle-Aquitaine fin 2025 ? | rte_fiche_presse_nouvelle_aquitaine_2025.pdf | _ | 6 800 MW (+1 200 MW) |
| 3 | Quelle a ete la production d'electricite en Occitanie en 2025 et son evolution ? | rte_fiche_presse_occitanie_2025.pdf | _ | 32,7 TWh (-17 %) |
| 4 | Pourquoi la production a-t-elle baisse en Occitanie ? | rte_fiche_presse_occitanie_2025.pdf | _ | maintenance Golfech + hydraulique normalisee |
| 5 | Quelle puissance eolienne en Occitanie ? | rte_fiche_presse_occitanie_2025.pdf | _ | 1 800 MW |
| 6 | Quel est le montant des investissements de RTE en Occitanie en 2025 ? | rte_fiche_presse_occitanie_2025.pdf | _ | 207 M€ |
| 7 | Quelle est la consommation nationale en 2025 par rapport a 2024 ? | rte_bilan_electrique_2025_principaux_resultats.pdf | _ | stable (+0,4 %) |
| 8 | Que dit la note negaWatt sur la production d'eolien terrestre du mix ADEME Ref ? | negawatt_analyse_etude_ademe_100enr.pdf | _ | a relever |
| 9-12 | ... (a rediger sur vos autres documents) | | | |

Ce jeu de questions servira d'evaluation du RAG aux etapes 5-8.

## 4. Environnement et versioning
```bash
git init
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
git add . && git commit -m "Etape 1 : cadrage et arborescence" && git tag etape-1
```

## 5. Arborescence
```
webcognitive/
├── data/raw/ | data/processed/ | data/chroma/
├── corpus/sources.csv
├── docs/cadrage.md
├── scripts/fetch_corpus.py
├── src/ (config, ingestion/, chunking, embeddings, vectorstore, pipeline, api)
└── tests/
```
