# 🧠 Hyperion

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-189%2F189-green.svg)](#)

**Hyperion v2.9 + v3.0** - Plateforme d'intelligence locale pour repositories Git avec architecture microservices.

## 🎯 Fonctionnalités

### Core
* **Analyse Git** : commits, contributeurs, hotspots, métriques
* **RAG Pipeline** : recherche sémantique avec validation qualité
* **API REST** : endpoints complets + compatibilité OpenAI
* **CLI** : interface ligne de commande complète
* **Dashboard** : interface web pour visualisation

### Architecture v3.0
* **API Gateway** : routage intelligent, auth, rate limiting, cache
* **8 Microservices** : RAG, Analytics, Dashboard, Monitoring, etc.
* **Cache distribué** : L1/L2 avec invalidation par tags
* **Monitoring** : Prometheus, structured logging, métriques
* **Sécurité** : JWT, TOTP, RBAC

## 🚀 Démarrage rapide

### Installation
```bash
git clone <repository>
cd Hyperion
pip install -e .
```

### Lancement
```bash
# Option 1: Orchestrateur master
./scripts/deploy/hyperion_master.sh --profile enterprise

# Option 2: Docker (8 services)
./scripts/docker/hyperion-docker.sh --action up --profile enterprise
```

### Services
Une fois lancé, les services sont disponibles :
* **API Gateway** : http://localhost:8000
* **Dashboard** : http://localhost:3000
* **Chat Interface** : http://localhost:3001
* **Monitoring** : http://localhost:9090
* **Neo4j Browser** : http://localhost:7474

## 📋 Utilisation

### CLI
```bash
# Analyser un repository
hyperion profile /path/to/repo

# Générer documentation
hyperion generate data/repositories/mon-repo/profile.yaml

# Ingérer dans Neo4j
hyperion ingest data/repositories/mon-repo/profile.yaml

# Informations système
hyperion info
```

### API REST
```bash
# Health check
curl http://localhost:8000/api/health

# Liste repositories
curl http://localhost:8000/api/repos

# Chat RAG
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Combien de commits ?", "repo": "requests"}'

# OpenAI compatible
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hyperion-rag",
    "messages": [{"role": "user", "content": "Analyse ce repository"}]
  }'
```

## 🏗️ Architecture

```
Hyperion/
├── src/hyperion/              # Code source principal
│   ├── api/                   # API Gateway v3.0
│   ├── cli/                   # Interface ligne de commande
│   ├── core/                  # Analyseur Git
│   ├── modules/               # Modules métier v3.0
│   │   ├── analytics/         # Moteur d'intelligence v2.9
│   │   ├── cache/             # Cache distribué v3.0
│   │   ├── gateway/           # API Gateway v3.0
│   │   ├── ml/                # Infrastructure ML v2.9
│   │   ├── monitoring/        # Monitoring v3.0
│   │   ├── rag/               # Pipeline RAG v2.9
│   │   └── security/          # Sécurité v3.0
│   └── utils/                 # Utilitaires
├── docs/                      # Documentation complète
├── scripts/                   # Scripts déploiement
├── tests/                     # Tests (189/189 passing)
└── frontend/                  # Dashboard React
```

## 📊 Qualité

* **Tests** : 189/189 passing (100%)
* **Linting** : 0 erreurs Ruff
* **Formatage** : 148 fichiers Black compliant
* **Type safety** : 95%+ annotations
* **Architecture** : 8 microservices validés

## 📚 Documentation

Documentation complète disponible dans `docs/` :
* **Cours** : guides utilisateur complets (français)
* **Technique** : architecture, déploiement, API, qualité code
* **Référence** : CLI, API endpoints, exemples

Points d'entrée :
* [Guide utilisateur](docs/cours/) - formation complète
* [Architecture v3.0](docs/technique/architecture/v3-enterprise-architecture.md)
* [Déploiement](docs/technique/architecture/deployment.md)
* [API Reference](docs/technique/reference/api-reference.md)

## 🔧 Prérequis

* Python 3.11+
* Docker (pour services)
* 8GB RAM minimum, 16GB recommandé
* Neo4j, Redis, Ollama (gérés par scripts)

## 🌟 Statut

* ✅ **Architecture v3.0** - microservices enterprise
* ✅ **Qualité code** - 0 erreurs, standards entreprise
* ✅ **Tests complets** - 189 tests, 100% pass rate
* ✅ **Documentation** - guides complets et référence API
* ✅ **Déploiement** - scripts orchestrés + Docker
* ✅ **Production ready** - architecture scalable et monitoring
