---
title: "Infrastructure ML Hyperion"
toc: true
description: "Version : **Platform**: Machine Learning Infrastructure"
weight: 1
---

**Version**: **Platform**: Machine Learning Infrastructure

---

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture ML](#architecture-ml)
- [Feature Store](#feature-store)
- [Training Pipeline](#training-pipeline)
- [Model Registry](#model-registry)
- [Data Validator](#data-validator)
- [MLflow Integration](#mlflow-integration)
- [Modèles ML](#modèles-ml)
- [Feature Engineering](#feature-engineering)
- [Utilisation pratique](#utilisation-pratique)

---

## 🎯 Vue d'ensemble

L'infrastructure ML de Hyperion est conçue comme une plateforme **Enterprise-grade** pour :

1. **Extraire et ingénier** 35+ features à partir de données Git et code
2. **Entraîner automatiquement** 4 modèles ML + ensemble pour prédictions
3. **Valider et surveiller** la qualité des données avec drift detection
4. **Versionner et déployer** les modèles avec MLflow
5. **Prédire les risques** et détecter les anomalies en temps réel

### Composants Clés

```
Infrastructure ML
├── Feature Store (35+ features)
├── Training Pipeline (4 models + ensemble)
├── Model Registry (MLflow integration)
├── Data Validator (quality + drift detection)
└── ML Config (hyperparameters centralisés)
```

---

## 🏗️ Architecture ML

### Structure des Modules

```
src/hyperion/modules/ml/
├── infrastructure/
│   ├── feature_store.py      # Stockage features + cache TTL
│   ├── model_registry.py     # Registry modèles + versioning
│   ├── data_validator.py     # Validation + drift detection
│   ├── ml_config.py          # Configuration centralisée
│   └── ml_environment.py     # Environment setup
├── training/
│   ├── training_pipeline.py  # Pipeline complet entraînement
│   └── feature_engineer.py   # Engineering 35+ features
└── tests/
    └── test_*.py             # Tests complets (16 fichiers)
```

### Flux de Données ML

```
Raw Git Data
     ↓
Feature Engineering (35+ features)
     ↓
Feature Store (cache + TTL)
     ↓
Data Validation (quality + drift)
     ↓
Training Pipeline (4 models)
     ↓
Model Registry (MLflow)
     ↓
Production Deployment
```

---

## 📦 Feature Store

### Capabilities

Le **Feature Store** d'Hyperion gère 35+ features avec :

- **Cache intelligent** avec TTL (24h par défaut)
- **Versioning automatique** basé sur contenu
- **Métadonnées complètes** (source, timestamp, hash)
- **Cleanup automatique** des features expirées
- **Search et filter** par repository/tags

### Structure de Stockage

```
data/ml/feature_store/
├── cache/                      # Features sérialisées (pickle)
│   └── {feature_set_id}.pkl
└── metadata/                   # Métadonnées JSON
    └── {feature_set_id}_metadata.json
```

### API Feature Store

```python
from hyperion.modules.ml.infrastructure.feature_store import FeatureStore

store = FeatureStore()

# Stocker features
feature_set_id = store.store_features(
    features_dict=features,
    source_file="requests/models.py",
    repository="requests",
    tags={"version": "1.0", "type": "risk"}
)

# Récupérer features
features = store.get_features(feature_set_id)

# Rechercher features
results = store.search_features(
    repository="requests",
    tags={"type": "risk"}
)

# Stats globales
stats = store.get_feature_statistics()
```

### Métadonnées Trackées

```python
class FeatureMetadata:
    feature_set_id: str              # ID unique (UUID)
    source_file: str                 # Fichier source
    repository: str                  # Repository
    extracted_at: datetime           # Timestamp extraction
    feature_names: list[str]         # Noms des 35+ features
    n_features: int                  # Nombre total
    content_hash: str                # Hash SHA256 du contenu
    source_hash: str                 # Hash MD5 du fichier source
    tags: dict[str, str]             # Tags personnalisés
    extraction_time_ms: float        # Performance extraction
    extraction_version: str = "3.0.0" # Version du feature engineering
```

---

## 🚀 Training Pipeline

### Vue d'ensemble

Le **Training Pipeline** orchestre l'entraînement de **4 modèles ML** + ensemble :

1. **Random Forest** - Prédiction de risques
2. **XGBoost** - Prédiction de risques (optimisé)
3. **Isolation Forest** - Détection d'anomalies
4. **Meta-learner** - Ensemble voting (LogisticRegression)

### Pipeline Complet

```python
from hyperion.modules.ml.training.training_pipeline import TrainingPipeline

pipeline = TrainingPipeline()

# Entraînement complet
result = pipeline.train_risk_predictor(
    data_file="data/ml/features.csv",
    target_column="risque_reel",
    test_size=0.2,
    cv_folds=5
)

print(f"Best model: {result['best_model']['name']} (F1: {result['best_model']['f1']:.3f})")
```

### Étapes du Pipeline

```
1. Data Validation & Preparation
   ├── Validate structure (min 10 samples)
   ├── Check for duplicates
   ├── Handle missing values
   └── Type conversion & cleaning

2. Feature/Target Separation
   ├── X: all columns except target
   └── y: target column

3. Train/Test Split
   ├── Stratified split (20% test)
   ├── Random state: 42
   └── Preserve class distribution

4. Model Training (parallel possible)
   ├── Random Forest (n_estimators=100, max_depth=10)
   ├── XGBoost (n_estimators=100, max_depth=8, lr=0.1)
   ├── Isolation Forest (contamination=0.1)
   └── Meta-learner (LogisticRegression)

5. Cross-Validation
   ├── 5-fold stratified CV
   ├── Metrics: accuracy, precision, recall, f1
   └── Feature importance extraction

6. MLflow Logging
   ├── Model registry + versioning
   ├── Hyperparameters logging
   ├── Metrics logging
   └── Artifacts storage
```

### Résultats Retournés

```python
{
    "training_time_seconds": 45.2,
    "validation_result": ValidationResult,
    "models_results": {
        "random_forest": {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.92,
            "f1": 0.92,
            "feature_importance": {...}
        },
        "xgboost": {...},
        "isolation_forest": {...},
        "meta_learner": {...}
    },
    "best_model": {
        "name": "xgboost",
        "f1": 0.94,
        "accuracy": 0.96
    },
    "ensemble_performance": {...},
    "feature_names": ["feature1", "feature2", ...],
    "training_samples": 800,
    "test_samples": 200
}
```

---

## 📚 Model Registry

### Capabilities

Le **Model Registry** gère le cycle de vie complet des modèles :

- **Versioning sémantique** automatique (v1.0.0, v1.1.0, ...)
- **Statuts de promotion** : trained → validated → production → deprecated
- **Métadonnées complètes** : métriques, hyperparamètres, features, timestamp
- **Sérialisation sécurisée** : pickle + JSON metadata
- **MLflow integration** : tracking automatique

### API Model Registry

```python
from hyperion.modules.ml.infrastructure.model_registry import ModelRegistry

registry = ModelRegistry()

# Sauvegarder modèle
version = registry.save_model(
    model=trained_model,
    name="risk_predictor",
    model_type="XGBoost",
    metadata={
        "accuracy": 0.95,
        "f1_score": 0.93,
        "training_features": ["feature1", "feature2"],
        "training_samples": 1000
    }
)

# Charger modèle
model, metadata = registry.load_model(
    name="risk_predictor",
    version="latest",  # ou version spécifique "v1.0.0"
    return_metadata=True
)

# Promouvoir modèle
registry.promote_model(
    name="risk_predictor",
    version="v1.0.0",
    status="production"
)

# Lister modèles
models = registry.list_models()
```

### Métadonnées Modèle

```python
class ModelMetadata:
    name: str                          # Nom du modèle
    version: str                       # Version sémantique
    model_type: str                    # Type (RandomForest, XGBoost, etc)
    created_at: datetime               # Timestamp création
    created_by: str = "hyperion-ml"   # Créateur

    # Métriques performance
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None

    # Entraînement
    training_features: list[str]       # Noms des features utilisées
    training_samples: int              # Nombre d'échantillons d'entraînement
    hyperparameters: dict[str, Any]    # Hyperparamètres du modèle

    # Statut et validation
    status: str = "trained"           # trained|validated|production|deprecated
    validation_results: dict[str, Any] # Résultats validation croisée

    # Métadonnées additionnelles
    tags: dict[str, str]              # Tags personnalisés
    description: str | None           # Description optionnelle
```

### Structure Stockage

```
modeles/
├── risk_predictor_v1.0.0.pkl         # Modèle sérialisé
├── risk_predictor_v1.1.0.pkl
├── anomaly_detector_v1.0.0.pkl
└── metadata/
    ├── risk_predictor_v1.0.0_metadata.json
    ├── risk_predictor_v1.1.0_metadata.json
    └── anomaly_detector_v1.0.0_metadata.json
```

---

## ✅ Data Validator

### Capabilities

Le **Data Validator** garantit la qualité des données avec :

- **Validation structure** : taille minimale, duplicatas
- **Validation features** : features manquantes/supplémentaires, types
- **Validation qualité** : valeurs manquantes, outliers
- **Validation target** : classes, déséquilibre
- **Data drift detection** : comparaison distributions

### Validations Effectuées

```python
class DataValidator:

    def validate_structure(self, df):
        """Validate basic data structure"""
        ✓ Minimum 10 samples
        ✓ No duplicate rows detection
        ✓ Valid DataFrame format

    def validate_features(self, df, expected_features):
        """Validate feature presence and coverage"""
        ✓ All expected features present
        ✓ No unexpected features (warning)
        ✓ Feature coverage > threshold per feature

    def validate_data_quality(self, df):
        """Validate overall data quality"""
        ✓ Global missing values < 20%
        ✓ Per-feature missing analysis
        ✓ Numeric data types validation

    def validate_target(self, df, target_column):
        """Validate target variable"""
        ✓ No missing values in target
        ✓ Minimum 2 unique classes
        ✓ Class balance detection

    def validate_distributions(self, df):
        """Validate feature distributions"""
        ✓ No constant features
        ✓ Outlier detection (> 3 IQR)
        ✓ Distribution sanity checks
```

### API Data Validator

```python
from hyperion.modules.ml.infrastructure.data_validator import DataValidator

validator = DataValidator()

# Validation simple
result = validator.validate_dataframe(
    df=data,
    target_column="risque_reel"
)

if result.is_valid:
    print("✅ Data validation passed")
else:
    print("❌ Data validation failed:")
    for error in result.errors:
        print(f"  - {error}")

# Validation + préparation automatique
df_clean, result = validator.validate_and_prepare_data(
    df=raw_data,
    target_column="risque_reel",
    fix_issues=True  # Auto-fix when possible
)

# Data drift detection
drift_report = validator.detect_data_drift(
    reference_df=train_data,
    current_df=new_data,
    threshold=0.1  # 10% difference threshold
)
```

### Résultat de Validation

```python
class ValidationResult:
    is_valid: bool                     # Global validation status
    warnings: list[str]                # Non-critical warnings
    errors: list[str]                  # Critical errors
    suggestions: list[str]             # Improvement suggestions

    # Statistics
    n_samples: int                     # Total number of samples
    n_features: int                    # Total number of features
    missing_percentage: float          # Global missing percentage
    duplicate_percentage: float        # Duplicate rows percentage

    # Feature quality
    feature_coverage: dict[str, float] # Coverage per feature
    feature_types: dict[str, str]      # Detected types per feature

    # Target analysis
    target_classes: list               # Unique target classes
    target_balance: dict               # Class distribution
```

---

## 🔮 Modèles ML

### 1. RiskPredictor (Ensemble)

**Objectif** : Prédire le niveau de risque d'un changement de code

**Architecture** : Ensemble Random Forest + XGBoost + Meta-learner

```python
# Configuration
random_forest_config = {
    "n_estimators": 100,
    "max_depth": 10,
    "class_weight": "balanced",
    "random_state": 42
}

xgboost_config = {
    "n_estimators": 100,
    "max_depth": 8,
    "learning_rate": 0.1,
    "random_state": 42
}

meta_learner_config = {
    "solver": "liblinear",
    "random_state": 42
}
```

**Features utilisées** : 35+ (code quality, team dynamics, business impact, temporal)

**Performance typique** :
- Accuracy: 92-95%
- F1-score: 90-94%
- Precision: 89-93%
- Recall: 91-95%

### 2. AnomalyDetector

**Objectif** : Détecter les anomalies et code smells

**Architecture** : Isolation Forest

```python
# Configuration
isolation_forest_config = {
    "contamination": 0.1,        # 10% contamination expected
    "max_samples": 256,          # Subsample size
    "random_state": 42,
    "n_jobs": -1                 # Use all cores
}
```

**Features utilisées** : Principalement code quality + complexity metrics

**Output** :
- Anomaly score: [-1, 1] (plus négatif = plus anormal)
- Binary prediction: 1 (normal), -1 (anomalie)

### 3. BugPredictor

**Objectif** : Prédire la probabilité de bugs dans les 30 prochains jours

**Architecture** : XGBoost avec split temporel

```python
# Configuration
bug_predictor_config = {
    "n_estimators": 200,
    "max_depth": 8,
    "learning_rate": 0.1,
    "random_state": 42,
    "eval_metric": "logloss"
}
```

**Features utilisées** : Historical + temporal + code quality

**Entraînement** :
- Split temporel : 80% passé, 20% futur
- Horizon de prédiction : 30 jours
- Validation : Time-series cross-validation

### 4. ImpactAnalyzer

**Objectif** : Prédire l'impact d'un changement sur l'écosystème code

**Architecture** : Ensemble de modèles selon contexte

**Features utilisées** : Dependency graph + change history + file metrics

**Output** :
- Impact score: [0, 1] (0 = impact minimal, 1 = impact maximal)
- Affected components: list des composants potentiellement affectés
- Risk level: LOW/MEDIUM/HIGH

### 5. Meta-learner (Ensemble)

**Objectif** : Agréger les prédictions des modèles de base

**Architecture** : Logistic Regression sur les prédictions des modèles de base

```python
# Input features pour meta-learner
meta_features = [
    "random_forest_prediction",      # Prédiction RF
    "random_forest_confidence",      # Confiance RF
    "xgboost_prediction",           # Prédiction XGBoost
    "xgboost_confidence"            # Confiance XGBoost
]
```

**Avantages** :
- Combine les forces des différents modèles
- Améliore la robustesse des prédictions
- Réduit la variance des prédictions individuelles

---

## ⚙️ Feature Engineering

### 35+ Features Extraites

Le **Feature Engineer** d'Hyperion extrait et calcule 35+ features réparties en 5 catégories :

#### 1. Code Quality (12 features)

```python
# Complexity metrics
"complexite_cyclomatique"      # McCabe cyclomatic complexity
"complexite_cognitive"         # Cognitive complexity
"complexite_npath"            # NPath complexity
"indice_maintenabilite"       # Maintainability index

# Size metrics
"lignes_code"                 # Lines of code
"nb_methodes"                 # Number of methods
"nb_classes"                  # Number of classes

# Documentation
"densite_commentaires"        # Comment density ratio

# Test coverage
"delta_couverture_tests"      # Test coverage change

# OOP metrics
"profondeur_heritage"         # Inheritance depth
"couplage_entrant"            # Afferent coupling
"cohesion_classe"             # Class cohesion
```

#### 2. Team Dynamics (8 features)

```python
# Contribution patterns
"frequence_commits"           # Commits frequency per period
"nb_contributeurs_uniques"    # Number of unique contributors
"distribution_connaissance"   # Knowledge distribution (bus factor)
"facteur_bus"                 # Bus factor percentage

# Developer experience
"experience_auteur"           # Author experience (months)
"experience_moyenne_reviewers" # Average reviewers experience

# Review process
"vitesse_approbation"         # Average approval time (hours)
"nb_discussions_pr"           # Number of PR discussions
```

#### 3. Business Impact (4 features)

```python
# User impact
"estimation_trafic_affecte"   # % of affected user traffic
"score_impact_revenus"        # Revenue impact score [0-1]

# System criticality
"niveau_criticite_module"     # Module criticality level [1-5]
"difficulte_rollback"         # Rollback difficulty score [0-1]
```

#### 4. Historical (6 features)

```python
# File history
"age_fichier_jours"           # File age in days
"nb_bugs_historiques"         # Historical bug count
"frequence_rollbacks"         # Historical rollback frequency
"nb_hotfixes"                 # Historical hotfix count
"volatilite_fichier"          # File change rate

# Dependency depth
"profondeur_dependances"      # Dependency nesting depth
```

#### 5. Temporal (5+ features)

```python
# Dependency analysis
"nb_dependances_circulaires"  # Circular dependencies count
"nb_deps_externes"            # External dependencies count
"nb_conflits_versions"        # Version conflicts count

# Breaking changes
"risque_breaking_changes"     # Breaking changes risk [0-1]

# Architecture metrics
"fan_in_fan_out"              # Fan-in/Fan-out ratio
```

### Pipeline Feature Engineering

```python
from hyperion.modules.ml.training.feature_engineer import FeatureEngineer

engineer = FeatureEngineer()

# Feature engineering complet
features = engineer.engineer_full_feature_set(
    raw_data=git_profile_data,
    requested_features=[
        "complexite_cyclomatique",
        "frequence_commits",
        "estimation_trafic_affecte",
        "age_fichier_jours",
        "nb_dependances_circulaires"
    ]
)

print(f"✅ Extracted {len(features)} features")
```

### Méthodes Disponibles

| Méthode | Input | Output | Description |
|---------|-------|--------|-------------|
| `extract_basic_features()` | raw_dict | basic_features | Features de base extraites |
| `engineer_temporal_features()` | data + dates | temporal_features | Features temporelles |
| `engineer_risk_features()` | code_metrics | risk_features | Features de risque |
| `create_interaction_features()` | base_features | interaction_features | Features d'interaction |
| `normalize_features()` | raw_features | normalized[0-1] | Normalisation Min-Max |
| `handle_missing_features()` | features | complete_features | Gestion valeurs manquantes |
| `engineer_full_feature_set()` | raw_data | final_features | Pipeline complet |

---

## 🔗 MLflow Integration

### Configuration MLflow

```python
class MLFlowConfig:
    tracking_uri: str = "file:./mlruns"        # Local tracking URI
    experiment_name: str = "hyperion_ml_v3"   # Experiment name
    default_tags: dict = {
        "project": "hyperion",
        "version": "3.0.0",
        "team": "hyperion-dev",
        "environment": "development"
    }
```

### Logging Automatique

Pour chaque modèle entraîné, MLflow logge automatiquement :

```python
with mlflow.start_run(run_name=f"{model_name}_{timestamp}"):

    # 1. Log hyperparameters
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("learning_rate", 0.1)

    # 2. Log training metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("precision", 0.92)
    mlflow.log_metric("recall", 0.94)
    mlflow.log_metric("f1_score", 0.93)
    mlflow.log_metric("training_time_seconds", 45.2)

    # 3. Log validation metrics (CV)
    mlflow.log_metric("cv_mean_accuracy", 0.93)
    mlflow.log_metric("cv_std_accuracy", 0.02)

    # 4. Log feature importance (si disponible)
    if hasattr(model, 'feature_importances_'):
        for i, importance in enumerate(model.feature_importances_):
            mlflow.log_metric(f"feature_importance_{feature_names[i]}", importance)

    # 5. Log tags
    mlflow.set_tags({
        "model_name": "risk_predictor_rf",
        "model_type": "RandomForest",
        "status": "training",
        "data_version": "v1.0",
        "features_version": "3.0.0"
    })

    # 6. Log artifacts
    mlflow.log_artifact("confusion_matrix.png", "plots")
    mlflow.log_artifact("feature_importance.png", "plots")

    # 7. Log model (format natif)
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="sklearn_model",
        signature=signature,
        input_example=input_example
    )
```

### Structure MLruns

```
mlruns/
├── 0/                           # Default experiment
│   └── meta.yaml
├── 1/                           # hyperion_ml_v3 experiment
│   ├── meta.yaml
│   ├── abc123def456/           # Run ID
│   │   ├── meta.yaml
│   │   ├── metrics/
│   │   │   ├── accuracy
│   │   │   ├── f1_score
│   │   │   └── training_time_seconds
│   │   ├── params/
│   │   │   ├── n_estimators
│   │   │   └── max_depth
│   │   ├── tags/
│   │   │   ├── model_name
│   │   │   └── model_type
│   │   └── artifacts/
│   │       ├── sklearn_model/
│   │       └── plots/
│   └── def789ghi012/           # Another run
└── models/                     # Model registry
    ├── risk_predictor/
    │   ├── version-1/
    │   └── version-2/
    └── anomaly_detector/
```

### Requêtes MLflow

```python
import mlflow

# Rechercher les meilleurs runs
runs = mlflow.search_runs(
    experiment_ids=["1"],
    filter_string="metrics.f1_score > 0.9",
    order_by=["metrics.f1_score DESC"],
    max_results=5
)

# Charger modèle depuis registry
model = mlflow.sklearn.load_model(
    model_uri="models:/risk_predictor/production"
)

# Comparer runs
mlflow.compare_runs(
    run_ids=["abc123def456", "def789ghi012"],
    metric_names=["accuracy", "f1_score"]
)
```

---

## 🚀 Utilisation Pratique

### Workflow Complet ML

```python
from hyperion.modules.ml.infrastructure import FeatureStore, DataValidator, ModelRegistry
from hyperion.modules.ml.training import TrainingPipeline, FeatureEngineer

# 1. Feature Engineering
engineer = FeatureEngineer()
features = engineer.engineer_full_feature_set(raw_git_data)

# 2. Stockage dans Feature Store
store = FeatureStore()
feature_set_id = store.store_features(
    features_dict=features,
    source_file="repo/file.py",
    repository="requests",
    tags={"version": "1.0", "type": "risk"}
)

# 3. Validation des données
validator = DataValidator()
df_clean, validation_result = validator.validate_and_prepare_data(
    df=features_df,
    target_column="risque_reel",
    fix_issues=True
)

if not validation_result.is_valid:
    print("❌ Data validation failed, aborting training")
    exit(1)

# 4. Entraînement des modèles
pipeline = TrainingPipeline()
training_result = pipeline.train_risk_predictor(
    data_file="features.csv",
    target_column="risque_reel",
    test_size=0.2,
    cv_folds=5
)

# 5. Registry des modèles
registry = ModelRegistry()
version = registry.save_model(
    model=training_result['best_model']['instance'],
    name="risk_predictor",
    model_type=training_result['best_model']['name'],
    metadata={
        "accuracy": training_result['best_model']['accuracy'],
        "f1_score": training_result['best_model']['f1'],
        "training_features": training_result['feature_names'],
        "training_samples": training_result['training_samples']
    }
)

print(f"✅ Model saved as {version}")

# 6. Promotion en production
registry.promote_model(
    name="risk_predictor",
    version=version,
    status="production"
)

print(f"🚀 Model promoted to production")
```

### Prédiction en Production

```python
# Charger modèle de production
registry = ModelRegistry()
model, metadata = registry.load_model(
    name="risk_predictor",
    version="latest"  # ou version spécifique
)

# Prédire sur nouvelles données
new_features = engineer.engineer_full_feature_set(new_git_data)
predictions = model.predict(new_features)
probabilities = model.predict_proba(new_features)

print(f"Risk prediction: {predictions[0]}")
print(f"Confidence: {max(probabilities[0]):.2%}")
```

### Monitoring et Drift Detection

```python
# Détecter data drift
drift_report = validator.detect_data_drift(
    reference_df=training_features,
    current_df=production_features,
    threshold=0.1
)

if drift_report.has_drift:
    print("⚠️  Data drift detected, consider retraining models")

    # Retrain automatiquement si drift significatif
    if drift_report.drift_magnitude > 0.2:
        print("🔄 Auto-retraining triggered")
        training_result = pipeline.train_risk_predictor(
            data_file="updated_features.csv",
            target_column="risque_reel"
        )
```

### Configuration via Environment

```bash
# MLflow
export MLFLOW_TRACKING_URI=file:./mlruns
export MLFLOW_EXPERIMENT_NAME=hyperion_ml_production

# Feature Store
export FEATURE_STORE_TTL_HOURS=24
export FEATURE_STORE_CACHE_SIZE=1000

# Training
export ML_RANDOM_STATE=42
export ML_N_JOBS=-1
export ML_CV_FOLDS=5
```

---

## 📊 Métriques et Monitoring

### Métriques Trackées

```python
# Performance metrics
- accuracy: % de prédictions correctes
- precision: TP / (TP + FP) par classe
- recall: TP / (TP + FN) par classe
- f1_score: moyenne harmonique precision/recall
- roc_auc: area under ROC curve

# Training metrics
- training_time_seconds: durée d'entraînement
- cv_mean_*: moyenne cross-validation
- cv_std_*: écart-type cross-validation

# Feature metrics
- feature_importance_*: importance par feature
- feature_count: nombre de features utilisées
- feature_coverage: couverture des features

# Data metrics
- training_samples: nombre d'échantillons train
- test_samples: nombre d'échantillons test
- missing_percentage: % valeurs manquantes
- class_balance: distribution des classes
```

### Dashboards MLflow

Accès via : http://localhost:5000 (si MLflow UI lancé)

```bash
# Lancer MLflow UI
mlflow ui --host 0.0.0.0 --port 5000
```

**Dashboards disponibles** :
- **Experiments** : Comparaison des runs d'entraînement
- **Models** : Registry et versions des modèles
- **Artifacts** : Plots, confusion matrices, feature importance
- **Metrics** : Évolution des métriques dans le temps

---

Cette documentation complète couvre l'ensemble de l'infrastructure ML de Hyperion. Pour toute question ou suggestion d'amélioration, n'hésitez pas à consulter les tests dans `src/hyperion/modules/ml/tests/` qui contiennent de nombreux exemples d'usage.