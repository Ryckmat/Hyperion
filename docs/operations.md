---
title: "Exploitation"
toc: true
description: "Runbook Hyperion : démarrage, arrêt, contrôles, diagnostic et reprise après incident."
weight: 2
---

## Démarrage et arrêt

```bash
./scripts/docker/hyperion-docker.sh --profile full        # démarrer tous les services
./scripts/docker/hyperion-docker.sh --action status       # état des conteneurs
./scripts/docker/hyperion-docker.sh --action down         # tout arrêter
./scripts/docker/hyperion-docker.sh --action restart --service hyperion-api
```

Démarrage sans Docker (API seule, services externes déjà lancés) :

```bash
hyperion server --host 0.0.0.0 --port 8000
```

## Contrôles

| Contrôle | Commande | Attendu |
|---|---|---|
| API | `curl -s localhost:8000/api/health` | `"status": "healthy"` |
| Moteurs code | `curl -s localhost:8000/api/v2/health` | statut sans erreur Neo4j |
| Services | `hyperion status` | tous en OK |
| Qualité RAG | `curl -s localhost:8000/api/quality/alerts` | aucune alerte active |
| Neo4j | `curl -s localhost:7474` | réponse HTTP 200 |
| Qdrant | `curl -s localhost:6333/collections` | collection `hyperion_repos` présente |
| Ollama | `curl -s localhost:11434/api/tags` | modèle configuré listé |

## Diagnostic

Toujours dans cet ordre : API, puis Neo4j, puis Qdrant, puis Ollama. Un service en panne en aval explique souvent l'erreur vue en amont.

```bash
./scripts/docker/hyperion-docker.sh --action logs --follow    # logs des conteneurs
tail -f logs/hyperion_$(date +%Y%m%d).log | jq .             # logs applicatifs
```

**Chercher une requête précise** : chaque log porte un `request_id` et un `correlation_id`.

```bash
grep '"request_id": "<id>"' logs/hyperion_*.log | jq .
```

## Incidents

**API en 500 sur `/api/v2/*`**
1. `curl -s localhost:7474` : si Neo4j ne répond pas, `./scripts/docker/hyperion-docker.sh --action restart --service neo4j`.
2. Vérifier `NEO4J_URI`, `NEO4J_USER` et `NEO4J_PASSWORD=***REDACTED***` dans `.env`.
3. Relancer la requête. Les connexions sont fermées à chaque appel, aucun nettoyage n'est nécessaire.

**Chat qui ne répond pas ou très lent**
1. `curl -s localhost:11434/api/tags` : le modèle de `OLLAMA_MODEL` doit apparaître.
2. Modèle absent : `docker exec -it hyperion-ollama ollama pull <modele>`.
3. Toujours lent : passer à un modèle plus léger dans `.env`, puis redémarrer `hyperion-api`. Les appels LLM n'ont pas de timeout : une requête bloquée occupe un worker jusqu'à sa fin.

**Réponses du chat vides ou hors sujet**
1. `curl -s localhost:6333/collections/hyperion_repos` : vérifier que la collection contient des points.
2. Collection vide : réindexer avec `python3 scripts/maintenance/ingest_rag.py --repo <repo> --clear`.

**Alerte qualité active**
1. `curl -s localhost:8000/api/quality/trends?days=7` pour situer la dérive.
2. Lancer l'évaluation : `hyperion eval --suite eval/suites/core.yaml`, puis comparer aux seuils de [slo](slo).

**Échec d'import au démarrage (`bcrypt`, `pyotp`, `jwt`, `xgboost`)**
Dépendance manquante : `pip install -r requirements.txt`. Ne jamais contourner, le module d'authentification refuse volontairement de démarrer sans elles.

## Maintenance

| Fréquence | Action | Commande |
|---|---|---|
| Quotidienne | Contrôles ci-dessus | voir tableau |
| Hebdomadaire | Évaluation RAG | `hyperion eval --suite eval/suites/core.yaml` |
| Hebdomadaire | Fichiers temporaires | `python3 scripts/cleanup.py` |
| Après analyse d'un nouveau dépôt | Ingestion Neo4j + RAG | `hyperion ingest ...` puis `ingest_rag.py --repo <repo>` |
| Mensuelle | Purge des anciens logs | `find logs/ -name "*.log" -mtime +30 -delete` |

## Sauvegarde et reprise

Les données reconstructibles (profils, index Qdrant, graphe Neo4j) se régénèrent depuis les dépôts sources avec le workflow de l'[accueil](./). À sauvegarder réellement :

- `.env` (secrets)
- `modeles/` (modèles de référence)
- `audit/hyperion_audit.jsonl` (traçabilité)

Reprise : restaurer ces trois éléments, démarrer les services, puis relancer profil, ingestion et indexation pour chaque dépôt.
