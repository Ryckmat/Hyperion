"""
Tests pour le Model Registry d'Hyperion.

Teste le versioning, sauvegarde et gestion des modèles ML.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from hyperion.modules.ml.infrastructure.model_registry import ModelMetadata


class TestModelMetadata:
    """Tests pour les métadonnées des modèles."""

    def test_model_metadata_creation(self):
        """Test création métadonnées modèle."""
        metadata = ModelMetadata(
            name="test_model", version="1.0.0", model_type="RandomForest", created_at=datetime.now()
        )

        assert metadata.name == "test_model"
        assert metadata.version == "1.0.0"
        assert metadata.model_type == "RandomForest"
        assert metadata.created_by == "hyperion-ml-system"
        assert metadata.status == "trained"

    def test_model_metadata_with_metrics(self):
        """Test métadonnées avec métriques."""
        metadata = ModelMetadata(
            name="test_model",
            version="1.0.0",
            model_type="XGBoost",
            created_at=datetime.now(),
            accuracy=0.95,
            precision=0.93,
            recall=0.97,
            f1_score=0.95,
        )

        assert metadata.accuracy == 0.95
        assert metadata.precision == 0.93
        assert metadata.recall == 0.97
        assert metadata.f1_score == 0.95

    def test_model_metadata_with_training_info(self):
        """Test métadonnées avec infos d'entraînement."""
        metadata = ModelMetadata(
            name="test_model",
            version="1.0.0",
            model_type="RandomForest",
            created_at=datetime.now(),
            training_features=["feature1", "feature2", "feature3"],
            training_samples=1000,
            hyperparameters={"n_estimators": 100, "max_depth": 10},
        )

        assert len(metadata.training_features) == 3
        assert metadata.training_samples == 1000
        assert metadata.hyperparameters["n_estimators"] == 100

    def test_model_metadata_serialization(self):
        """Test sérialisation métadonnées."""
        metadata = ModelMetadata(
            name="test_model", version="1.0.0", model_type="RandomForest", created_at=datetime.now()
        )

        # Test conversion dict
        metadata_dict = metadata.dict()
        assert "name" in metadata_dict
        assert "version" in metadata_dict
        assert "created_at" in metadata_dict

        # Test JSON serialization
        json_str = metadata.json()
        assert isinstance(json_str, str)


class TestModelRegistry:
    """Tests pour le Model Registry principal."""

    def test_registry_initialization(self, mock_model_registry):
        """Test initialisation du registry."""
        registry = mock_model_registry

        assert registry.models_dir.exists()
        assert registry.metadata_dir.exists()

    def test_save_model_basic(self, mock_model_registry, sample_sklearn_model):
        """Test sauvegarde modèle de base."""
        registry = mock_model_registry

        version = registry.save_model(
            model=sample_sklearn_model, name="test_rf", model_type="RandomForest"
        )

        assert version == "1.0.0"  # Première version

        # Vérifier fichiers créés
        model_file = registry.models_dir / f"test_rf_v{version}.pkl"
        metadata_file = registry.metadata_dir / f"test_rf_v{version}_metadata.json"

        assert model_file.exists()
        assert metadata_file.exists()

    def test_save_model_with_metadata(self, mock_model_registry, sample_sklearn_model):
        """Test sauvegarde avec métadonnées complètes."""
        registry = mock_model_registry

        metadata = {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.97,
            "f1_score": 0.95,
            "training_features": ["feature1", "feature2"],
            "training_samples": 1000,
            "hyperparameters": {"n_estimators": 100, "max_depth": 10},
            "tags": {"experiment": "test", "branch": "main"},
        }

        version = registry.save_model(
            model=sample_sklearn_model,
            name="test_rf_full",
            model_type="RandomForest",
            metadata=metadata,
        )

        # Charger et vérifier métadonnées
        model_info = registry.get_model_info("test_rf_full", version)
        assert model_info["accuracy"] == 0.95
        assert model_info["training_samples"] == 1000
        assert model_info["tags"]["experiment"] == "test"

    def test_save_model_explicit_version(self, mock_model_registry, sample_sklearn_model):
        """Test sauvegarde avec version explicite."""
        registry = mock_model_registry

        version = registry.save_model(
            model=sample_sklearn_model,
            name="test_rf_explicit",
            model_type="RandomForest",
            version="2.5.0",
        )

        assert version == "2.5.0"

    def test_load_model_basic(self, mock_model_registry, sample_sklearn_model):
        """Test chargement modèle de base."""
        registry = mock_model_registry

        # Sauvegarder d'abord
        version = registry.save_model(sample_sklearn_model, "test_load", "RandomForest")

        # Charger
        loaded_model = registry.load_model("test_load", version)

        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")

    def test_load_model_latest(self, mock_model_registry, sample_sklearn_model):
        """Test chargement dernière version."""
        registry = mock_model_registry

        # Sauvegarder plusieurs versions
        registry.save_model(sample_sklearn_model, "test_latest", "RandomForest", version="1.0.0")
        registry.save_model(sample_sklearn_model, "test_latest", "RandomForest", version="1.1.0")
        registry.save_model(sample_sklearn_model, "test_latest", "RandomForest", version="2.0.0")

        # Charger dernière version (sans spécifier)
        loaded_model = registry.load_model("test_latest")
        assert loaded_model is not None

    def test_load_model_with_metadata(self, mock_model_registry, sample_sklearn_model):
        """Test chargement avec métadonnées."""
        registry = mock_model_registry

        # Sauvegarder avec métadonnées
        metadata = {"accuracy": 0.95, "description": "Test model"}
        version = registry.save_model(
            sample_sklearn_model, "test_with_meta", "RandomForest", metadata=metadata
        )

        # Charger avec métadonnées
        model, meta = registry.load_model("test_with_meta", version, return_metadata=True)

        assert model is not None
        assert meta.accuracy == 0.95

    def test_load_nonexistent_model(self, mock_model_registry):
        """Test chargement modèle inexistant."""
        registry = mock_model_registry

        with pytest.raises(ValueError):
            registry.load_model("nonexistent_model")

        with pytest.raises(FileNotFoundError):
            registry.load_model("nonexistent_model", "1.0.0")

    def test_list_models_empty(self, mock_model_registry):
        """Test listage modèles vide."""
        registry = mock_model_registry

        models = registry.list_models()
        assert models == []

    def test_list_models_with_data(self, mock_model_registry, sample_sklearn_model):
        """Test listage avec modèles."""
        registry = mock_model_registry

        # Sauvegarder plusieurs modèles
        registry.save_model(sample_sklearn_model, "model1", "RandomForest")
        registry.save_model(sample_sklearn_model, "model2", "XGBoost")

        models = registry.list_models()
        assert len(models) == 2

        # Vérifier informations
        model_names = [m["name"] for m in models]
        assert "model1" in model_names
        assert "model2" in model_names

        # Vérifier existence fichiers
        for model in models:
            assert model["file_exists"] is True
            assert model["file_size_mb"] > 0

    def test_get_model_info(self, mock_model_registry, sample_sklearn_model):
        """Test récupération infos modèle."""
        registry = mock_model_registry

        metadata = {"accuracy": 0.95, "training_samples": 1000}
        version = registry.save_model(
            sample_sklearn_model, "test_info", "RandomForest", metadata=metadata
        )

        info = registry.get_model_info("test_info", version)

        assert info["name"] == "test_info"
        assert info["version"] == version
        assert info["accuracy"] == 0.95
        assert info["file_exists"] is True
        assert "file_size_mb" in info

    def test_get_model_info_latest(self, mock_model_registry, sample_sklearn_model):
        """Test infos dernière version."""
        registry = mock_model_registry

        registry.save_model(
            sample_sklearn_model, "test_latest_info", "RandomForest", version="1.0.0"
        )
        registry.save_model(
            sample_sklearn_model, "test_latest_info", "RandomForest", version="2.0.0"
        )

        # Sans version = dernière
        info = registry.get_model_info("test_latest_info")
        assert info["version"] == "2.0.0"

    def test_promote_model(self, mock_model_registry, sample_sklearn_model):
        """Test promotion modèle."""
        registry = mock_model_registry

        version = registry.save_model(sample_sklearn_model, "test_promote", "RandomForest")

        # Promouvoir en production
        registry.promote_model("test_promote", version, "production")

        # Vérifier statut
        info = registry.get_model_info("test_promote", version)
        assert info["status"] == "production"
        assert "promoted_at" in info

    def test_delete_model(self, mock_model_registry, sample_sklearn_model):
        """Test suppression modèle."""
        registry = mock_model_registry

        version = registry.save_model(sample_sklearn_model, "test_delete", "RandomForest")

        # Vérifier existence
        model_file = registry.models_dir / f"test_delete_v{version}.pkl"
        metadata_file = registry.metadata_dir / f"test_delete_v{version}_metadata.json"
        assert model_file.exists()
        assert metadata_file.exists()

        # Supprimer
        registry.delete_model("test_delete", version, confirm=True)

        # Vérifier suppression
        assert not model_file.exists()
        assert not metadata_file.exists()

    def test_delete_model_without_confirm(self, mock_model_registry, sample_sklearn_model):
        """Test suppression sans confirmation."""
        registry = mock_model_registry

        version = registry.save_model(sample_sklearn_model, "test_no_confirm", "RandomForest")

        with pytest.raises(ValueError, match="confirm=True"):
            registry.delete_model("test_no_confirm", version)

    def test_version_generation(self, mock_model_registry, sample_sklearn_model):
        """Test génération versions."""
        registry = mock_model_registry

        # Première version
        v1 = registry.save_model(sample_sklearn_model, "test_versions", "RandomForest")
        assert v1 == "1.0.0"

        # Deuxième version
        v2 = registry.save_model(sample_sklearn_model, "test_versions", "RandomForest")
        assert v2 == "1.1.0"

        # Troisième version
        v3 = registry.save_model(sample_sklearn_model, "test_versions", "RandomForest")
        assert v3 == "1.2.0"

    def test_version_generation_with_packaging(self, mock_model_registry, sample_sklearn_model):
        """Test génération versions avec packaging."""
        registry = mock_model_registry

        # Versions dans le désordre
        registry.save_model(sample_sklearn_model, "test_packaging", "RandomForest", version="1.0.0")
        registry.save_model(sample_sklearn_model, "test_packaging", "RandomForest", version="2.0.0")
        registry.save_model(sample_sklearn_model, "test_packaging", "RandomForest", version="1.5.0")

        # Nouvelle version automatique
        new_version = registry.save_model(sample_sklearn_model, "test_packaging", "RandomForest")

        # Doit être supérieure à 2.0.0
        from packaging import version

        assert version.parse(new_version) > version.parse("2.0.0")

    def test_get_latest_version(self, mock_model_registry, sample_sklearn_model):
        """Test récupération dernière version."""
        registry = mock_model_registry

        # Pas de version
        latest = registry._get_latest_version("nonexistent")
        assert latest is None

        # Sauvegarder versions
        registry.save_model(
            sample_sklearn_model, "test_latest_version", "RandomForest", version="1.0.0"
        )
        registry.save_model(
            sample_sklearn_model, "test_latest_version", "RandomForest", version="2.0.0"
        )
        registry.save_model(
            sample_sklearn_model, "test_latest_version", "RandomForest", version="1.5.0"
        )

        latest = registry._get_latest_version("test_latest_version")
        assert latest == "2.0.0"


class TestModelRegistryMLflow:
    """Tests pour l'intégration MLflow."""

    def test_mlflow_logging_disabled(self, mock_model_registry, sample_sklearn_model):
        """Test sauvegarde sans MLflow."""
        registry = mock_model_registry

        version = registry.save_model(
            sample_sklearn_model, "test_no_mlflow", "RandomForest", mlflow_logging=False
        )

        assert version is not None
        # MLflow ne doit pas être appelé (déjà mocké dans conftest)

    def test_mlflow_logging_enabled(self, mock_model_registry, sample_sklearn_model):
        """Test sauvegarde avec MLflow."""
        registry = mock_model_registry

        metadata = {
            "accuracy": 0.95,
            "precision": 0.93,
            "hyperparameters": {"n_estimators": 100},
            "tags": {"experiment": "test"},
        }

        version = registry.save_model(
            sample_sklearn_model,
            "test_with_mlflow",
            "RandomForest",
            metadata=metadata,
            mlflow_logging=True,
        )

        assert version is not None
        # MLflow calls sont mockés, on vérifie juste que ça n'échoue pas

    @patch("mlflow.start_run")
    def test_mlflow_error_handling(self, mock_start_run, mock_model_registry, sample_sklearn_model):
        """Test gestion erreurs MLflow."""
        registry = mock_model_registry

        # Simuler erreur MLflow
        mock_start_run.side_effect = Exception("MLflow error")

        # Sauvegarde doit réussir malgré erreur MLflow
        version = registry.save_model(
            sample_sklearn_model, "test_mlflow_error", "RandomForest", mlflow_logging=True
        )

        assert version is not None


class TestModelRegistryIntegration:
    """Tests d'intégration Model Registry."""

    def test_complete_model_lifecycle(self, mock_model_registry, sample_sklearn_model):
        """Test cycle de vie complet modèle."""
        registry = mock_model_registry

        # 1. Sauvegarder modèle
        metadata = {"accuracy": 0.95, "training_samples": 1000}
        version = registry.save_model(
            sample_sklearn_model, "lifecycle_model", "RandomForest", metadata=metadata
        )

        # 2. Lister modèles
        models = registry.list_models()
        assert len(models) == 1
        assert models[0]["name"] == "lifecycle_model"

        # 3. Charger modèle
        loaded_model = registry.load_model("lifecycle_model", version)
        assert loaded_model is not None

        # 4. Promouvoir modèle
        registry.promote_model("lifecycle_model", version, "production")

        # 5. Vérifier promotion
        info = registry.get_model_info("lifecycle_model", version)
        assert info["status"] == "production"

        # 6. Nouvelle version
        v2 = registry.save_model(sample_sklearn_model, "lifecycle_model", "RandomForest")
        assert v2 != version

        # 7. Charger dernière version
        latest_model = registry.load_model("lifecycle_model")  # Sans version
        assert latest_model is not None

    def test_multiple_models_management(self, mock_model_registry, sample_sklearn_model):
        """Test gestion plusieurs modèles."""
        registry = mock_model_registry

        models_to_create = [
            ("risk_predictor", "RandomForest"),
            ("bug_predictor", "XGBoost"),
            ("anomaly_detector", "IsolationForest"),
        ]

        # Sauvegarder plusieurs modèles
        for name, model_type in models_to_create:
            registry.save_model(sample_sklearn_model, name, model_type)

        # Lister tous
        all_models = registry.list_models()
        assert len(all_models) == 3

        # Vérifier chaque modèle
        model_names = {m["name"] for m in all_models}
        for name, _ in models_to_create:
            assert name in model_names

        # Charger chaque modèle
        for name, _ in models_to_create:
            model = registry.load_model(name)
            assert model is not None

    def test_error_recovery(self, mock_model_registry, sample_sklearn_model):
        """Test récupération d'erreurs."""
        registry = mock_model_registry

        # Sauvegarder modèle valide
        version = registry.save_model(sample_sklearn_model, "error_test", "RandomForest")

        # Corrompre fichier métadonnées
        metadata_file = registry.metadata_dir / f"error_test_v{version}_metadata.json"
        metadata_file.write_text("invalid json content")

        # Charger avec métadonnées corrompues
        model, metadata = registry.load_model("error_test", version, return_metadata=True)

        assert model is not None  # Modèle doit être chargé
        # Métadonnées peuvent être par défaut ou None selon implémentation

    def test_concurrent_access_simulation(self, mock_model_registry, sample_sklearn_model):
        """Test simulation accès concurrent."""
        registry = mock_model_registry

        # Sauvegarder plusieurs versions rapidement
        versions = []
        for i in range(5):
            v = registry.save_model(
                sample_sklearn_model, "concurrent_test", "RandomForest", version=f"1.{i}.0"
            )
            versions.append(v)

        assert len(versions) == 5
        assert len(set(versions)) == 5  # Toutes différentes

        # Vérifier tous les modèles existent
        models = registry.list_models()
        concurrent_models = [m for m in models if m["name"] == "concurrent_test"]
        assert len(concurrent_models) == 5
