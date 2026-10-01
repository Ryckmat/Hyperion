---
title: "Getting Started - Hyperion"
toc: true
description: "Guide rapide pour démarrer avec Hyperion."
weight: 4
---

Guide rapide pour démarrer avec Hyperion.

## 🎯 Prérequis

- Python 3.10+
- Git installé
- (Optionnel) Neo4j 5.x pour l'ingestion graphe

## 📦 Installation

### Installation standard

```bash
cd Hyperion
pip install -e .
```

### Installation avec dépendances dev

```bash
pip install -e ".[dev]"
```

### Vérification

```bash
hyperion --version
hyperion info
```

## 🚀 Premier profiling

### 1. Cloner un repo à analyser

```bash
git clone https://github.com/psf/requests.git /tmp/requests
```

### 2. Profiler le repo

```bash
hyperion profile /tmp/requests --output data/repositories/
```

Cela génère : `data/repositories/requests/profile.yaml`

### 3. Générer la documentation

```bash
hyperion generate data/repositories/requests/profile.yaml --output output/requests/
```

Cela génère :
- `output/requests/index.md` : Vue d'ensemble
- `output/requests/registre.md` : Registre technique

## 📊 Export historique production

### 1. Export releases taggées

```bash
hyperion export /tmp/requests --tags-pattern "^v\d+\.\d+\.\d+$" --output data/repositories/requests/
```

Génère :
- `data/repositories/requests/prod_deploys.json`
- `data/repositories/requests/prod_commits.jsonl`
- `data/repositories/requests/prod_files.jsonl`

## 🗄️ Ingestion Neo4j

### 1. Démarrer Neo4j

```bash
# Docker
docker run -d \
  --name neo4j-hyperion \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.28
```

### 2. Configuration

```bash
# Copier et éditer .env
cp .env.example .env
nano .env

# Ajuster :
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=password
```

### 3. Ingestion

```bash
hyperion ingest data/repositories/requests/ --database hyperion
```

### 4. Requêtes Cypher

```cypher
// Top 10 fichiers les plus modifiés
MATCH (c:Commit)-[r:TOUCHED]->(f:File)
RETURN f.path, COUNT(c) AS commits, SUM(r.add + r.del) AS changes
ORDER BY changes DESC
LIMIT 10

// Contributeurs les plus actifs
MATCH (a:Author)-[:COMMITTED_BY]->(c:Commit)
RETURN a.name, a.email, COUNT(c) AS commits
ORDER BY commits DESC
LIMIT 10

// Fichiers dans la dernière release
MATCH (t:Tag {name: 'v2.32.3'})<-[:IN_RELEASE]-(c:Commit)-[:TOUCHED]->(f:File)
RETURN DISTINCT f.path
ORDER BY f.path
```

## 📝 Workflow complet

```bash
# 1. Profiler
hyperion profile /path/to/repo

# 2. Générer docs
hyperion generate data/repositories/mon-repo/profile.yaml

# 3. Export prod
hyperion export /path/to/repo

# 4. Ingestion Neo4j
hyperion ingest data/repositories/mon-repo/
```

## 🔧 Configuration avancée

### Filtres personnalisés

Modifier `config/filters.yaml` :

```yaml
ignore_extensions:
  - .lock
  - .min.js
  # ... ajoutez vos extensions

ignore_prefixes:
  - vendor/
  - node_modules/
  # ... ajoutez vos préfixes
```

### Variables d'environnement

```bash
# Surcharge batch sizes
export BATCH_SIZE_COMMITS=1000
export BATCH_SIZE_FILES=5000

# Surcharge patterns Git
export TAGS_REGEX="^release-\d+\.\d+$"
```

## 📚 Prochaines étapes

- [Architecture](../architecture/system-overview) : Architecture détaillée du projet
- [CLI Reference](../reference/cli-reference) : Référence complète des commandes
- Configuration : Configuration et format YAML
- [Neo4j Integration](../advanced/neo4j-integration) : Modèle de graphe

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'hyperion'`

```bash
# Réinstaller en mode éditable
pip install -e .
```

### `Neo4j connection failed`

```bash
# Vérifier Neo4j actif
docker ps | grep neo4j

# Tester connexion
python -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j','password')).verify_connectivity(); print('OK')"
```

### Erreurs de parsing Git

```bash
# Vérifier Git installé
git --version

# Vérifier repo valide
cd /path/to/repo && git log --oneline -1
```

## 💬 Support

- Issues GitHub : https://github.com/Ryckmat/Hyperion/issues
- Email : contact@ryckmat.dev
