---
title: "Hyperion API - Backend FastAPI"
toc: true
description: "API REST pour interroger les données Hyperion."
weight: 2
---

API REST pour interroger les données Hyperion.

---

## 🚀 Démarrage rapide

### Installation
```bash
pip install fastapi uvicorn --break-system-packages
```

### Lancer l'API
```bash
cd /home/kortazo/Documents/Hyperion
python3 scripts/run_api.py
```

**API disponible sur** : http://localhost:8000  
**Documentation** : http://localhost:8000/docs

---

## 📡 Endpoints

### Général
- `GET /` - Informations API
- `GET /api/health` - Health check (API + Neo4j)

### Repositories
- `GET /api/repos` - Liste tous les repos analysés
- `GET /api/repos/{name}` - Détails complets d'un repo
- `GET /api/repos/{name}/contributors?limit=10` - Top contributeurs
- `GET /api/repos/{name}/hotspots?limit=10` - Top hotspots
- `GET /api/repos/{name}/metrics` - Métriques qualité

### Neo4j
- `GET /api/neo4j/repos/{name}` - Stats Neo4j d'un repo

---

## 📋 Exemples

### Liste repos
```bash
curl http://localhost:8000/api/repos
```

**Response** :
```json
{
  "repos": [
    {
      "name": "requests",
      "language": "python",
      "commits": 6379,
      "contributors": 770,
      "first_commit": "2011-02-13",
      "last_commit": "2025-10-15",
      "license": "Apache-2.0"
    }
  ],
  "count": 1
}
```

### Détails repo
```bash
curl http://localhost:8000/api/repos/requests
```

### Top contributeurs
```bash
curl http://localhost:8000/api/repos/requests/contributors?limit=5
```

### Métriques
```bash
curl http://localhost:8000/api/repos/requests/metrics
```

---

## 🔧 Configuration

L'API utilise la configuration Hyperion (`hyperion/config.py`) :
- Neo4j URI, credentials
- Chemins data directories

---

## 🌐 CORS

CORS activé pour :
- `http://localhost:3000` (React dev)
- `http://localhost:5173` (Vite dev)

---

## 🧪 Tests

```bash
# Health check
curl http://localhost:8000/api/health

# Devrait retourner :
{
  "status": "healthy",
  "api": "ok",
  "neo4j": "ok"
}
```

---

## 📚 Documentation interactive

FastAPI génère automatiquement :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

## 🎯 Prochaines étapes

Frontend React qui consomme cette API ! 🚀
