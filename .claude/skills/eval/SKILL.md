---
name: eval
description: Lance l'évaluation RAG Hyperion (eval/run.py) sur une suite et résume les métriques par rapport aux seuils.
---

1. Lister les suites disponibles dans `eval/suites/` ; par défaut `core.yaml`
2. Lancer `python eval/run.py --help` pour vérifier les options, puis exécuter la suite demandée
3. Si le moteur RAG ne se charge pas (Qdrant ou Ollama absents), le dire clairement sans simuler de résultats
4. Résumer : métriques (latence, confiance, couverture des sources) vs `threshold` et `critical_threshold` de la suite, régressions éventuelles
