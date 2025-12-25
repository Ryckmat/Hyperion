# Guide d'Utilisation Complète - Hyperion v2.5.0 Enterprise Ready

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Installation et configuration](#installation-et-configuration)
3. [Utilisation CLI](#utilisation-cli)
4. [Infrastructure ML](#infrastructure-ml)
5. [API et intégrations](#api-et-intégrations)
6. [Dashboard et interfaces](#dashboard-et-interfaces)
7. [Dépannage et maintenance](#dépannage-et-maintenance)
8. [Exemples pratiques](#exemples-pratiques)

---

## Vue d'ensemble

Hyperion v2.5.0 Enterprise Ready est une plateforme d'analyse de code avancée qui combine :

- **Analyse Git intelligente** avec métriques approfondies
- **Infrastructure ML complète** avec prédiction de risques et détection d'anomalies
- **RAG (Retrieval Augmented Generation)** pour interrogation contextuelle
- **API OpenAI-compatible** pour intégration avec outils externes
- **Dashboard interactif** et interface conversationnelle

### Nouveautés v2.5.0

- ✅ **Infrastructure ML Enterprise** : MLflow, Feature Store, Training Pipeline
- ✅ **4 modèles ML opérationnels** : RiskPredictor, AnomalyDetector, ImpactAnalyzer, BugPredictor
- ✅ **35+ features ML** prêtes pour analyse avancée
- ✅ **138 tests validés** avec couverture complète
- ✅ **Standards entreprise** : Black/Ruff formatting

---

## Installation et configuration

### Prérequis système

```bash
# Vérifier les prérequis
python --version  # >= 3.10 requis
docker --version  # Pour Qdrant et Neo4j
git --version     # Pour analyse des repos
```

### Installation rapide

```bash
# 1. Cloner le projet
git clone https://github.com/Ryckmat/Hyperion.git
cd Hyperion

# 2. Installation Python
pip install -e . --break-system-packages

# 3. Vérification
hyperion --version
hyperion info
```

### Configuration avancée

```bash
# Variables d'environnement (optionnel)
export HYPERION_LOG_LEVEL=INFO
export HYPERION_ML_BACKEND=mlflow
export HYPERION_FEATURE_STORE_CACHE=true

# Configuration Neo4j (optionnel)
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=votre_password
```

### Vérification installation

```bash
# Test complet installation
python -m pytest tests/ -v
# Doit afficher : 138 tests PASSED

# Test CLI
hyperion info
# Doit afficher la configuration complète
```

---

## Utilisation CLI

### Commandes principales

```bash
# Aide générale
hyperion --help

# Version
hyperion --version

# Informations système
hyperion info
```

### Analyse d'un repository

```bash
# Analyse basique
hyperion profile /path/to/repo

# Analyse avec nom personnalisé
hyperion profile /path/to/repo --name="MonProjet"

# Analyse avec sortie spécifique
hyperion profile /path/to/repo --output=/tmp/analysis
```

**Exemple détaillé :**

```bash
# Analyser le repo actuel
hyperion profile . --name="Hyperion-Self-Analysis"

# Sortie attendue :
# 🔍 Analyse du dépôt : /home/user/Hyperion
# ✅ Analyse terminée !
#    • Repo          : Hyperion-Self-Analysis
#    • Commits       : 51
#    • Contributeurs : 1
#    • Profil YAML   : data/repositories/Hyperion-Self-Analysis/profile.yaml
```

### Génération de documentation

```bash
# Documentation Markdown
hyperion generate data/repositories/MonProjet/profile.yaml --format markdown

# Documentation HTML
hyperion generate data/repositories/MonProjet/profile.yaml --format html

# Sortie personnalisée
hyperion generate profile.yaml --format markdown --output=/tmp/docs
```

### Ingestion Neo4j

```bash
# Ingestion simple
hyperion ingest data/repositories/MonProjet/profile.yaml

# Ingestion avec nettoyage
hyperion ingest profile.yaml --clear

# Ingestion multiple
for profile in data/repositories/*/profile.yaml; do
    hyperion ingest "$profile"
done
```

### Export de données

```bash
# Export releases
hyperion export /path/to/repo

# Export avec filtre
hyperion export /path/to/repo --since="2024-01-01"
```

---

## Infrastructure ML

### Vue d'ensemble ML

Hyperion v2.5.0 inclut une infrastructure ML complète avec :

- **MLflow** : Tracking et registry de modèles
- **Feature Store** : Gestion centralisée des features
- **Training Pipeline** : Entraînement automatisé
- **Data Validator** : Validation et monitoring

### Utilisation Feature Store

```python
from hyperion.modules.ml.infrastructure.feature_store import FeatureStore

# Initialisation
feature_store = FeatureStore()

# Stockage de features
features = {
    'complexity_score': 0.75,
    'bug_history_count': 5,
    'test_coverage': 0.85
}
feature_store.store_features('mon-repo', features, source_file='analysis.py')

# Récupération de features
stored_features = feature_store.get_features('mon-repo')
print(f"Features disponibles : {len(stored_features)}")
```

### Entraînement de modèles

```python
from hyperion.modules.ml.training.training_pipeline import TrainingPipeline

# Initialisation pipeline
pipeline = TrainingPipeline()

# Entraînement modèle de risque
results = pipeline.train_risk_predictor()
print(f"Précision du modèle : {results['metrics']['accuracy']:.2%}")

# Sauvegarde automatique avec MLflow
model_uri = results.get('model_uri')
print(f"Modèle sauvé : {model_uri}")
```

### Prédiction de risques

```python
from hyperion.modules.impact.predictor import ImpactPredictor

# Prédiction sur fichier
predictor = ImpactPredictor()
risk_score = predictor.predict_risk('src/module/important.py')

print(f"Score de risque : {risk_score:.2%}")
if risk_score > 0.7:
    print("⚠️  Fichier à haut risque - Review recommandée")
```

### Détection d'anomalies

```python
from hyperion.modules.anomaly.detector import AnomalyDetector

# Analyse d'anomalies
detector = AnomalyDetector()
anomalies = detector.detect_anomalies('src/')

for anomaly in anomalies:
    print(f"🔍 {anomaly['file']} : {anomaly['type']} (score: {anomaly['score']:.2f})")
```

### Configuration ML

```yaml
# config/ml_config.yaml
models:
  risk_predictor:
    type: "RandomForest"
    hyperparameters:
      n_estimators: 100
      max_depth: 10
      random_state: 42

  anomaly_detector:
    type: "IsolationForest"
    hyperparameters:
      contamination: 0.1
      random_state: 42

features:
  target_features:
    - complexity_score
    - bug_history_count
    - test_coverage
    - commit_frequency
```

---

## API et intégrations

### Lancement de l'API

```bash
# API seule
python scripts/dev/run_api.py

# API avec dashboard
python scripts/dev/run_dashboard.py

# Orchestration complète
./scripts/deploy/hyperion_master.sh
```

### Endpoints disponibles

#### API Core
- `GET /` - Informations API
- `GET /api/health` - Health check
- `GET /api/repos` - Liste des repositories analysés
- `GET /api/repos/{repo_name}` - Détails d'un repository
- `POST /api/chat` - Chat RAG

#### API OpenAI-Compatible
- `GET /v1/models` - Liste des modèles
- `POST /v1/chat/completions` - Chat completions

### Utilisation API

```bash
# Test health check
curl http://localhost:8000/api/health

# Liste des repos
curl http://localhost:8000/api/repos | jq .

# Chat RAG
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hyperion-rag",
    "messages": [
      {"role": "user", "content": "Quels sont les fichiers les plus risqués ?"}
    ]
  }' | jq .
```

### Intégration Python

```python
import requests

# Client API
class HyperionClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_repos(self):
        response = requests.get(f"{self.base_url}/api/repos")
        return response.json()

    def chat(self, message):
        response = requests.post(f"{self.base_url}/v1/chat/completions", json={
            "model": "hyperion-rag",
            "messages": [{"role": "user", "content": message}]
        })
        return response.json()

# Utilisation
client = HyperionClient()
repos = client.get_repos()
print(f"Repositories analysés : {len(repos)}")

response = client.chat("Analyse le fichier le plus complexe")
print(response['choices'][0]['message']['content'])
```

---

## Dashboard et interfaces

### Lancement des interfaces

```bash
# Dashboard React (port 3000)
cd frontend
python -m http.server 3000

# Open WebUI (port 3001)
# Automatique via hyperion_master.sh

# API Documentation (port 8000)
# Disponible sur http://localhost:8000/docs
```

### Utilisation Open WebUI

1. **Accès** : http://localhost:3001
2. **Configuration** :
   - Modèle : `hyperion-rag`
   - Aucune clé API requise
3. **Requêtes exemples** :
   ```
   Quels sont les hotspots du repository ?
   Analyse les risques du fichier src/main.py
   Quels développeurs ont le plus contribué ?
   Détecte les anomalies dans le code
   ```

### Dashboard React

1. **Accès** : http://localhost:3000
2. **Fonctionnalités** :
   - Vue d'ensemble des repositories
   - Métriques en temps réel
   - Graphiques d'activité
   - Export de rapports

---

## Dépannage et maintenance

### Tests et validation

```bash
# Tests complets
python -m pytest tests/ -v

# Tests ML spécifiques
python -m pytest tests/unit/test_*ml* -v

# Tests API
python -m pytest tests/api/ -v

# Tests avec couverture
python -m pytest tests/ --cov=src/hyperion --cov-report=html
```

### Formatage et qualité

```bash
# Formatage Black
black src/ tests/ scripts/

# Vérification Ruff
ruff check src/ tests/ scripts/

# Correction automatique
ruff check --fix src/ tests/ scripts/
```

### Logs et monitoring

```bash
# Logs API
tail -f logs/api.log

# Logs ML
tail -f logs/ml/training.log

# Logs dashboard
tail -f logs/dashboard.log
```

### Nettoyage

```bash
# Nettoyage cache
rm -rf logs/ml/cache/
rm -rf data/ml/feature_store/cache/

# Reset MLflow
rm -rf mlruns/

# Nettoyage complet
make clean  # Si Makefile disponible
```

### Problèmes courants

**1. Tests ML échouent**
```bash
# Vérifier dépendances ML
python -c "import mlflow, sklearn, xgboost; print('OK')"

# Réinstaller dépendances
pip install -e . --force-reinstall
```

**2. API ne démarre pas**
```bash
# Vérifier port
lsof -i :8000

# Tuer processus existant
pkill -f "uvicorn.*hyperion"
```

**3. Features ML manquantes**
```bash
# Régénérer features
python -c "
from hyperion.modules.ml.infrastructure.feature_store import FeatureStore
fs = FeatureStore()
fs.rebuild_cache()
"
```

---

## Exemples pratiques

### Workflow complet d'analyse

```bash
#!/bin/bash
# Script d'analyse complète

REPO_PATH="/path/to/your/repo"
REPO_NAME="MyProject"

echo "🚀 Démarrage analyse complète de $REPO_NAME"

# 1. Profilage Git
echo "📊 Profilage Git..."
hyperion profile "$REPO_PATH" --name="$REPO_NAME"

# 2. Génération documentation
echo "📝 Génération documentation..."
hyperion generate "data/repositories/$REPO_NAME/profile.yaml" --format markdown

# 3. Ingestion Neo4j (optionnel)
echo "💾 Ingestion Neo4j..."
hyperion ingest "data/repositories/$REPO_NAME/profile.yaml"

# 4. Analyse ML
echo "🤖 Analyse ML..."
python -c "
from hyperion.modules.impact.predictor import ImpactPredictor
from hyperion.modules.anomaly.detector import AnomalyDetector

# Prédiction risques
predictor = ImpactPredictor()
risks = predictor.analyze_repository('$REPO_PATH')
print(f'Fichiers à haut risque : {len([r for r in risks if r[\"risk\"] > 0.7])}')

# Détection anomalies
detector = AnomalyDetector()
anomalies = detector.scan_repository('$REPO_PATH')
print(f'Anomalies détectées : {len(anomalies)}')
"

echo "✅ Analyse terminée !"
echo "🌐 Dashboard : http://localhost:3000"
echo "💬 Chat : http://localhost:3001"
echo "📚 API Docs : http://localhost:8000/docs"
```

### Monitoring continu

```python
#!/usr/bin/env python3
"""Script de monitoring continu Hyperion."""

import time
import schedule
from pathlib import Path
from hyperion.core.git_analyzer import GitAnalyzer
from hyperion.modules.ml.infrastructure.feature_store import FeatureStore

class HyperionMonitor:
    def __init__(self, repos_to_monitor):
        self.repos = repos_to_monitor
        self.feature_store = FeatureStore()

    def analyze_repo(self, repo_path):
        """Analyse périodique d'un repo."""
        print(f"🔍 Analyse de {repo_path}")

        analyzer = GitAnalyzer(repo_path)
        profile = analyzer.analyze()

        # Stockage des métriques
        features = {
            'commits_count': profile['git_summary']['commits'],
            'contributors_count': profile['git_summary']['contributors'],
            'recent_activity': profile['git_summary']['recent_commits_90d']
        }

        self.feature_store.store_features(
            repo_name=Path(repo_path).name,
            features=features,
            source_file='monitor'
        )

        print(f"✅ {Path(repo_path).name} analysé")

    def daily_analysis(self):
        """Analyse quotidienne."""
        for repo in self.repos:
            self.analyze_repo(repo)

    def weekly_report(self):
        """Rapport hebdomadaire."""
        print("📊 Génération rapport hebdomadaire...")
        # Logique de rapport

    def start_monitoring(self):
        """Démarrage du monitoring."""
        # Analyse quotidienne à 9h
        schedule.every().day.at("09:00").do(self.daily_analysis)

        # Rapport hebdomadaire le lundi à 8h
        schedule.every().monday.at("08:00").do(self.weekly_report)

        print("🚀 Monitoring démarré")
        while True:
            schedule.run_pending()
            time.sleep(60)

# Configuration
repos_to_monitor = [
    "/path/to/repo1",
    "/path/to/repo2"
]

monitor = HyperionMonitor(repos_to_monitor)
monitor.start_monitoring()
```

### Intégration CI/CD

```yaml
# .github/workflows/hyperion-analysis.yml
name: Hyperion Code Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  hyperion-analysis:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Nécessaire pour analyse Git complète

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Hyperion
      run: |
        pip install git+https://github.com/Ryckmat/Hyperion.git

    - name: Run Analysis
      run: |
        hyperion profile . --name="CI-Analysis-${{ github.sha }}"
        hyperion generate data/repositories/CI-Analysis-${{ github.sha }}/profile.yaml --format markdown

    - name: ML Risk Analysis
      run: |
        python -c "
        from hyperion.modules.impact.predictor import ImpactPredictor
        predictor = ImpactPredictor()
        risks = predictor.analyze_repository('.')
        high_risks = [r for r in risks if r['risk'] > 0.8]
        if high_risks:
            print(f'⚠️ {len(high_risks)} fichiers à très haut risque détectés')
            for risk in high_risks[:5]:  # Top 5
                print(f'  - {risk[\"file\"]}: {risk[\"risk\"]:.2%}')
            exit(1) if len(high_risks) > 10 else exit(0)
        "

    - name: Upload Analysis
      uses: actions/upload-artifact@v3
      with:
        name: hyperion-analysis
        path: docs/generated/
```

---

## Support et ressources

### Documentation
- **Guide Architecture** : `docs/architecture/architecture.md`
- **Plan v3.0** : `docs/v3.0-enterprise-plan.md`
- **API Reference** : http://localhost:8000/docs
- **Code Examples** : `scripts/dev/`

### Communauté
- **Issues GitHub** : [GitHub Issues](https://github.com/Ryckmat/Hyperion/issues)
- **Discussions** : [GitHub Discussions](https://github.com/Ryckmat/Hyperion/discussions)

### Maintenance
- **Tests réguliers** : `python -m pytest tests/`
- **Updates** : `git pull && pip install -e .`
- **Monitoring** : Logs dans `logs/`

---

**Hyperion v2.5.0 Enterprise Ready** - Analyse de code intelligente avec infrastructure ML complète.

Dernière mise à jour : 25 décembre 2024