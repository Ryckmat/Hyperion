"""
Configuration ML centralisée pour Hyperion.

Gère toute la configuration des modèles ML, features, et paramètres d'entraînement.
Utilise des patterns professionnels avec validation Pydantic.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration d'un modèle ML spécifique."""

    name: str = Field(..., description="Nom du modèle")
    type: str = Field(..., description="Type: RandomForest, XGBoost, IsolationForest, etc.")
    version: str = Field(default="1.0.0", description="Version du modèle")
    path: str | None = Field(default=None, description="Chemin du modèle sauvegardé")
    hyperparameters: dict[str, Any] = Field(..., description="Hyperparamètres")
    description: str | None = Field(default=None, description="Description du modèle")

    @field_validator("type")
    @classmethod
    def validate_model_type(cls, v):
        allowed_types = [
            "RandomForest",
            "XGBoost",
            "LightGBM",
            "IsolationForest",
            "LogisticRegression",
            "SVM",
            "NeuralNetwork",
        ]
        if v not in allowed_types:
            raise ValueError(f"Type modèle doit être dans {allowed_types}")
        return v


class FeatureConfig(BaseModel):
    """Configuration des features ML."""

    # Features qualité code (12)
    code_quality_features: list[str] = Field(
        default=[
            "complexite_cyclomatique",
            "complexite_cognitive",
            "complexite_npath",
            "lignes_code",
            "densite_commentaires",
            "delta_couverture_tests",
            "nb_methodes",
            "nb_classes",
            "profondeur_heritage",
            "couplage_entrant",
            "cohesion_classe",
            "indice_maintenabilite",
        ]
    )

    # Features team dynamics (8)
    team_dynamics_features: list[str] = Field(
        default=[
            "frequence_commits",
            "experience_auteur",
            "nb_contributeurs_uniques",
            "experience_moyenne_reviewers",
            "vitesse_approbation",
            "nb_discussions_pr",
            "distribution_connaissance",
            "facteur_bus",
        ]
    )

    # Features business impact (4)
    business_impact_features: list[str] = Field(
        default=[
            "estimation_trafic_affecte",
            "score_impact_revenus",
            "niveau_criticite_module",
            "difficulte_rollback",
        ]
    )

    # Features historiques (6)
    historical_features: list[str] = Field(
        default=[
            "age_fichier_jours",
            "nb_bugs_historiques",
            "frequence_rollbacks",
            "nb_hotfixes",
            "volatilite_fichier",
            "profondeur_dependances",
        ]
    )

    # Features temporelles (5)
    temporal_features: list[str] = Field(
        default=[
            "nb_dependances_circulaires",
            "nb_deps_externes",
            "risque_breaking_changes",
            "nb_conflits_versions",
            "fan_in_fan_out",
        ]
    )

    @property
    def all_features(self) -> list[str]:
        """Retourne toutes les features combinées."""
        return (
            self.code_quality_features
            + self.team_dynamics_features
            + self.business_impact_features
            + self.historical_features
            + self.temporal_features
        )


class TrainingConfig(BaseModel):
    """Configuration d'entraînement ML."""

    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Taille test set")
    validation_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Taille validation set")
    cross_validation_folds: int = Field(default=5, ge=3, le=10, description="Nombre folds CV")
    random_state: int = Field(default=42, description="Seed aléatoire")

    # Critères d'arrêt
    early_stopping: bool = Field(default=True, description="Early stopping activé")
    patience: int = Field(default=10, description="Patience early stopping")
    min_improvement: float = Field(default=0.001, description="Amélioration minimale")

    # Métriques
    primary_metric: str = Field(default="accuracy", description="Métrique principale")
    metrics: list[str] = Field(
        default=["accuracy", "precision", "recall", "f1"],
        description="Métriques à calculer",
    )


class MLFlowConfig(BaseModel):
    """Configuration MLFlow pour tracking."""

    tracking_uri: str = Field(default="file:./mlruns", description="URI tracking MLFlow")
    experiment_name: str = Field(default="hyperion_ml_v3", description="Nom expérience")
    artifact_location: str | None = Field(default=None, description="Localisation artifacts")

    # Tags par défaut
    default_tags: dict[str, str] = Field(
        default={"project": "hyperion", "version": "3.0.0", "team": "hyperion-dev"}
    )


class MLConfig:
    """Configuration ML centralisée pour Hyperion."""

    def __init__(self, config_path: str | None = None):
        """
        Initialise la configuration ML.

        Args:
            config_path: Chemin vers fichier config custom (optionnel)
        """
        self.project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        self.models_dir = self.project_root / "modeles"
        self.data_dir = self.project_root / "data" / "ml"
        self.logs_dir = self.project_root / "logs" / "ml"

        # Créer dossiers si nécessaire
        for directory in [self.models_dir, self.data_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Configuration par défaut
        self.features = FeatureConfig()
        self.training = TrainingConfig()
        self.mlflow = MLFlowConfig()

        # Modèles configurés
        self._setup_default_models()

        # Charger config custom si fournie
        if config_path:
            self._load_custom_config(config_path)

    def _setup_default_models(self):
        """Configure les modèles par défaut."""
        self.models = {
            "risk_predictor_random_forest": ModelConfig(
                name="risk_predictor_random_forest",
                type="RandomForest",
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2,
                    "class_weight": "balanced",
                    "random_state": 42,
                },
            ),
            "risk_predictor_xgboost": ModelConfig(
                name="risk_predictor_xgboost",
                type="XGBoost",
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 8,
                    "learning_rate": 0.1,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "random_state": 42,
                },
            ),
            "anomaly_detector": ModelConfig(
                name="anomaly_detector",
                type="IsolationForest",
                hyperparameters={
                    "contamination": 0.1,
                    "max_samples": "auto",  # min(256, n_samples)
                    "random_state": 42,
                    "n_jobs": -1,
                },
            ),
            "bug_predictor": ModelConfig(
                name="bug_predictor",
                type="XGBoost",
                hyperparameters={
                    "n_estimators": 200,
                    "max_depth": 8,
                    "learning_rate": 0.1,
                    "subsample": 0.8,
                    "random_state": 42,
                },
            ),
        }

    def _load_custom_config(self, config_path: str):
        """Charge configuration custom depuis fichier YAML."""
        import yaml

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Mettre à jour configurations
            if "features" in config_data:
                self.features = FeatureConfig(**config_data["features"])
            if "training" in config_data:
                self.training = TrainingConfig(**config_data["training"])
            if "mlflow" in config_data:
                self.mlflow = MLFlowConfig(**config_data["mlflow"])

        except Exception as e:
            print(f"⚠️ Erreur chargement config custom: {e}")
            print("📋 Utilisation configuration par défaut")

    def get_model_path(self, model_key: str) -> Path:
        """Retourne le chemin d'un modèle."""
        if model_key not in self.models:
            raise ValueError(f"Modèle {model_key} non configuré")

        model_name = self.models[model_key].name
        return self.models_dir / f"{model_name}.pkl"

    def get_model_config(self, model_key: str) -> ModelConfig:
        """Retourne la configuration d'un modèle."""
        if model_key not in self.models:
            raise ValueError(f"Modèle {model_key} non configuré")

        return self.models[model_key]

    def export_config(self, output_path: str):
        """Exporte la configuration vers fichier YAML."""
        import yaml

        config_dict = {
            "features": self.features.model_dump(),
            "training": self.training.model_dump(),
            "mlflow": self.mlflow.model_dump(),
            "models": {k: v.model_dump() for k, v in self.models.items()},
        }

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=True,
            )

        print(f"✅ Configuration exportée: {output_path}")

    @property
    def total_features_count(self) -> int:
        """Retourne le nombre total de features."""
        return len(self.features.all_features)

    def validate_environment(self) -> dict[str, Any]:
        """Valide l'environnement ML."""
        validation_results = {
            "directories_exist": all(
                d.exists() for d in [self.models_dir, self.data_dir, self.logs_dir]
            ),
            "features_count": self.total_features_count,
            "models_configured": len(self.models),
            "mlflow_tracking_uri": self.mlflow.tracking_uri,
        }

        # Vérifier dépendances Python
        try:
            import lightgbm  # noqa: F401
            import mlflow  # noqa: F401
            import shap  # noqa: F401
            import sklearn
            import xgboost

            validation_results["dependencies_ok"] = True
            validation_results["sklearn_version"] = sklearn.__version__
            validation_results["xgboost_version"] = xgboost.__version__
        except ImportError as e:
            validation_results["dependencies_ok"] = False
            validation_results["missing_dependency"] = str(e)

        return validation_results


# Instance globale de configuration
ml_config = MLConfig()
