# 🐳 Hyperion Docker v2.7 - Guide Complet

Ce guide vous explique comment utiliser Hyperion v2.7 avec Docker pour une expérience de déploiement simplifiée et reproductible.

## 🚀 Démarrage Rapide

### 1. Prérequis

- **Docker** ≥ 24.0
- **Docker Compose** ≥ 2.20
- **Git** pour cloner le projet
- **8GB RAM** minimum recommandé
- **GPU optionnel** pour améliorer les performances (Ollama + PyTorch)

### 2. Installation

```bash
# Cloner le projet
git clone https://github.com/Ryckmat/hyperion.git
cd hyperion

# Basculer sur la branche docker
git checkout v2.7-docker

# Démarrer la stack core (services essentiels)
./scripts/docker/hyperion-docker.sh

# OU démarrer la stack complète
./scripts/docker/hyperion-docker.sh --profile full
```

### 3. Premier test

```bash
# Analyser un repository
./scripts/docker/analyze-repo.sh /home/user/mon-projet

# Vérifier le statut
./scripts/docker/hyperion-docker.sh --action status

# Tester l'API
curl http://localhost:8000/api/health
```

---

## 📦 Architecture des Services

### Services Core (--profile core, par défaut)

| Service | Port | Description |
|---------|------|-------------|
| **qdrant** | 6333 | Vector database pour RAG |
| **ollama** | 11434 | LLM server local |
| **hyperion-api** | 8000 | API FastAPI principale |

### Services Full (--profile full)

Ajoute aux services core :

| Service | Port | Description |
|---------|------|-------------|
| **neo4j** | 7474/7687 | Graph database pour relations |
| **hyperion-dashboard** | 3000 | Frontend React |
| **open-webui** | 3001 | Interface chat avancée |

---

## 🛠️ Commandes Principales

### Gestion des Services

```bash
# Démarrer services essentiels
./scripts/docker/hyperion-docker.sh

# Démarrer tous les services
./scripts/docker/hyperion-docker.sh --profile full

# Arrêter tous les services
./scripts/docker/hyperion-docker.sh --action down

# Redémarrer un service spécifique
./scripts/docker/hyperion-docker.sh --action restart --service hyperion-api

# Voir les logs
./scripts/docker/hyperion-docker.sh --action logs --follow

# Vérifier le statut
./scripts/docker/hyperion-docker.sh --action status
```

### Configuration Initiale

```bash
# Télécharger les modèles LLM
./scripts/docker/hyperion-docker.sh --action setup

# Rebuilder les images
./scripts/docker/hyperion-docker.sh --action build

# Démarrer avec rebuild
./scripts/docker/hyperion-docker.sh --build
```

### Analyse de Repositories

```bash
# Analyser un repository complet
./scripts/docker/analyze-repo.sh /path/to/repository

# Analyser avec modules spécifiques
./scripts/docker/analyze-repo.sh /path/to/repo --modules v2,rag

# Analyser sans redémarrer les services
./scripts/docker/analyze-repo.sh /path/to/repo --skip-start
```

---

## 🔧 Configuration

### Variables d'Environnement

Principales variables configurables dans `docker-compose.yml` :

```yaml
# Configuration Qdrant
- QDRANT_HOST=qdrant
- QDRANT_PORT=6333
- QDRANT_COLLECTION=hyperion_repos

# Configuration Ollama
- OLLAMA_BASE_URL=http://ollama:11434
- OLLAMA_MODEL=llama3.2:1b

# Configuration LLM
- LLM_TEMPERATURE=0.0
- LLM_MAX_TOKENS=128
- LLM_TIMEOUT=10

# Configuration Embeddings
- EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
- EMBEDDING_DEVICE=cpu  # ou 'cuda' avec GPU

# Configuration Neo4j (profil full)
- NEO4J_URI=bolt://neo4j:7687
- NEO4J_USER=neo4j
- NEO4J_PASSWORD=hyperion123
```

### Volumes Persistants

```bash
# Voir les volumes
docker volume ls | grep hyperion

# Volumes principaux:
# - hyperion_data        -> Données et profils
# - qdrant_storage      -> Base vectorielle
# - ollama_models       -> Modèles LLM
# - neo4j_data         -> Graph database
```

### Modèles LLM Disponibles

```bash
# Modèles supportés (configurez OLLAMA_MODEL):
llama3.2:1b       # Rapide: <3s (défaut)
llama3.1:8b       # Équilibré: 5-10s
qwen2.5:14b       # Premium: 10-30s
qwen2.5:32b       # Expert: 30s+
```

---

## 🏗️ Développement

### Structure Docker

```
hyperion/
├── Dockerfile                 # Image principale Hyperion
├── docker-compose.yml         # Orchestration services
├── .dockerignore              # Exclusions build
├── scripts/docker/
│   ├── hyperion-docker.sh     # Script principal
│   └── analyze-repo.sh        # Script analyse
└── README-docker.md           # Ce guide
```

### Développement Local

```bash
# Build image de développement
docker compose build hyperion-api

# Monter code local pour dev
# Modifiez docker-compose.yml:
volumes:
  - ./src:/app/src  # Mount code pour hot-reload
```

### Debug et Logs

```bash
# Logs service spécifique
docker compose logs hyperion-api

# Logs en temps réel
docker compose logs -f

# Entrer dans un container
docker compose exec hyperion-api bash

# Débugger l'API
docker compose exec hyperion-api python -c "
from hyperion.api.main import app
print('API démarrée')
"
```

---

## 📊 Utilisation

### URLs d'Accès

**Services Core:**
- API Hyperion : http://localhost:8000
- API Docs : http://localhost:8000/docs
- Health Check : http://localhost:8000/api/health
- Qdrant : http://localhost:6333

**Services Full (avec --profile full):**
- Neo4j Browser : http://localhost:7474
- Dashboard : http://localhost:3000
- Open WebUI : http://localhost:3001

### Exemples d'API

```bash
# Health check
curl http://localhost:8000/api/health

# Lister les repos analysés
curl http://localhost:8000/api/repos

# Fonctions d'un repository
curl "http://localhost:8000/api/v2/repos/requests/functions?limit=5"

# Chat RAG
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Combien de fichiers Python ?","repo":"requests"}'

# Analyse d'impact
curl -X POST http://localhost:8000/api/v2/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo":"requests","file":"requests/api.py","changes":["modification"]}'
```

### Workflow Complet

1. **Démarrage:**
   ```bash
   ./scripts/docker/hyperion-docker.sh --profile full
   ```

2. **Analyse d'un repository:**
   ```bash
   ./scripts/docker/analyze-repo.sh /home/user/mon-projet
   ```

3. **Utilisation de l'API:**
   - Documentation : http://localhost:8000/docs
   - Chat RAG : http://localhost:3001

4. **Arrêt:**
   ```bash
   ./scripts/docker/hyperion-docker.sh --action down
   ```

---

## 🔍 Dépannage

### Problèmes Courants

**Erreur "port already in use":**
```bash
# Vérifier les ports utilisés
sudo netstat -tulpn | grep :8000

# Arrêter les services conflictuels
./scripts/docker/hyperion-docker.sh --action down
```

**API ne répond pas:**
```bash
# Vérifier les logs
./scripts/docker/hyperion-docker.sh --action logs --service hyperion-api

# Redémarrer l'API
./scripts/docker/hyperion-docker.sh --action restart --service hyperion-api
```

**Ollama ne télécharge pas de modèles:**
```bash
# Vérifier l'espace disque
df -h

# Redémarrer Ollama
docker compose restart ollama

# Télécharger manuellement
docker compose exec ollama ollama pull llama3.2:1b
```

**Repository non trouvé:**
```bash
# Vérifier le mount point
# Le docker-compose.yml monte: /home/kortazo/Documents:/mnt/repositories
# Vos repositories doivent être dans /home/kortazo/Documents/
```

### Performance

**GPU Support:**
```bash
# Installer NVIDIA Container Toolkit
# Décommenter dans docker-compose.yml:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]

# Changer EMBEDDING_DEVICE=cuda
```

**Mémoire:**
```bash
# Augmenter mémoire Docker si nécessaire
# Docker Desktop > Settings > Resources > Memory: 8GB+
```

---

## 📚 Documentation

- **API Documentation:** http://localhost:8000/docs
- **Architecture:** [docs/architecture/README.md](docs/architecture/README.md)
- **Version native:** [scripts/deploy/hyperion_master.sh](scripts/deploy/hyperion_master.sh)

## 🤝 Support

Pour les problèmes Docker spécifiques, créez une issue sur le repository avec :
- Version Docker : `docker --version`
- Version Compose : `docker compose version`
- Logs : `./scripts/docker/hyperion-docker.sh --action logs`
- Système : `uname -a`

---

**🎯 Hyperion v2.7 Docker est prêt pour la production !**