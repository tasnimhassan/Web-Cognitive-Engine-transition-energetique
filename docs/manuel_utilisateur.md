# Manuel utilisateur — WebCognitive Engine

## 1. Démarrer
1. Ouvrir un terminal dans le dossier du projet et activer l'environnement : `.venv\Scripts\Activate.ps1`
2. Lancer l'application : `python -m uvicorn src.api:app --reload`
3. Ouvrir **http://127.0.0.1:8000/** dans un navigateur.

En haut à droite, deux voyants indiquent l'état du système :
- **base** : nombre de documents et de passages indexés (vert si la base n'est pas vide) ;
- **Ollama** : nom du modèle (vert si le modèle est installé et disponible).

## 2. Poser une question (onglet Chat)
1. Taper la question dans la zone de saisie, ou cliquer sur une question d'exemple.
2. Choisir le nombre de passages utilisés (3, 5 ou 8) : moins de passages = réponse plus rapide, plus de passages = plus de contexte.
3. Cliquer sur **Envoyer**. La réponse s'écrit progressivement.

**Lire une réponse**
- Les nombres entre crochets (`[1]`, `[2]`) renvoient aux sources listées sous la réponse.
- Chaque source indique le fichier, la page et la pertinence ; un clic affiche l'extrait exact.
- « Je ne sais pas » signifie que l'information n'est pas dans les documents : le système n'invente pas.

**Bonnes pratiques** : questions précises (chiffres, dates, acteurs), une idée par question, reformuler si la réponse est vague.

## 3. Analyser le corpus (onglet Analyse du corpus)
- Chiffres clés : documents, passages, caractères, taille moyenne d'un passage.
- Camemberts : répartition par format et par famille de source.
- Mots-clés : cliquer sur une barre pour voir les documents les plus riches sur ce thème.
- Volume par document, taille des passages, carte des passages (un point = un passage ; points proches = sens proche).
- Bouton **Actualiser** : recalcule les statistiques.

## 4. Mettre à jour le corpus
1. Ajouter ou retirer des fichiers dans `data/raw/` (PDF, HTML, DOCX, TXT) ou modifier `corpus/sources.csv` puis `python -m scripts.fetch_corpus`.
2. Dans http://127.0.0.1:8000/docs, lancer **POST /index** (le corpus est relu, nettoyé et réindexé).

## 5. Questions fréquentes
- **Pourquoi la première réponse est-elle lente ?** Les modèles se chargent en mémoire ; les suivantes sont plus rapides.
- **Les données quittent-elles mon ordinateur ?** Non : embeddings, base et modèle de langage tournent en local.
- **Une réponse me semble fausse.** Vérifier les sources affichées ; si l'extrait ne la soutient pas, reformuler la question.
