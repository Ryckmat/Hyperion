---
title: "Guide Ingestion Généralisée"
toc: true
description: "Script : scripts/maintenance/ingest_generalized.py"
weight: 4
---

**Script** : `scripts/maintenance/ingest_generalized.py`
**Version** : **Component** : Neo4j Data Ingestion

---

## Vue d'ensemble

Le script d'**ingestion généralisée** permet d'indexer plusieurs sources de données dans Hyperion v2 :
- 📦 **Repositories Git** (commits, diffs, historique)
- 📚 **Documentation** (Markdown, HTML, PDFs)
- 🎫 **Tickets** (GitLab, Jira via API)
- 💻 **Code source** (AST, dépendances, métriques)

## Installation

```bash
# Activer l'environnement
cd /path/to/Hyperion
source venv/bin/activate  # si venv

# Installer les dépendances
pip install -e .

# Vérifier le script
python scripts/maintenance/ingest_generalized.py --help
```

## Usage de base

### 1. Ingestion d'un repository Git

```bash
python scripts/maintenance/ingest_generalized.py \
  --repo /path/to/project
```

**Ce qui est indexé** :
- Commits (auteur, date, message)
- Diffs (fichiers modifiés, lignes ajoutées/supprimées)
- Contributors (dédupliqués)
- Hotspots (fichiers les plus modifiés)

### 2. Ingestion de documentation

```bash
python scripts/maintenance/ingest_generalized.py \
  --docs /path/to/docs
```

**Formats supportés** :
- Markdown (.md)
- HTML (.html)
- PDF (à venir)

### 3. Ingestion de tickets

```bash
python scripts/maintenance/ingest_generalized.py \
  --tickets-url "https://gitlab.com/api/v4/projects/123/issues" \
  --tickets-token "glpat-xxxxxxxxxxxx"
```

**Métadonnées extraites** :
- Titre, description
- Labels, milestones
- Auteur, assigné
- Statut, dates

### 4. Ingestion combinée

```bash
python scripts/maintenance/ingest_generalized.py \
  --repo /path/to/project \
  --docs /path/to/docs \
  --tickets-url "https://api.example.com/tickets" \
  --tickets-token "token_secret"
```

## Configuration avancée

### Services Qdrant / Neo4j

```bash
# Qdrant custom
python scripts/maintenance/ingest_generalized.py \
  --repo /path/to/project \
  --qdrant-host qdrant.example.com \
  --qdrant-port 6333

# Neo4j custom
python scripts/maintenance/ingest_generalized.py \
  --repo /path/to/project \
  --neo4j-uri bolt://neo4j.example.com:7687
```

### Exemple complet

```bash
#!/bin/bash
# ingest_all.sh - Script d'ingestion complète

REPO="/home/user/projects/my-project"
DOCS="/home/user/projects/my-project/docs"
TICKETS_URL="https://gitlab.com/api/v4/projects/456/issues"
TICKETS_TOKEN="glpat-secret"

python scripts/maintenance/ingest_generalized.py \
  --repo "$REPO" \
  --docs "$DOCS" \
  --tickets-url "$TICKETS_URL" \
  --tickets-token "$TICKETS_TOKEN" \
  --qdrant-host localhost \
  --qdrant-port 6333 \
  --neo4j-uri bolt://localhost:7687

echo "✅ Ingestion terminée"
```

## Workflow Python

```python
from pathlib import Path
from scripts.maintenance.ingest_generalized import GeneralizedIngestion

# Initialisation
ingestion = GeneralizedIngestion(
    qdrant_host="localhost",
    qdrant_port=6333,
    neo4j_uri="bolt://localhost:7687"
)

# Ingestion
stats = ingestion.run(
    repo_path=Path("/path/to/repo"),
    docs_path=Path("/path/to/docs"),
    tickets_api={
        "url": "https://api.example.com/tickets",
        "token": "secret_token"
    }
)

# Résultats
print(f"Git: {stats['git']} éléments")
print(f"Docs: {stats['docs']} documents")
print(f"Tickets: {stats['tickets']} issues")
print(f"Code: {stats['code']} fichiers analysés")
```

## Sortie attendue

```
🚀 Démarrage ingestion généralisée

📦 Ingestion Git: /path/to/repo
  ✅ 1247 commits indexés
  ✅ 342 contributeurs dédupliqués

💻 Ingestion Code Analysis: /path/to/repo
  ✅ 156 fichiers Python analysés
  ✅ 89 relations DEPENDS_ON créées

📚 Ingestion Documentation: /path/to/docs
  ✅ 23 fichiers Markdown indexés
  ✅ 156 chunks créés

🎫 Ingestion Tickets: https://api.example.com
  ✅ 78 tickets indexés

✅ Ingestion terminée
📊 Stats: {
  "git": 1247,
  "docs": 23,
  "tickets": 78,
  "code": 156
}

📈 Total ingéré: 1504 éléments
```

## Vérification

### 1. Vérifier Qdrant

```bash
curl -s http://localhost:6333/collections/hyperion | jq .
```

### 2. Vérifier Neo4j

```cypher
// Compter les nodes
MATCH (n) RETURN labels(n), count(n)

// Vérifier dépendances
MATCH (f:File)-[:DEPENDS_ON]->(dep:File)
RETURN f.path, dep.path
LIMIT 10
```

### 3. Tester requête RAG

```python
from hyperion.modules.rag.query import RAGQueryEngine

engine = RAGQueryEngine()
response = engine.query("Quels sont les principaux modules du projet ?")
print(response["answer"])
```

## Troubleshooting

### Erreur: "Qdrant connection refused"

```bash
# Vérifier que Qdrant tourne
docker ps | grep qdrant

# Redémarrer si nécessaire
docker restart hyperion-qdrant
```

### Erreur: "Neo4j authentication failed"

```bash
# Vérifier credentials Neo4j
docker logs hyperion-neo4j | grep password

# Mettre à jour si nécessaire
```

### Erreur: "API tickets unauthorized"

```bash
# Vérifier token GitLab
curl -H "PRIVATE-TOKEN: $TOKEN" https://gitlab.com/api/v4/user

# Regénérer token si expiré
```

## Automatisation

### Cron job quotidien

```bash
# /etc/cron.d/hyperion-ingest
0 2 * * * user /path/to/ingest_all.sh >> /var/log/hyperion-ingest.log 2>&1
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
ingest:
  stage: deploy
  script:
    - python scripts/maintenance/ingest_generalized.py --repo $CI_PROJECT_DIR
  only:
    - main
```

## TODO

- [ ] Support incremental ingestion (ne ré-indexer que les changements)
- [ ] Progress bars
- [ ] Parallel processing
- [ ] Webhooks temps réel
- [ ] Support GitHub API
- [ ] Support Jira API

## Références

- Qdrant: https://qdrant.tech/documentation/
- Neo4j: https://neo4j.com/docs/
- GitLab API: https://docs.gitlab.com/ee/api/
