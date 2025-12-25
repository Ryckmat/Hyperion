"""
Tests pour la configuration ML d'Hyperion.

Teste la classe MLConfig et la gestion des paramètres ML.
"""

import pytest
from pydantic import ValidationError

from hyperion.modules.ml.infrastructure.ml_config import MLConfig, ModelConfig


class TestMLConfig:
    """Tests pour la configuration ML principale."""

    def test_default_config_creation(self):
        """Test création config par défaut."""
        config = MLConfig()

        assert "ml" in str(config.data_dir)
        assert "model" in str(config.models_dir)  # Accepte "modeles" ou "models"
        assert "logs" in str(config.logs_dir)
        assert config.training.random_state == 42
        assert config.training.cross_validation_folds == 5

    def test_features_configuration(self):
        """Test configuration des features."""
        config = MLConfig()

        # Vérifier catégories de features
        assert len(config.features.code_quality_features) > 0
        assert len(config.features.team_dynamics_features) > 0
        assert len(config.features.business_impact_features) > 0
        assert len(config.features.historical_features) > 0
        assert len(config.features.temporal_features) > 0

        # Vérifier features totales
        all_features = config.features.all_features
        assert len(all_features) >= 35  # Au moins 35 features
        assert "complexite_cyclomatique" in all_features
        assert "nb_contributeurs_uniques" in all_features
        assert "estimation_trafic_affecte" in all_features

    def test_model_configurations(self):
        """Test configurations des modèles."""
        config = MLConfig()

        # Risk Predictor RF
        rf_config = config.get_model_config("risk_predictor_random_forest")
        assert rf_config.name == "risk_predictor_random_forest"
        assert rf_config.hyperparameters["n_estimators"] == 100
        assert rf_config.hyperparameters["random_state"] == 42

        # Risk Predictor XGB
        xgb_config = config.get_model_config("risk_predictor_xgboost")
        assert xgb_config.name == "risk_predictor_xgboost"
        assert xgb_config.hyperparameters["n_estimators"] == 100
        assert xgb_config.hyperparameters["random_state"] == 42

        # Bug Predictor
        bug_config = config.get_model_config("bug_predictor")
        assert bug_config.name == "bug_predictor"
        assert "learning_rate" in bug_config.hyperparameters

        # Anomaly Detector
        anomaly_config = config.get_model_config("anomaly_detector")
        assert anomaly_config.name == "anomaly_detector"
        assert anomaly_config.hyperparameters["contamination"] == 0.1

    def test_invalid_model_config(self):
        """Test récupération configuration modèle inexistant."""
        config = MLConfig()

        with pytest.raises(ValueError, match="non configuré"):
            config.get_model_config("modele_inexistant")

    def test_mlflow_configuration(self):
        """Test configuration MLflow."""
        config = MLConfig()

        assert "file:" in config.mlflow.tracking_uri
        assert config.mlflow.experiment_name == "hyperion_ml_v3"
        assert "version" in config.mlflow.default_tags
        assert config.mlflow.default_tags["version"] == "3.0.0"

    def test_custom_paths(self, temp_ml_directory):
        """Test configuration avec chemins personnalisés."""
        config = MLConfig()
        config.data_dir = temp_ml_directory / "custom_data"
        config.models_dir = temp_ml_directory / "custom_models"

        assert config.data_dir == temp_ml_directory / "custom_data"
        assert config.models_dir == temp_ml_directory / "custom_models"


class TestModelConfig:
    """Tests pour la configuration des modèles individuels."""

    def test_valid_model_config(self):
        """Test création configuration modèle valide."""
        config = ModelConfig(
            name="test_model",
            type="RandomForest",
            hyperparameters={"n_estimators": 50, "max_depth": 10, "random_state": 42},
            description="Modèle de test",
        )

        assert config.name == "test_model"
        assert config.hyperparameters["n_estimators"] == 50
        assert config.description == "Modèle de test"

    def test_model_config_validation(self):
        """Test validation configuration modèle."""
        # Name et type requis
        with pytest.raises(ValidationError):
            ModelConfig(hyperparameters={})

        # Hyperparamètres requis
        with pytest.raises(ValidationError):
            ModelConfig(name="test", type="XGBoost")

    def test_model_config_defaults(self):
        """Test valeurs par défaut configuration modèle."""
        config = ModelConfig(
            name="test_model", type="XGBoost", hyperparameters={"param1": "value1"}
        )

        assert config.description is None
        assert isinstance(config.hyperparameters, dict)

    def test_hyperparameters_types(self):
        """Test types des hyperparamètres."""
        config = ModelConfig(
            name="test_model",
            type="RandomForest",
            hyperparameters={
                "n_estimators": 100,  # int
                "learning_rate": 0.01,  # float
                "random_state": 42,  # int
                "bootstrap": True,  # bool
                "criterion": "gini",  # str
            },
        )

        assert isinstance(config.hyperparameters["n_estimators"], int)
        assert isinstance(config.hyperparameters["learning_rate"], float)
        assert isinstance(config.hyperparameters["bootstrap"], bool)
        assert isinstance(config.hyperparameters["criterion"], str)


class TestMLConfigIntegration:
    """Tests d'intégration de la configuration ML."""

    def test_config_paths_creation(self, mock_ml_config):
        """Test création automatique des répertoires."""
        config = mock_ml_config

        # Les répertoires doivent exister
        assert config.data_dir.exists()
        assert config.models_dir.exists()
        assert config.logs_dir.exists()

    def test_features_completeness(self):
        """Test complétude des features définies."""
        config = MLConfig()

        # Vérifier que toutes les catégories ont des features
        categories = [
            config.features.code_quality_features,
            config.features.team_dynamics_features,
            config.features.business_impact_features,
            config.features.historical_features,
            config.features.temporal_features,
        ]

        for category in categories:
            assert len(category) > 0, "Chaque catégorie doit avoir au moins une feature"

        # Vérifier qu'il n'y a pas de doublons
        all_features = config.features.all_features
        assert len(all_features) == len(
            set(all_features)
        ), "Pas de doublons dans les features"

    def test_model_configs_completeness(self):
        """Test complétude des configurations modèles."""
        config = MLConfig()

        required_models = [
            "risk_predictor_random_forest",
            "risk_predictor_xgboost",
            "bug_predictor",
            "anomaly_detector",
        ]

        for model_name in required_models:
            model_config = config.get_model_config(model_name)
            assert model_config.name == model_name
            assert len(model_config.hyperparameters) > 0
            assert (
                "random_state" in model_config.hyperparameters
                or "random_seed" in model_config.hyperparameters
            )

    def test_config_serialization(self):
        """Test sérialisation de la configuration."""
        config = MLConfig()

        # Test sérialisation basique
        assert hasattr(config, "training")
        assert hasattr(config, "features")
        assert hasattr(config, "mlflow")

        # Vérifier structure
        assert config.training.random_state == 42
        assert len(config.features.all_features) > 0
        assert config.mlflow.experiment_name == "hyperion_ml_v3"
