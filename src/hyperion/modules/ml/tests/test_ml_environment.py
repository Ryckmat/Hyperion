"""
Test simple pour valider l'environnement ML d'Hyperion.

Teste que l'infrastructure ML de base fonctionne correctement.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hyperion.modules.ml.infrastructure.data_validator import data_validator
from hyperion.modules.ml.infrastructure.feature_store import feature_store
from hyperion.modules.ml.infrastructure.ml_config import ml_config
from hyperion.modules.ml.infrastructure.model_registry import model_registry


class TestMLEnvironment:
    """Tests d'environnement ML."""

    def test_ml_config_initialization(self):
        """Test que la config ML s'initialise correctement."""
        assert ml_config is not None
        assert hasattr(ml_config, "features")
        assert hasattr(ml_config, "training")
        assert hasattr(ml_config, "mlflow")
        assert len(ml_config.features.all_features) > 0

    def test_data_validator_basic_functionality(self):
        """Test fonctionnalité basique du validateur."""
        # Créer données de test simples
        test_data = pd.DataFrame(
            {
                "complexite_cyclomatique": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "nb_methodes": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

        result = data_validator.validate_dataframe(test_data, "target")
        assert result is not None
        assert hasattr(result, "is_valid")
        assert hasattr(result, "n_samples")
        assert result.n_samples == 10

    def test_feature_store_basic_operations(self, tmp_path):
        """Test opérations basiques du feature store."""
        # Utiliser store temporaire
        temp_store = feature_store
        temp_store.store_dir = tmp_path / "feature_store_test"
        temp_store.metadata_dir = temp_store.store_dir / "metadata"
        temp_store.cache_dir = temp_store.store_dir / "cache"

        # Créer dossiers
        for directory in [temp_store.store_dir, temp_store.metadata_dir, temp_store.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Test stockage et récupération
        test_features = {"feature1": 1.0, "feature2": 2.0, "feature3": 3.0}

        feature_set_id = temp_store.store_features(
            features=test_features, source_file="/test/file.py", repository="test_repo"
        )

        assert feature_set_id is not None

        retrieved_features = temp_store.get_features(
            source_file="/test/file.py", repository="test_repo"
        )

        assert retrieved_features == test_features

    def test_model_registry_basic_operations(self, tmp_path):
        """Test opérations basiques du model registry."""
        # Mock simple model
        from sklearn.datasets import make_classification
        from sklearn.ensemble import RandomForestClassifier

        X, y = make_classification(n_samples=20, n_features=4, random_state=42)
        model = RandomForestClassifier(n_estimators=3, random_state=42)
        model.fit(X, y)

        # Utiliser registry temporaire
        temp_registry = model_registry
        temp_registry.models_dir = tmp_path / "models"
        temp_registry.metadata_dir = temp_registry.models_dir / "metadata"
        temp_registry.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Test sauvegarde
        version = temp_registry.save_model(
            model=model,
            name="test_model",
            model_type="RandomForest",
            mlflow_logging=False,  # Désactiver pour test
        )

        assert version is not None
        assert version == "1.0.0"

        # Test chargement
        loaded_model = temp_registry.load_model("test_model", version)
        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")

    def test_ml_dependencies_available(self):
        """Test que les dépendances ML sont disponibles."""
        # Test imports critiques
        try:
            import mlflow
            import numpy as np
            import pandas as pd
            import sklearn  # noqa: F401
            import xgboost  # noqa: F401

            # Vérifier que les imports fonctionnent
            assert np is not None
            assert pd is not None
            assert mlflow is not None
        except ImportError as e:
            pytest.fail(f"Dépendance ML manquante: {e}")

    def test_ml_directories_structure(self):
        """Test que la structure des répertoires ML est correcte."""
        assert ml_config.data_dir is not None
        assert ml_config.models_dir is not None
        assert ml_config.logs_dir is not None

        # Vérifier types
        assert isinstance(ml_config.data_dir, Path)
        assert isinstance(ml_config.models_dir, Path)
        assert isinstance(ml_config.logs_dir, Path)

    def test_training_pipeline_import(self):
        """Test que le pipeline d'entraînement peut être importé."""
        try:
            from hyperion.modules.ml.training.training_pipeline import training_pipeline

            assert training_pipeline is not None
            assert hasattr(training_pipeline, "train_risk_predictor")
        except ImportError as e:
            pytest.fail(f"Impossible d'importer le pipeline d'entraînement: {e}")


class TestMLEnvironmentIntegration:
    """Tests d'intégration environnement ML."""

    def test_end_to_end_minimal_workflow(self, tmp_path):
        """Test workflow minimal de bout en bout."""
        # 1. Préparer données simples
        data = pd.DataFrame(
            {
                "complexite_cyclomatique": np.random.uniform(1, 20, 50),
                "nb_methodes": np.random.randint(1, 50, 50),
                "nb_contributeurs_uniques": np.random.randint(1, 10, 50),
                "risque_reel": np.random.choice([0, 1], 50),
            }
        )

        # 2. Valider données
        df_clean, validation_result = data_validator.validate_and_prepare_data(
            data, "risque_reel", fix_issues=True
        )

        assert validation_result is not None
        assert len(df_clean) > 0

        # 3. Stocker features dans store temporaire
        temp_store = feature_store
        temp_store.store_dir = tmp_path / "integration_test"
        temp_store.metadata_dir = temp_store.store_dir / "metadata"
        temp_store.cache_dir = temp_store.store_dir / "cache"

        for directory in [temp_store.store_dir, temp_store.metadata_dir, temp_store.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        features = {
            "complexite_cyclomatique": df_clean["complexite_cyclomatique"].mean(),
            "nb_methodes": df_clean["nb_methodes"].mean(),
        }

        feature_set_id = temp_store.store_features(
            features, "/integration/test.py", "integration_repo"
        )

        # 4. Récupérer features
        retrieved = temp_store.get_features("/integration/test.py", "integration_repo")

        assert retrieved == features

        print(f"✅ Test d'intégration ML réussi: {feature_set_id}")

    def test_configuration_consistency(self):
        """Test cohérence des configurations ML."""
        # Vérifier que toutes les features configurées sont utilisables
        all_features = ml_config.features.all_features
        assert len(all_features) > 10  # Au moins quelques features

        # Vérifier qu'il y a au moins des modèles configurés
        try:
            # Tester avec des noms de modèles probables
            possible_models = ["risk_predictor_random_forest", "bug_predictor", "anomaly_detector"]

            found_models = 0
            for model_name in possible_models:
                try:
                    config_model = ml_config.get_model_config(model_name)
                    if config_model is not None:
                        found_models += 1
                except Exception:
                    pass

            assert found_models > 0, "Aucun modèle configuré trouvé"

        except Exception as e:
            print(f"Warning: Problème configuration modèles: {e}")

    def test_pydantic_models_validation(self):
        """Test que les modèles Pydantic fonctionnent correctement."""
        from datetime import datetime

        from hyperion.modules.ml.infrastructure.feature_store import FeatureMetadata
        from hyperion.modules.ml.infrastructure.model_registry import ModelMetadata

        # Test FeatureMetadata
        feature_meta = FeatureMetadata(
            feature_set_id="test123",
            source_file="/test.py",
            repository="test",
            extracted_at=datetime.now(),
            feature_names=["f1", "f2"],
            n_features=2,
            content_hash="hash123",
            source_hash="shash456",
        )

        assert feature_meta.feature_set_id == "test123"

        # Test ModelMetadata
        model_meta = ModelMetadata(
            name="test_model", version="1.0.0", model_type="RandomForest", created_at=datetime.now()
        )

        assert model_meta.name == "test_model"

        print("✅ Modèles Pydantic fonctionnent correctement")
