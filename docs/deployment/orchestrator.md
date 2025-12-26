# 🎭 Orchestrateur Master Hyperion

## Vue d'ensemble

L'orchestrateur master (`scripts/deploy/hyperion_master.sh`) est le script principal de déploiement et gestion d'Hyperion. Il automatise l'installation, la configuration et le lancement de tous les composants de la plateforme.

## 🚀 Utilisation

### Commandes Principales

```bash
# Aide complète
./scripts/deploy/hyperion_master.sh --help

# Mode automatique (recommandé)
./scripts/deploy/hyperion_master.sh --auto

# Configuration interactive des modèles
./scripts/deploy/hyperion_master.sh --setup-model

# Lancement avec modèle spécifique
./scripts/deploy/hyperion_master.sh --model llama3.2:1b

# Mode verbose pour debug
./scripts/deploy/hyperion_master.sh --auto --verbose
```

## ⚙️ Options Détaillées

| Option | Description | Exemple |
|--------|-------------|---------|
| `--auto` | Mode automatique sans interaction | `--auto` |
| `--setup-model` | Configuration interactive des modèles LLM | `--setup-model` |
| `--model MODEL` | Spécifier un modèle LLM directement | `--model llama3.1:8b` |
| `--skip-deps` | Ignorer la vérification des dépendances | `--skip-deps` |
| `--force` | Forcer les opérations même en cas d'erreur | `--force` |
| `--verbose` | Logs détaillés | `--verbose` |
| `--dry-run` | Simulation sans exécution | `--dry-run` |
| `--help` | Afficher l'aide | `--help` |

## 🎯 Profils de Modèles

### Configuration Interactive
```bash
./scripts/deploy/hyperion_master.sh --setup-model
```

Profils disponibles :
1. **🏃‍♂️ Performance Ultra-Rapide** (`llama3.2:1b`)
   - Temps de réponse : <3s
   - Usage mémoire : ~2GB
   - Cas d'usage : Exploration rapide, prototypage

2. **⚖️ Équilibre Performance/Qualité** (`llama3.1:8b`)
   - Temps de réponse : 5-10s
   - Usage mémoire : ~8GB
   - Cas d'usage : Usage quotidien, développement

3. **🧠 Qualité Premium** (`qwen2.5:14b`)
   - Temps de réponse : 10-30s
   - Usage mémoire : ~14GB
   - Cas d'usage : Analyses complexes, entreprise

4. **🚀 Expert/Recherche** (`qwen2.5:32b`)
   - Temps de réponse : 30s+
   - Usage mémoire : ~32GB
   - Cas d'usage : Recherche, analyses critiques

## 🔧 Étapes d'Exécution

L'orchestrateur exécute les étapes suivantes :

### 1. Vérification Système
- ✅ Dépendances système (Python, Git, Docker)
- ✅ Versions des composants
- ✅ Espace disque disponible
- ✅ Ports réseau libres

### 2. Installation Dépendances
```bash
# Dépendances Python
pip install -r requirements.txt

# Installation package Hyperion
pip install -e .

# Modèles LLM (selon profil)
ollama pull llama3.2:1b  # ou autre modèle
```

### 3. Configuration Services
- **Qdrant** : Base vectorielle (port 6333)
- **Ollama** : Serveur LLM (port 11434)
- **Neo4j** : Base graphe (ports 7474/7687)
- **API** : FastAPI Hyperion (port 8000)

### 4. Tests de Validation
- Health checks des services
- Test de connectivity RAG
- Validation des endpoints API
- Vérification des modèles LLM

## 📊 Monitoring et Logs

### Logs Détaillés
```bash
# Mode verbose pour debug complet
./scripts/deploy/hyperion_master.sh --auto --verbose

# Logs sauvés dans
tail -f logs/hyperion_master.log
```

### Status des Services
L'orchestrateur affiche l'état des services :
```
🟢 Qdrant      : http://localhost:6333 (RUNNING)
🟢 Ollama      : http://localhost:11434 (RUNNING)
🟢 Neo4j       : http://localhost:7474 (RUNNING)
🟢 API         : http://localhost:8000 (RUNNING)
```

## 🎮 Scénarios d'Usage

### Développement Local

#### Premier lancement
```bash
# Installation complète automatique
./scripts/deploy/hyperion_master.sh --auto
```

#### Changement de modèle
```bash
# Reconfigurer le modèle LLM
./scripts/deploy/hyperion_master.sh --setup-model

# Ou directement
./scripts/deploy/hyperion_master.sh --model llama3.1:8b
```

#### Debug et dépannage
```bash
# Mode verbose pour diagnostique
./scripts/deploy/hyperion_master.sh --auto --verbose

# Forcer la réinstallation
./scripts/deploy/hyperion_master.sh --auto --force
```

### Déploiement Production

#### Configuration standard
```bash
# Profil équilibré pour production
echo "2" | ./scripts/deploy/hyperion_master.sh --setup-model

# Lancement automatique
./scripts/deploy/hyperion_master.sh --auto
```

#### Validation complète
```bash
# Test en mode simulation
./scripts/deploy/hyperion_master.sh --dry-run

# Puis lancement réel
./scripts/deploy/hyperion_master.sh --auto --verbose
```

### CI/CD Integration

```bash
#!/bin/bash
# Script CI/CD

# Mode automatique non-interactif
export HYPERION_AUTO_MODE=1
export OLLAMA_MODEL="llama3.1:8b"

./scripts/deploy/hyperion_master.sh --auto --skip-deps
```

## 🔍 Dépannage

### Problèmes Courants

#### Services ne démarrent pas
```bash
# Vérifier les ports occupés
netstat -tlnp | grep ':8000\|:6333\|:11434\|:7474'

# Killer les processus
./scripts/deploy/hyperion_master.sh --force
```

#### Modèle LLM non trouvé
```bash
# Reconfigurer le modèle
./scripts/deploy/hyperion_master.sh --setup-model

# Ou télécharger manuellement
ollama pull llama3.2:1b
```

#### Erreurs de dépendances
```bash
# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# Mode force
./scripts/deploy/hyperion_master.sh --auto --force
```

### Codes de Retour

| Code | Signification |
|------|---------------|
| 0 | Succès complet |
| 1 | Erreur de dépendances |
| 2 | Erreur de configuration |
| 3 | Erreur de service |
| 4 | Erreur de validation |

## 🚀 Optimisations

### Performance
```bash
# Utiliser un modèle rapide pour développement
./scripts/deploy/hyperion_master.sh --model llama3.2:1b

# Mode production avec GPU
CUDA_VISIBLE_DEVICES=0 ./scripts/deploy/hyperion_master.sh --auto
```

### Ressources
```bash
# Limiter l'usage mémoire d'Ollama
export OLLAMA_MAX_MEMORY=8GB
./scripts/deploy/hyperion_master.sh --auto
```

## 🔧 Configuration Avancée

### Variables d'Environnement

```bash
# Configuration personnalisée
export HYPERION_API_PORT=8080
export QDRANT_PORT=6334
export OLLAMA_PORT=11435
export NEO4J_HTTP_PORT=7475

./scripts/deploy/hyperion_master.sh --auto
```

### Hooks Personnalisés

Créer `scripts/deploy/hooks/` pour des actions personnalisées :
- `pre_install.sh` : Avant installation
- `post_install.sh` : Après installation
- `pre_start.sh` : Avant démarrage services
- `post_start.sh` : Après démarrage services

## 📈 Métriques et Monitoring

### Métriques Exposées
- Temps de démarrage des services
- Usage mémoire par composant
- Temps de réponse des health checks
- Statut des modèles LLM

### Intégration Monitoring
```bash
# Export métriques Prometheus
export HYPERION_METRICS_ENABLED=1
./scripts/deploy/hyperion_master.sh --auto
```

## 🆘 Support

### Diagnostique Automatique
```bash
# Rapport de diagnostic complet
./scripts/deploy/hyperion_master.sh --diagnose

# Health check approfondi
./scripts/deploy/hyperion_master.sh --health-check
```

### Contact Support
- **Logs** : `logs/hyperion_master.log`
- **Configuration** : `.hyperion/config.yaml`
- **État services** : `curl http://localhost:8000/api/health`

---

**Note** : L'orchestrateur master est l'interface principale recommandée pour gérer Hyperion en mode traditionnel (non-Docker). Pour le déploiement Docker, voir [Docker Deployment](README.md).