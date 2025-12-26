# 🧠 Chapitre 07 - Infrastructure ML

**Comprendre les modèles et prédictions** - L'intelligence artificielle d'Hyperion

*⏱️ Durée estimée : 50 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous comprendrez :
- ✅ Les 5 modèles ML d'Hyperion et leurs cas d'usage
- ✅ Le Feature Store et les 35+ features engineered
- ✅ Comment interpréter et utiliser les prédictions
- ✅ MLflow et le suivi des expérimentations

---

## 🤖 **Les 5 Modèles ML d'Hyperion**

### 🎯 **1. RiskPredictor - Prédiction de Risques**

**Objectif** : Identifier les fichiers/modules avec le plus haut risque de bugs

#### 🔬 **Algorithme**
- **Ensemble** : Random Forest + XGBoost
- **Features** : 15 features de complexité + historique Git
- **Target** : Probabilité de bug dans les 30 prochains jours

#### 📊 **Utilisation**
```bash
# Via CLI
hyperion predict mon-projet/ --type risk

# Via API
curl http://localhost:8000/api/v2/repos/mon-projet/predictions/risk
```

#### 🎯 **Interprétation des Résultats**
```json
{
  "risk_predictions": [
    {
      "file": "src/core/payment.py",
      "risk_score": 0.87,  // Très haut risque
      "factors": [
        "High cyclomatic complexity (15.3)",
        "Recent frequent changes (12 commits last week)",
        "Multiple contributors (5 developers)",
        "Low test coverage (23%)"
      ],
      "recommendations": [
        "Add unit tests",
        "Refactor complex functions",
        "Code review required"
      ]
    }
  ]
}
```

**Actions recommandées par score :**
- **0.8-1.0** : Action immédiate requise
- **0.6-0.8** : Surveillance renforcée
- **0.4-0.6** : À surveiller
- **<0.4** : Risque normal

### 🔍 **2. AnomalyDetector - Détection d'Anomalies**

**Objectif** : Détecter les patterns inhabituels dans le code et les commits

#### 🔬 **Algorithme**
- **Isolation Forest** : Détection d'outliers
- **Features** : Patterns de commits, taille des changements, timing
- **Detection** : Score d'anomalie (-1 à 1)

#### 📊 **Types d'Anomalies Détectées**
```python
# Exemples d'anomalies typiques
anomaly_types = {
    "large_commit": "Commit inhabituellemen volumineux (>500 lignes)",
    "late_night_coding": "Commits fréquents tard la nuit",
    "complexity_spike": "Augmentation soudaine de complexité",
    "unusual_file_pattern": "Modification de fichiers inhabituels",
    "mass_deletion": "Suppression massive de code",
    "dependency_injection": "Nouvelle dépendance inattendue"
}
```

#### 🎯 **Exemple de Détection**
```json
{
  "anomalies_detected": [
    {
      "type": "complexity_spike",
      "confidence": 0.92,
      "description": "Le fichier auth.py a vu sa complexité passer de 4.2 à 12.8 en un commit",
      "commit": "a1b2c3d",
      "timestamp": "2024-12-25T23:45:00Z",
      "impact_assessment": "High",
      "suggested_action": "Review commit a1b2c3d for potential issues"
    }
  ]
}
```

### 🐛 **3. BugPredictor - Prédiction de Bugs**

**Objectif** : Prédire la probabilité d'apparition de bugs

#### 🔬 **Algorithme**
- **Time Series + Gradient Boosting**
- **Features** : Historique bugs, patterns temporels, qualité code
- **Horizon** : 7, 15, 30 jours

#### 📈 **Analyse Temporelle**
```python
# Patterns temporels typiques
temporal_patterns = {
    "sprint_end_spike": "Plus de bugs en fin de sprint",
    "monday_effect": "Plus de bugs le lundi (code weekend)",
    "release_correlation": "Pics de bugs post-release",
    "team_rotation": "Bugs lors de changements d'équipe"
}
```

#### 📊 **Prédictions Détaillées**
```json
{
  "bug_predictions": {
    "overall_probability_30_days": 0.34,
    "high_risk_areas": [
      {
        "module": "authentication",
        "probability": 0.67,
        "historical_bug_rate": 0.23,
        "trend": "increasing",
        "contributing_factors": [
          "Recent major refactoring",
          "New team member contributions",
          "Complex business logic"
        ]
      }
    ],
    "temporal_forecast": {
      "week_1": 0.12,
      "week_2": 0.18,
      "week_3": 0.25,
      "week_4": 0.34
    }
  }
}
```

### 📈 **4. ImpactAnalyzer - Analyse d'Impact**

**Objectif** : Évaluer l'impact potentiel d'un changement dans la codebase

#### 🔬 **Algorithme**
- **Graph Neural Network** : Analyse du graphe de dépendances
- **Features** : Couplage, centralité, usage
- **Output** : Score d'impact 0-10

#### 🔗 **Types d'Impact Analysés**
```python
impact_dimensions = {
    "functional": "Impact sur les fonctionnalités",
    "performance": "Impact sur les performances",
    "security": "Impact sur la sécurité",
    "maintainability": "Impact sur la maintenabilité",
    "architectural": "Impact sur l'architecture"
}
```

#### 📊 **Exemple d'Analyse d'Impact**
```json
{
  "impact_analysis": {
    "file_changed": "src/core/database.py",
    "overall_impact_score": 8.3,
    "affected_components": [
      {
        "component": "user_service",
        "impact_score": 9.1,
        "impact_type": "functional",
        "dependency_path": ["database", "user_model", "user_service"],
        "estimated_test_effort": "high"
      },
      {
        "component": "payment_service",
        "impact_score": 7.2,
        "impact_type": "functional"
      }
    ],
    "recommendations": [
      "Run integration tests for user_service",
      "Verify payment transaction flows",
      "Update API documentation if schema changed"
    ]
  }
}
```

### 🧠 **5. Meta-learner - Ensemble Intelligent**

**Objectif** : Combiner tous les modèles pour des prédictions plus robustes

#### 🔬 **Algorithme**
- **Voting Ensemble** : Combine les 4 modèles précédents
- **Weighted Average** : Pondération adaptative selon le contexte
- **Confidence Score** : Niveau de confiance de la prédiction

#### 🎯 **Scores Combinés**
```json
{
  "meta_predictions": {
    "overall_health_score": 7.2,
    "confidence": 0.89,
    "contributing_models": {
      "risk_predictor": {"score": 6.8, "weight": 0.3},
      "anomaly_detector": {"score": 8.1, "weight": 0.2},
      "bug_predictor": {"score": 6.9, "weight": 0.3},
      "impact_analyzer": {"score": 7.8, "weight": 0.2}
    },
    "consolidated_recommendations": [
      "Focus testing on payment module (high risk + impact)",
      "Monitor recent auth changes (anomaly detected)",
      "Prepare for potential bugs in sprint +2"
    ]
  }
}
```

---

## 🏗️ **Feature Store - 35+ Features Engineered**

### 📊 **Catégories de Features**

#### 🔧 **Code Quality Features (12)**
```python
code_quality_features = {
    "cyclomatic_complexity": "Complexité cyclomatique moyenne",
    "cognitive_complexity": "Complexité cognitive",
    "lines_of_code": "Nombre de lignes de code",
    "code_duplication_ratio": "Ratio de duplication",
    "technical_debt_ratio": "Ratio de dette technique",
    "maintainability_index": "Index de maintenabilité",
    "test_coverage_ratio": "Couverture de tests",
    "comment_density": "Densité de commentaires",
    "function_length_avg": "Taille moyenne des fonctions",
    "class_coupling": "Couplage entre classes",
    "inheritance_depth": "Profondeur d'héritage",
    "code_smells_count": "Nombre de code smells"
}
```

#### 👥 **Team Dynamics Features (8)**
```python
team_features = {
    "commit_frequency": "Fréquence de commits",
    "contributors_count": "Nombre de contributeurs",
    "code_ownership_concentration": "Concentration de la propriété du code",
    "review_participation_rate": "Taux de participation aux reviews",
    "knowledge_distribution": "Distribution de la connaissance",
    "collaboration_score": "Score de collaboration",
    "contributor_experience": "Expérience moyenne des contributeurs",
    "team_velocity": "Vélocité de l'équipe"
}
```

#### 💼 **Business Impact Features (10)**
```python
business_features = {
    "feature_usage_frequency": "Fréquence d'usage des features",
    "user_impact_score": "Score d'impact utilisateur",
    "business_criticality": "Criticité business",
    "revenue_impact": "Impact sur le chiffre d'affaires",
    "security_sensitivity": "Sensibilité sécurité",
    "compliance_requirements": "Exigences de conformité",
    "performance_criticality": "Criticité performance",
    "data_sensitivity": "Sensibilité des données",
    "external_dependencies": "Dépendances externes",
    "scalability_requirements": "Exigences de scalabilité"
}
```

#### ⏰ **Temporal Features (5+)**
```python
temporal_features = {
    "time_since_last_change": "Temps depuis dernier changement",
    "change_frequency_trend": "Tendance de fréquence des changements",
    "seasonal_patterns": "Patterns saisonniers",
    "sprint_phase": "Phase du sprint",
    "release_proximity": "Proximité de la release",
    "historical_bug_density": "Densité historique de bugs",
    "code_age": "Âge du code"
}
```

### 🔄 **Feature Engineering Pipeline**

```python
# Exemple de feature engineering pour RiskPredictor
class RiskFeatureEngineer:
    def __init__(self, repo_data):
        self.repo = repo_data

    def extract_features(self, file_path):
        features = {}

        # Code quality features
        features["complexity"] = self.calculate_complexity(file_path)
        features["test_coverage"] = self.get_test_coverage(file_path)
        features["code_smells"] = self.detect_code_smells(file_path)

        # Historical features
        features["bug_history"] = self.get_historical_bugs(file_path)
        features["change_frequency"] = self.get_change_frequency(file_path, days=30)
        features["contributor_count"] = self.get_contributor_count(file_path, days=90)

        # Contextual features
        features["module_importance"] = self.calculate_module_importance(file_path)
        features["dependency_count"] = self.count_dependencies(file_path)
        features["usage_frequency"] = self.estimate_usage_frequency(file_path)

        return features

    def calculate_complexity(self, file_path):
        """Calculer la complexité cyclomatique"""
        # Implémentation avec AST parsing
        pass

    def get_historical_bugs(self, file_path):
        """Extraire l'historique des bugs"""
        # Analyse des commits avec mots-clés "fix", "bug", "issue"
        pass
```

---

## 📊 **MLflow Integration - Tracking et Registry**

### 🔬 **Suivi des Expérimentations**

#### 📈 **Interface MLflow**
```bash
# Accéder à MLflow UI
# http://localhost:5000

# Ou démarrer manuellement
mlflow ui --host 0.0.0.0 --port 5000
```

#### 📊 **Métriques Trackées**
```python
# Exemple d'expérimentation trackée
experiment_metrics = {
    # Performance du modèle
    "accuracy": 0.87,
    "precision": 0.84,
    "recall": 0.91,
    "f1_score": 0.87,
    "auc_roc": 0.93,

    # Validation croisée
    "cv_mean_accuracy": 0.85,
    "cv_std_accuracy": 0.03,

    # Métriques business
    "false_positive_cost": 120.0,  # Coût d'un faux positif
    "false_negative_cost": 800.0,  # Coût d'un faux négatif
    "expected_value": 15600.0,     # Valeur attendue

    # Performance technique
    "training_time_seconds": 45.2,
    "prediction_time_ms": 12.3,
    "model_size_mb": 2.4
}
```

### 🗃️ **Model Registry**

#### 📦 **Versioning des Modèles**
```python
# Enregistrer un nouveau modèle
mlflow.sklearn.log_model(
    model=risk_predictor,
    artifact_path="risk_predictor",
    registered_model_name="RiskPredictor_v2.7",
    signature=model_signature,
    input_example=sample_features
)

# Promouvoir en production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="RiskPredictor_v2.7",
    version=3,
    stage="Production"
)
```

#### 🎯 **Comparaison de Modèles**
```python
# Script de comparaison automatique
def compare_models():
    client = mlflow.tracking.MlflowClient()

    # Récupérer les runs récents
    experiment = mlflow.get_experiment_by_name("RiskPredictor")
    runs = client.search_runs(experiment.experiment_id)

    # Comparer les métriques
    comparison = []
    for run in runs[:5]:  # Top 5 runs
        metrics = run.data.metrics
        comparison.append({
            "run_id": run.info.run_id,
            "accuracy": metrics.get("accuracy", 0),
            "f1_score": metrics.get("f1_score", 0),
            "training_time": metrics.get("training_time_seconds", 0),
            "model_size": metrics.get("model_size_mb", 0)
        })

    # Trouver le meilleur compromis
    best_model = max(comparison, key=lambda x: x["f1_score"] - x["training_time"]/100)

    return best_model
```

---

## 🎯 **Utilisation Pratique des Prédictions**

### 📋 **Workflows ML**

#### 🚀 **Pipeline de Prédiction Continue**
```bash
#!/bin/bash
# continuous_ml_pipeline.sh

# 1. Extraction des nouvelles features
hyperion ingest mon-projet/ --extract-features --update

# 2. Prédictions de risques
RISKS=$(hyperion predict mon-projet/ --type risk --format json)

# 3. Alertes si risques élevés
HIGH_RISK_COUNT=$(echo $RISKS | jq '[.risk_predictions[] | select(.risk_score > 0.7)] | length')

if [ "$HIGH_RISK_COUNT" -gt 0 ]; then
    echo "⚠️ $HIGH_RISK_COUNT high-risk files detected!"
    # Envoyer notification Slack/Teams
    curl -X POST $SLACK_WEBHOOK \
        -d "{\"text\": \"🚨 High risk files detected in $PROJECT_NAME\"}"
fi

# 4. Mise à jour dashboard
hyperion generate mon-projet/ --type ml-report --output dashboard/
```

#### 🔍 **Code Review Assisté**
```python
# pre-commit hook avec prédictions ML
def ml_assisted_code_review():
    # Récupérer les fichiers modifiés
    changed_files = get_changed_files()

    for file_path in changed_files:
        # Prédire le risque du fichier modifié
        risk_score = hyperion_predict_risk(file_path)

        # Analyser l'impact du changement
        impact = hyperion_analyze_impact(file_path)

        # Générer recommendations
        if risk_score > 0.7:
            print(f"⚠️ HIGH RISK: {file_path} (score: {risk_score:.2f})")
            print("Recommendations:")
            print("- Mandatory code review required")
            print("- Add/update unit tests")
            print("- Consider pair programming")

        if impact["overall_impact_score"] > 8.0:
            print(f"🎯 HIGH IMPACT: {file_path}")
            print(f"Affected components: {len(impact['affected_components'])}")
            print("- Run integration tests")
            print("- Update documentation")
```

### 📊 **Dashboard ML Personnalisé**

```python
import streamlit as st
import plotly.express as px

def create_ml_dashboard():
    st.title("🤖 Hyperion ML Dashboard")

    # Sélection repository
    repo = st.selectbox("Repository", ["mon-projet", "autre-projet"])

    # Récupération données
    risk_data = get_risk_predictions(repo)
    anomaly_data = get_anomaly_detection(repo)

    # Graphiques
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Risk Distribution")
        fig_risk = px.histogram(
            risk_data,
            x="risk_score",
            bins=20,
            title="Distribution des Scores de Risque"
        )
        st.plotly_chart(fig_risk)

    with col2:
        st.subheader("🔍 Anomalies Timeline")
        fig_anomaly = px.line(
            anomaly_data,
            x="date",
            y="anomaly_count",
            title="Anomalies Détectées dans le Temps"
        )
        st.plotly_chart(fig_anomaly)

    # Top des fichiers à risque
    st.subheader("⚠️ Top High-Risk Files")
    high_risk_files = risk_data[risk_data["risk_score"] > 0.7]
    st.dataframe(high_risk_files[["file", "risk_score", "recommendations"]])

    # Actions recommandées
    st.subheader("🎯 Recommended Actions")
    for _, file_data in high_risk_files.iterrows():
        with st.expander(f"🔴 {file_data['file']} (Score: {file_data['risk_score']:.2f})"):
            for recommendation in file_data["recommendations"]:
                st.write(f"- {recommendation}")

# Lancer le dashboard
streamlit run ml_dashboard.py
```

---

## ⚡ **Performance et Optimisation ML**

### 🚀 **Optimisation des Modèles**

#### 📊 **Monitoring Performance**
```python
# Métriques de performance en temps réel
performance_metrics = {
    "prediction_latency_ms": 15.2,  # Latence de prédiction
    "feature_extraction_ms": 8.7,   # Extraction de features
    "model_loading_ms": 120.0,      # Chargement du modèle
    "cache_hit_rate": 0.78,         # Taux de hit du cache
    "memory_usage_mb": 245.0,       # Utilisation mémoire
    "cpu_usage_percent": 23.5       # Utilisation CPU
}
```

#### 🎯 **Cache Intelligent**
```python
class MLPredictionCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl = ttl_seconds

    def get_prediction(self, repo_name, model_type, features_hash):
        cache_key = f"{repo_name}:{model_type}:{features_hash}"

        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]

            # Vérifier TTL
            if time.time() - timestamp < self.ttl:
                return cached_result, True  # Cache hit

        return None, False  # Cache miss

    def store_prediction(self, repo_name, model_type, features_hash, prediction):
        cache_key = f"{repo_name}:{model_type}:{features_hash}"
        self.cache[cache_key] = (prediction, time.time())
```

---

## 🎉 **Maîtrise de l'Infrastructure ML !**

### ✅ **Ce que Vous Comprenez Maintenant**

- 🤖 **5 Modèles ML** : RiskPredictor, AnomalyDetector, BugPredictor, ImpactAnalyzer, Meta-learner
- 🏗️ **Feature Store** : 35+ features dans 4 catégories
- 📊 **MLflow** : Tracking, expérimentation, model registry
- 🎯 **Applications** : Code review, monitoring, dashboard
- ⚡ **Performance** : Cache, optimisation, monitoring temps réel

### 🚀 **Applications Pratiques**

- Quality gates automatiques
- Code review assisté par IA
- Prédiction de charge de travail
- Optimisation des sprints
- Monitoring proactif

### 📚 **Prochaines Étapes**

👉 **Continuez avec** : [Chapitre 08 - Workflows](08-workflows.md)

Au prochain chapitre, vous apprendrez :
- Automatisation de workflows complets
- Intégration CI/CD avancée
- Monitoring continu avec les prédictions ML
- Scripts d'automation et orchestration

---

*Parfait ! Vous comprenez maintenant l'intelligence artificielle d'Hyperion. Rendez-vous au [Chapitre 08](08-workflows.md) !* 🧠

---

*Cours Hyperion v2.7.0 - Chapitre 07 - Décembre 2024*