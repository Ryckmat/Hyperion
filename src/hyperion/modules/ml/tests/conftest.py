"""
Configuration pytest pour les tests ML d'Hyperion.

Fixtures communes et setup pour tous les tests ML.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from hyperion.modules.ml.infrastructure.feature_store import FeatureStore
from hyperion.modules.ml.infrastructure.ml_config import MLConfig
from hyperion.modules.ml.infrastructure.model_registry import ModelRegistry


@pytest.fixture
def sample_training_data():
    """DataFrame d'exemple pour les tests d'entraînement."""
    np.random.seed(42)
    n_samples = 100

    data = {
        # Features numériques
        "complexite_cyclomatique": np.random.uniform(1, 20, n_samples),
        "nb_methodes": np.random.randint(1, 50, n_samples),
        "densite_commentaires": np.random.uniform(0, 0.5, n_samples),
        "nb_contributeurs_uniques": np.random.randint(1, 10, n_samples),
        "frequence_commits": np.random.uniform(0.1, 5.0, n_samples),
        "experience_auteur": np.random.uniform(0, 10, n_samples),
        "age_fichier_jours": np.random.randint(1, 1000, n_samples),
        # Target pour classification
        "risque_reel": np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_bug_prediction_data():
    """DataFrame d'exemple pour prédiction de bugs."""
    np.random.seed(42)
    n_samples = 150

    data = {
        "complexite_cyclomatique": np.random.uniform(1, 25, n_samples),
        "nb_bugs_historiques": np.random.randint(0, 20, n_samples),
        "nb_hotfixes": np.random.randint(0, 5, n_samples),
        "couverture_tests": np.random.uniform(0, 1, n_samples),
        "volatilite_fichier": np.random.uniform(0, 10, n_samples),
        "nb_contributeurs_uniques": np.random.randint(1, 15, n_samples),
        # Target: bug dans les 30 prochains jours
        "bug_dans_30j": np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
    }

    return pd.DataFrame(data)


@pytest.fixture
def temp_ml_directory():
    """Répertoire temporaire pour les tests ML."""
    temp_dir = Path(tempfile.mkdtemp(prefix="hyperion_ml_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ml_config(temp_ml_directory):
    """Configuration ML mock pour les tests."""
    config = MLConfig()

    # Override paths pour utiliser le répertoire temporaire
    config.data_dir = temp_ml_directory / "data"
    config.models_dir = temp_ml_directory / "models"
    config.logs_dir = temp_ml_directory / "logs"

    # Créer les répertoires
    for directory in [config.data_dir, config.models_dir, config.logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    return config


@pytest.fixture
def mock_model_registry(mock_ml_config):
    """Model Registry mock pour les tests."""
    # Mock MLflow pour éviter les dépendances externes
    import mlflow

    mlflow.set_tracking_uri = MagicMock()
    mlflow.get_experiment_by_name = MagicMock(return_value=None)
    mlflow.create_experiment = MagicMock(return_value="test_experiment_id")

    registry = ModelRegistry()
    registry.models_dir = mock_ml_config.models_dir
    registry.metadata_dir = registry.models_dir / "metadata"
    registry.metadata_dir.mkdir(exist_ok=True)

    return registry


@pytest.fixture
def mock_feature_store(temp_ml_directory):
    """Feature Store mock pour les tests."""
    store = FeatureStore(ttl_hours=24)
    store.store_dir = temp_ml_directory / "feature_store"
    store.metadata_dir = store.store_dir / "metadata"
    store.cache_dir = store.store_dir / "cache"

    # Créer dossiers
    for directory in [store.store_dir, store.metadata_dir, store.cache_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    return store


@pytest.fixture
def sample_features():
    """Features d'exemple pour les tests."""
    return {
        "complexite_cyclomatique": 15.5,
        "nb_methodes": 25,
        "densite_commentaires": 0.3,
        "nb_contributeurs_uniques": 5,
        "frequence_commits": 2.1,
        "experience_auteur": 3.5,
    }


@pytest.fixture
def sample_sklearn_model():
    """Modèle scikit-learn simple pour les tests."""
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier

    # Générer données d'entraînement simple
    X, y = make_classification(n_samples=100, n_features=4, n_classes=2, random_state=42)

    # Entraîner modèle simple
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    return model


@pytest.fixture(autouse=True)
def mock_mlflow():
    """Mock MLflow pour tous les tests par défaut."""
    import mlflow

    # Mock des principales fonctions MLflow
    mlflow.set_tracking_uri = MagicMock()
    mlflow.get_experiment_by_name = MagicMock(return_value=None)
    mlflow.create_experiment = MagicMock(return_value="test_exp")
    mlflow.start_run = MagicMock()
    mlflow.log_param = MagicMock()
    mlflow.log_metric = MagicMock()
    mlflow.set_tags = MagicMock()
    mlflow.log_artifact = MagicMock()
    mlflow.sklearn = MagicMock()
    mlflow.sklearn.log_model = MagicMock()

    # Context manager pour start_run
    mlflow.start_run.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mlflow.start_run.return_value.__exit__ = MagicMock(return_value=None)


@pytest.fixture
def invalid_data():
    """Données invalides pour tester la validation."""
    return pd.DataFrame(
        {
            "feature1": [1, 2, np.nan, np.nan, np.nan],  # Beaucoup de NaN
            "feature2": ["a", "b", "c", "d", "e"],  # Type incorrect
            "feature3": [1, 1, 1, 1, 1],  # Valeurs constantes
            "target": [0, 1, 0, np.nan, 1],  # Target avec NaN
        }
    )
