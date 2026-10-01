---
title: "Déploiement Docker Hyperion"
toc: true
description: "Hyperion offre une solution de containerisation complète avec Docker et Docker Compose, permettant un déploiement simplifié et robuste de l'ensemble de la..."
weight: 1
---

## Vue d'ensemble

Hyperion offre une solution de containerisation complète avec Docker et Docker Compose, permettant un déploiement simplifié et robuste de l'ensemble de la stack.

## 📋 Prérequis

- **Docker** : 20.10+
- **Docker Compose** : 2.0+
- **Système** : Linux, macOS, Windows (WSL2)
- **RAM** : 8GB minimum, 16GB recommandé
- **Stockage** : 10GB libre minimum
- **GPU** : Optionnel (accélération CUDA)

## 🚀 Démarrage Rapide

### 1. Orchestrateur Principal

```bash
# Lancement complet automatique
./scripts/docker/hyperion-docker.sh --action up --profile core

# Vérification du statut
./scripts/docker/hyperion-docker.sh --action status

# Accès aux logs
./scripts/docker/hyperion-docker.sh --action logs hyperion-api
```

### 2. Profils Disponibles

#### Core (Recommandé pour débuter)
Services essentiels : API, Qdrant, Ollama
```bash
./scripts/docker/hyperion-docker.sh --action up --profile core
```

#### Full (Stack complète)
Tous les services : Core + Neo4j + Dashboard + WebUI
```bash
./scripts/docker/hyperion-docker.sh --action up --profile full
```

## 🏗️ Architecture des Services

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ hyperion-api    │ ── │   qdrant        │ ── │   ollama        │
│ (FastAPI)       │    │ (Vectors)       │    │   (LLM)         │
│ Port: 8000      │    │ Port: 6333      │    │ Port: 11434     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         └─────────────┬──────────────────────────────────┐
                       │                                  │
               ┌─────────────┐                   ┌─────────────┐
               │    neo4j    │                   │ hyperion-   │
               │ (Graph DB)  │                   │ dashboard   │
               │ Port: 7474  │                   │ Port: 3000  │
               └─────────────┘                   └─────────────┘
```

## ⚙️ Services Détaillés

### hyperion-api
- **Description** : API principale FastAPI
- **Port** : 8000
- **Health Check** : `http://localhost:8000/api/health`
- **Documentation** : `http://localhost:8000/docs`

### qdrant
- **Description** : Base de données vectorielle pour RAG
- **Port** : 6333
- **Dashboard** : `http://localhost:6333/dashboard`

### ollama
- **Description** : Serveur LLM local
- **Port** : 11434
- **Modèles** : llama3.2:1b, llama3.1:8b, qwen2.5:14b

### neo4j (Profile full)
- **Description** : Base de données graphe
- **Ports** : 7474 (HTTP), 7687 (Bolt)
- **Browser** : `http://localhost:7474`
- **Credentials** : neo4j/password

### hyperion-dashboard (Profile full)
- **Description** : Interface React
- **Port** : 3000

## 📂 Volumes et Persistance

```
./data/              # Données Hyperion
├── repositories/    # Repos analysés
├── ml/             # Modèles ML
└── logs/           # Logs applicatifs

./qdrant_data/      # Base vectorielle
./neo4j_data/       # Base graphe
./ollama_data/      # Modèles LLM
```

## 🔧 Configuration

### Variables d'Environnement

Créer un fichier `.env` :
```env
# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:1b

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# API Configuration
HYPERION_API_PORT=8000
HYPERION_DATA_DIR=/app/data
```

### Personnalisation docker-compose.yml

```yaml
# Ajouter des variables d'environnement
services:
  hyperion-api:
    environment:
      - CUSTOM_VAR=value

# Modifier les ports
  hyperion-api:
    ports:
      - "8080:8000"  # Port personnalisé
```

## 🧪 Tests et Validation

### Test Standalone
```bash
./scripts/docker/test-standalone.sh
```

Ce script teste :
- ✅ Build de l'image Docker
- ✅ CLI Hyperion fonctionnelle
- ✅ Imports Python
- ✅ API accessible

### Tests Manuels
```bash
# Health check
curl http://localhost:8000/api/health

# Test chat RAG
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello","repo":"test"}'

# Vérifier Qdrant
curl http://localhost:6333/health
```

## 🎯 Cas d'Usage

### Développement Local
```bash
# Mode core pour le développement
./scripts/docker/hyperion-docker.sh --action up --profile core

# Reload du code en développement
docker compose restart hyperion-api
```

### Production
```bash
# Mode full pour la production
./scripts/docker/hyperion-docker.sh --action up --profile full

# Monitoring des logs
./scripts/docker/hyperion-docker.sh --action logs --follow
```

### Analyse de Repository
```bash
# Analyser un repository
./scripts/docker/analyze-repo.sh /path/to/repo

# Avec modules spécifiques
./scripts/docker/analyze-repo.sh /path/to/repo --modules v2,rag
```

## 🔍 Dépannage

### Problèmes Courants

#### Port déjà utilisé
```bash
# Identifier les processus
lsof -i :8000
sudo kill -9 <PID>
```

#### Services ne démarrent pas
```bash
# Vérifier les logs
./scripts/docker/hyperion-docker.sh --action logs hyperion-api

# Reconstruire les images
./scripts/docker/hyperion-docker.sh --action build --no-cache
```

#### Problèmes de volumes
```bash
# Nettoyer les volumes
docker volume prune

# Recréer les volumes
./scripts/docker/hyperion-docker.sh --action down --volumes
./scripts/docker/hyperion-docker.sh --action up --profile core
```

### Logs Détaillés

```bash
# Tous les services
docker compose logs -f

# Service spécifique
docker compose logs -f hyperion-api

# Avec horodatage
docker compose logs -f -t
```

## 📊 Monitoring

### Métriques Système
```bash
# Utilisation des containers
docker stats

# Espace disque
docker system df
```

### Health Checks Automatiques

Les services incluent des health checks automatiques :
- **hyperion-api** : Test de l'endpoint `/api/health`
- **qdrant** : Test du port 6333
- **ollama** : Test du port 11434

## 🚀 Mise à l'Échelle

### Réplication Services
```yaml
# Dans docker-compose.yml
services:
  hyperion-api:
    deploy:
      replicas: 3
```

### Load Balancer
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 🔒 Sécurité

### Bonnes Pratiques
- Changer les mots de passe par défaut
- Utiliser des secrets Docker
- Limiter l'exposition des ports
- Utiliser des utilisateurs non-root

### Exemples
```yaml
# Secrets
secrets:
  neo4j_password:
    file: ./secrets/neo4j_password.txt

services:
  neo4j:
    secrets:
      - neo4j_password
```

## 📈 Performance

### Optimisations
- Utiliser des volumes nommés pour la performance
- Configurer la mémoire selon la charge
- Activer le support GPU si disponible

```yaml
# Support GPU
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 🆘 Support

Pour toute question sur le déploiement Docker :

1. **Documentation** : Ce guide et `/docs`
2. **Logs** : `./scripts/docker/hyperion-docker.sh --action logs`
3. **Tests** : `./scripts/docker/test-standalone.sh`
4. **Issues** : GitHub repository

---

**Hyperion** - Docker-Ready Enterprise Platform