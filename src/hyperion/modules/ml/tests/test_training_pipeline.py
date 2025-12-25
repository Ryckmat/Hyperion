"""
Tests pour le pipeline d'entraînement ML d'Hyperion.

Teste l'orchestration complète d'entraînement des modèles.
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from hyperion.modules.ml.training.training_pipeline import TrainingPipeline


class TestTrainingPipeline:
    """Tests pour le pipeline d'entraînement principal."""

    @pytest.fixture
    def pipeline(self, mock_ml_config):
        """Pipeline avec configuration mock."""
        pipeline = TrainingPipeline()
        pipeline.config = mock_ml_config
        return pipeline

    def test_pipeline_initialization(self, pipeline):
        """Test initialisation pipeline."""
        assert pipeline.config is not None
        assert isinstance(pipeline.trained_models, dict)
        assert isinstance(pipeline.training_results, dict)

    def test_train_risk_predictor_basic(self, pipeline, sample_training_data):
        """Test entraînement RiskPredictor de base."""
        results = pipeline.train_risk_predictor(
            training_data=sample_training_data,
            target_column="risque_reel",
            save_models=False,  # Pas de sauvegarde pour test
        )

        assert isinstance(results, dict)
        assert "training_time_seconds" in results
        assert "models_results" in results
        assert "best_model" in results
        assert "feature_names" in results

        # Vérifier modèles entraînés
        models_results = results["models_results"]
        expected_models = [
            "random_forest",
            "xgboost",
            "isolation_forest",
            "meta_learner",
        ]
        for model_name in expected_models:
            assert model_name in models_results

    def test_train_risk_predictor_with_validation_errors(self, pipeline):
        """Test avec données invalides."""
        # Données trop petites
        invalid_data = pd.DataFrame({"feature1": [1, 2], "risque_reel": [0, 1]})

        with pytest.raises(ValueError, match="Données invalides"):
            pipeline.train_risk_predictor(invalid_data, "risque_reel")

    def test_train_risk_predictor_custom_params(self, pipeline, sample_training_data):
        """Test avec paramètres personnalisés."""
        results = pipeline.train_risk_predictor(
            training_data=sample_training_data,
            target_column="risque_reel",
            test_size=0.3,  # 30% test au lieu de 20%
            save_models=False,
        )

        assert results["test_samples"] == int(len(sample_training_data) * 0.3)

    def test_train_random_forest(self, pipeline, sample_training_data):
        """Test entraînement Random Forest spécifique."""
        feature_cols = [col for col in sample_training_data.columns if col != "risque_reel"]
        X = sample_training_data[feature_cols]
        y = sample_training_data["risque_reel"]

        # Split simple pour test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        model, results = pipeline._train_random_forest(X_train, y_train, X_test, y_test)

        assert model is not None
        assert isinstance(model, RandomForestClassifier)
        assert results["model_type"] == "RandomForest"
        assert "metrics" in results
        assert "cv_score_mean" in results
        assert "feature_importance" in results

        # Vérifier métriques
        metrics = results["metrics"]
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics

    def test_train_xgboost(self, pipeline, sample_training_data):
        """Test entraînement XGBoost spécifique."""
        feature_cols = [col for col in sample_training_data.columns if col != "risque_reel"]
        X = sample_training_data[feature_cols]
        y = sample_training_data["risque_reel"]

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        model, results = pipeline._train_xgboost(X_train, y_train, X_test, y_test)

        assert model is not None
        assert results["model_type"] == "XGBoost"
        assert "metrics" in results
        assert "feature_importance" in results

    def test_train_isolation_forest(self, pipeline, sample_training_data):
        """Test entraînement Isolation Forest."""
        feature_cols = [col for col in sample_training_data.columns if col != "risque_reel"]
        X = sample_training_data[feature_cols]
        y = sample_training_data["risque_reel"]

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        model, results = pipeline._train_isolation_forest(X_train, y_train, X_test, y_test)

        assert model is not None
        assert results["model_type"] == "IsolationForest"
        assert "normal_samples_training" in results
        assert "anomaly_score_mean" in results
        assert "anomalies_detected" in results

    def test_train_meta_learner(self, pipeline, sample_training_data):
        """Test entraînement meta-learner."""
        feature_cols = [col for col in sample_training_data.columns if col != "risque_reel"]
        X = sample_training_data[feature_cols]
        y = sample_training_data["risque_reel"]

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Créer modèles de base
        rf = RandomForestClassifier(n_estimators=10, random_state=42)
        rf.fit(X_train, y_train)

        from xgboost import XGBClassifier

        xgb = XGBClassifier(n_estimators=10, random_state=42)
        xgb.fit(X_train, y_train)

        base_models = [rf, xgb]

        ensemble_model, results = pipeline._train_meta_learner(
            base_models, X_train, y_train, X_test, y_test
        )

        assert isinstance(ensemble_model, dict)
        assert "meta_learner" in ensemble_model
        assert "base_models" in ensemble_model
        assert results["model_type"] == "MetaLearner"
        assert results["base_models_count"] == 2
        assert "metrics" in results

    def test_calculate_metrics(self, pipeline):
        """Test calcul métriques."""
        # Données de test simples
        y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 1, 0, 0, 0, 1])
        y_proba = np.random.rand(len(y_true), 2)

        metrics = pipeline._calculate_metrics(y_true, y_pred, y_proba)

        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert "classification_report" in metrics

        # Vérifier valeurs valides
        for _metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                assert 0 <= value <= 1

    def test_find_best_model(self, pipeline):
        """Test recherche meilleur modèle."""
        models_results = {
            "model1": {"metrics": {"f1": 0.85, "accuracy": 0.80}},
            "model2": {"metrics": {"f1": 0.90, "accuracy": 0.85}},
            "model3": {"metrics": {"f1": 0.75, "accuracy": 0.78}},
        }

        best_model = pipeline._find_best_model(models_results)

        assert best_model["name"] == "model2"
        assert best_model["f1"] == 0.90
        assert best_model["accuracy"] == 0.85

    def test_find_best_model_empty(self, pipeline):
        """Test recherche sur modèles vides."""
        best_model = pipeline._find_best_model({})

        assert best_model["name"] is None
        assert best_model["f1"] == 0

    def test_train_bug_predictor(self, pipeline, sample_bug_prediction_data):
        """Test entraînement BugPredictor."""
        results = pipeline.train_bug_predictor(
            training_data=sample_bug_prediction_data,
            target_column="bug_dans_30j",
            save_model=False,
        )

        assert isinstance(results, dict)
        assert results["model_type"] == "BugPredictor"
        assert "metrics" in results
        assert "feature_importance" in results
        assert "temporal_split" in results
        assert results["temporal_split"] is True

    def test_validate_all_models_empty(self, mock_ml_config):
        """Test validation modèles sans modèles."""
        # Mock model_registry vide
        mock_registry = MagicMock()
        mock_registry.list_models.return_value = []

        # Pipeline avec mock registry
        pipeline = TrainingPipeline(model_registry_override=mock_registry)
        pipeline.config = mock_ml_config

        results = pipeline.validate_all_models()

        assert isinstance(results, dict)
        assert len(results) == 0

    def test_validate_all_models_with_models(self, mock_ml_config):
        """Test validation avec modèles."""
        # Mock model_registry avec modèles
        mock_models = [
            {"name": "test_model_1", "version": "1.0.0", "status": "trained"},
            {"name": "test_model_2", "version": "1.1.0", "status": "trained"},
        ]

        mock_metadata = MagicMock()
        mock_metadata.accuracy = 0.95
        mock_metadata.f1_score = 0.93
        mock_metadata.training_samples = 1000

        mock_registry = MagicMock()
        mock_registry.list_models.return_value = mock_models
        mock_registry.load_model.return_value = (MagicMock(), mock_metadata)

        # Pipeline avec mock registry
        pipeline = TrainingPipeline(model_registry_override=mock_registry)
        pipeline.config = mock_ml_config

        results = pipeline.validate_all_models()

        assert len(results) == 2
        for model_name in ["test_model_1", "test_model_2"]:
            assert model_name in results
            assert results[model_name]["loadable"] is True
            assert results[model_name]["status"] == "validé"

    def test_save_trained_models(self, mock_ml_config):
        """Test sauvegarde modèles entraînés."""
        # Mock registry
        mock_registry = MagicMock()
        mock_registry.save_model.return_value = "1.0.0"

        # Pipeline avec mock registry
        pipeline = TrainingPipeline(model_registry_override=mock_registry)
        pipeline.config = mock_ml_config

        # Mock modèles
        mock_model = MagicMock()
        models = {"test_model": mock_model}

        # Mock résultats d'entraînement
        training_results = {
            "models_results": {
                "test_model": {
                    "model_type": "RandomForest",
                    "metrics": {
                        "accuracy": 0.95,
                        "precision": 0.93,
                        "recall": 0.97,
                        "f1": 0.95,
                    },
                    "hyperparameters": {"n_estimators": 100},
                }
            },
            "feature_names": ["feature1", "feature2"],
            "training_samples": 1000,
        }

        # Appeler méthode
        pipeline._save_trained_models(models, training_results)

        # Vérifier appel save_model
        mock_registry.save_model.assert_called_once()
        call_args = mock_registry.save_model.call_args

        assert call_args[1]["model"] == mock_model
        assert call_args[1]["name"] == "risk_predictor_test_model"
        assert call_args[1]["model_type"] == "RandomForest"
        assert "metadata" in call_args[1]


class TestTrainingPipelineIntegration:
    """Tests d'intégration pipeline d'entraînement."""

    def test_complete_training_workflow(self, pipeline, sample_training_data):
        """Test workflow complet d'entraînement."""
        # Configuration pour tests rapides
        pipeline.config.training.cross_validation_folds = 3

        results = pipeline.train_risk_predictor(
            training_data=sample_training_data,
            target_column="risque_reel",
            test_size=0.2,
            save_models=False,
        )

        # Vérifier structure résultats
        assert "training_time_seconds" in results
        assert "validation_result" in results
        assert "models_results" in results
        assert "best_model" in results
        assert "ensemble_performance" in results

        # Vérifier que tous les modèles ont été entraînés
        models_results = results["models_results"]
        expected_models = [
            "random_forest",
            "xgboost",
            "isolation_forest",
            "meta_learner",
        ]

        for model_name in expected_models:
            assert model_name in models_results
            if model_name != "isolation_forest":  # Isolation Forest a structure différente
                assert "metrics" in models_results[model_name]

        # Vérifier meilleur modèle
        best_model = results["best_model"]
        assert best_model["name"] is not None
        assert 0 <= best_model["f1"] <= 1

    def test_training_with_data_issues(self, pipeline):
        """Test entraînement avec problèmes de données."""
        # Données avec problèmes
        problematic_data = pd.DataFrame(
            {
                "feature1": [1, 2, 3, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  # Doublons
                "feature2": [np.inf, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],  # Inf
                "feature3": [1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],  # NaN
                "risque_reel": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

        # Doit réussir grâce à la préparation des données
        results = pipeline.train_risk_predictor(
            training_data=problematic_data,
            target_column="risque_reel",
            save_models=False,
        )

        assert results is not None
        assert "models_results" in results

    def test_training_different_target_distributions(self, pipeline):
        """Test avec différentes distributions de target."""
        # Distribution déséquilibrée
        unbalanced_data = pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "feature3": np.random.randn(100),
                "risque_reel": np.random.choice([0, 1], 100, p=[0.9, 0.1]),  # 90% classe 0
            }
        )

        results = pipeline.train_risk_predictor(
            training_data=unbalanced_data,
            target_column="risque_reel",
            save_models=False,
        )

        assert results is not None
        # Pipeline doit gérer automatiquement le déséquilibrage

    def test_pipeline_with_minimal_features(self, pipeline):
        """Test avec features minimales."""
        minimal_data = pd.DataFrame(
            {
                "complexite_cyclomatique": np.random.uniform(1, 20, 50),
                "nb_methodes": np.random.randint(1, 50, 50),
                "risque_reel": np.random.choice([0, 1], 50),
            }
        )

        results = pipeline.train_risk_predictor(
            training_data=minimal_data, target_column="risque_reel", save_models=False
        )

        assert results is not None
        # Doit fonctionner même avec peu de features

    def test_pipeline_error_handling(self, pipeline):
        """Test gestion d'erreurs pipeline."""
        # DataFrame complètement vide
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError):
            pipeline.train_risk_predictor(empty_data, "risque_reel")

        # Target inexistante
        good_data = pd.DataFrame(
            {
                "feature1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "target_wrong": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

        with pytest.raises(ValueError):
            pipeline.train_risk_predictor(good_data, "target_inexistant")

    def test_performance_metrics_validity(self, pipeline, sample_training_data):
        """Test validité métriques de performance."""
        results = pipeline.train_risk_predictor(
            training_data=sample_training_data,
            target_column="risque_reel",
            save_models=False,
        )

        # Vérifier que toutes les métriques sont valides
        for model_name, model_results in results["models_results"].items():
            if "metrics" in model_results:
                metrics = model_results["metrics"]

                for metric_name, value in metrics.items():
                    if isinstance(value, (int, float)) and metric_name != "classification_report":
                        assert (
                            0 <= value <= 1
                        ), f"Métrique {metric_name} invalide pour {model_name}: {value}"

        # Vérifier meilleur modèle
        best_model = results["best_model"]
        if best_model["name"] is not None:
            assert 0 <= best_model["f1"] <= 1
            assert 0 <= best_model["accuracy"] <= 1
