"""
Model Registry pour gestion des modèles ML avec versioning et métadonnées.

Système professionnel de gestion des modèles ML avec:
- Versioning des modèles
- Métadonnées et métriques
- Sauvegarde/chargement sécurisé
- Intégration MLFlow
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import mlflow
from pydantic import BaseModel

from .ml_config import ml_config


class ModelMetadata(BaseModel):
    """Métadonnées d'un modèle ML."""

    name: str
    version: str
    model_type: str
    created_at: datetime
    created_by: str = "hyperion-ml-system"

    # Métriques performance
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None

    # Informations entraînement
    training_features: list[str] = []
    training_samples: int | None = None
    hyperparameters: dict[str, Any] = {}

    # Statut et validation
    status: str = "trained"  # trained, validated, production, deprecated
    validation_results: dict[str, Any] = {}

    # Tags et description
    tags: dict[str, str] = {}
    description: str | None = None

    class Config:
        arbitrary_types_allowed = True


class ModelRegistry:
    """
    Registry professionnel pour modèles ML avec intégration MLFlow.

    Gère le cycle de vie complet des modèles:
    - Sauvegarde avec métadonnées
    - Versioning automatique
    - Tracking MLFlow
    - Validation et promotion
    """

    def __init__(self):
        """Initialise le registry."""
        self.models_dir = ml_config.models_dir
        self.metadata_dir = self.models_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)

        # Configuration MLFlow
        mlflow.set_tracking_uri(ml_config.mlflow.tracking_uri)
        self._ensure_mlflow_experiment()

    def _ensure_mlflow_experiment(self):
        """S'assurer que l'expérience MLFlow existe."""
        try:
            experiment = mlflow.get_experiment_by_name(ml_config.mlflow.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    ml_config.mlflow.experiment_name, artifact_location=ml_config.mlflow.artifact_location
                )
                print(f"✅ Expérience MLFlow créée: {experiment_id}")
            else:
                print(f"📋 Expérience MLFlow existante: {experiment.experiment_id}")
        except Exception as e:
            print(f"⚠️ Erreur configuration MLFlow: {e}")

    def save_model(
        self,
        model: Any,
        name: str,
        model_type: str,
        metadata: dict[str, Any] | None = None,
        version: str | None = None,
        mlflow_logging: bool = True,
    ) -> str:
        """
        Sauvegarde un modèle avec métadonnées complètes.

        Args:
            model: Modèle ML à sauvegarder
            name: Nom du modèle
            model_type: Type du modèle (RandomForest, XGBoost, etc.)
            metadata: Métadonnées additionnelles
            version: Version explicite (auto-incrémentée si None)
            mlflow_logging: Activer logging MLFlow

        Returns:
            Version du modèle sauvegardé
        """
        # Générer version si non fournie
        if version is None:
            version = self._generate_version(name)

        # Préparer métadonnées
        model_metadata = ModelMetadata(
            name=name, version=version, model_type=model_type, created_at=datetime.now(), **(metadata or {})
        )

        # Chemins de sauvegarde
        model_filename = f"{name}_v{version}.pkl"
        model_path = self.models_dir / model_filename
        metadata_path = self.metadata_dir / f"{name}_v{version}_metadata.json"

        try:
            # Sauvegarder modèle
            if hasattr(model, "save_model"):
                # XGBoost/LightGBM natif
                model.save_model(str(model_path))
            else:
                # Scikit-learn et autres (joblib pour performance)
                joblib.dump(model, model_path, compress=3)

            # Sauvegarder métadonnées
            metadata_dict = model_metadata.dict()
            # Convertir datetime en string pour JSON
            if "created_at" in metadata_dict and isinstance(metadata_dict["created_at"], datetime):
                metadata_dict["created_at"] = metadata_dict["created_at"].isoformat()

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

            # Logging MLFlow si activé
            if mlflow_logging:
                self._log_to_mlflow(model, model_metadata, model_path)

            print(f"✅ Modèle sauvegardé: {name} v{version}")
            print(f"   📁 Fichier: {model_path}")
            print(f"   📋 Métadonnées: {metadata_path}")

            return version

        except Exception as e:
            print(f"❌ Erreur sauvegarde modèle {name}: {e}")
            # Nettoyer fichiers partiels
            for path in [model_path, metadata_path]:
                if path.exists():
                    path.unlink()
            raise

    def load_model(
        self, name: str, version: str | None = None, return_metadata: bool = False
    ) -> Any | tuple[Any, ModelMetadata]:
        """
        Charge un modèle avec version spécifique ou latest.

        Args:
            name: Nom du modèle
            version: Version spécifique (latest si None)
            return_metadata: Retourner aussi les métadonnées

        Returns:
            Modèle chargé (et métadonnées si demandées)
        """
        # Déterminer version à charger
        if version is None:
            version = self._get_latest_version(name)
            if version is None:
                raise ValueError(f"Aucun modèle trouvé pour {name}")

        # Chemins
        model_filename = f"{name}_v{version}.pkl"
        model_path = self.models_dir / model_filename
        metadata_path = self.metadata_dir / f"{name}_v{version}_metadata.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Modèle non trouvé: {model_path}")

        try:
            # Charger modèle
            model = joblib.load(model_path)

            # Charger métadonnées si demandées
            if return_metadata:
                if metadata_path.exists():
                    with open(metadata_path, encoding="utf-8") as f:
                        metadata_dict = json.load(f)

                    # Convertir string datetime en datetime object
                    if "created_at" in metadata_dict and isinstance(metadata_dict["created_at"], str):
                        metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])

                    metadata = ModelMetadata(**metadata_dict)
                else:
                    # Métadonnées basiques si fichier manquant
                    metadata = ModelMetadata(
                        name=name, version=version, model_type="unknown", created_at=datetime.now()
                    )

                return model, metadata
            else:
                return model

        except Exception as e:
            print(f"❌ Erreur chargement modèle {name} v{version}: {e}")
            raise

    def list_models(self) -> list[dict[str, Any]]:
        """Liste tous les modèles disponibles avec leurs métadonnées."""
        models_info = []

        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata = json.load(f)

                # Convertir string datetime en datetime object si nécessaire
                if "created_at" in metadata and isinstance(metadata["created_at"], str):
                    metadata["created_at"] = datetime.fromisoformat(metadata["created_at"])

                # Vérifier existence fichier modèle
                model_filename = f"{metadata['name']}_v{metadata['version']}.pkl"
                model_path = self.models_dir / model_filename
                metadata["file_exists"] = model_path.exists()
                metadata["file_size_mb"] = (
                    round(model_path.stat().st_size / (1024 * 1024), 2) if model_path.exists() else 0
                )

                models_info.append(metadata)

            except Exception as e:
                print(f"⚠️ Erreur lecture métadonnées {metadata_file}: {e}")
                continue

        # Trier par nom puis version
        models_info.sort(key=lambda x: (x["name"], x["version"]))
        return models_info

    def get_model_info(self, name: str, version: str | None = None) -> dict[str, Any]:
        """Récupère les informations détaillées d'un modèle."""
        if version is None:
            version = self._get_latest_version(name)

        metadata_path = self.metadata_dir / f"{name}_v{version}_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Métadonnées non trouvées pour {name} v{version}")

        with open(metadata_path, encoding="utf-8") as f:
            info = json.load(f)

        # Convertir string datetime en datetime object si nécessaire
        if "created_at" in info and isinstance(info["created_at"], str):
            info["created_at"] = datetime.fromisoformat(info["created_at"])

        # Ajouter informations fichier
        model_filename = f"{name}_v{version}.pkl"
        model_path = self.models_dir / model_filename
        info["file_exists"] = model_path.exists()
        if model_path.exists():
            stat = model_path.stat()
            info["file_size_mb"] = round(stat.st_size / (1024 * 1024), 2)
            info["file_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return info

    def promote_model(self, name: str, version: str, status: str = "production"):
        """Promeut un modèle vers un nouveau statut."""
        metadata_path = self.metadata_dir / f"{name}_v{version}_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Modèle non trouvé: {name} v{version}")

        # Charger et mettre à jour métadonnées
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)

        # Convertir string datetime en datetime object si nécessaire
        if "created_at" in metadata and isinstance(metadata["created_at"], str):
            metadata["created_at"] = datetime.fromisoformat(metadata["created_at"])

        old_status = metadata.get("status", "unknown")
        metadata["status"] = status
        metadata["promoted_at"] = datetime.now().isoformat()

        # Convertir datetime en string pour JSON
        if 'created_at' in metadata and isinstance(metadata['created_at'], datetime):
            metadata['created_at'] = metadata['created_at'].isoformat()

        # Sauvegarder
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"✅ Modèle {name} v{version} promu: {old_status} → {status}")

    def delete_model(self, name: str, version: str, confirm: bool = False):
        """Supprime un modèle et ses métadonnées."""
        if not confirm:
            raise ValueError("Suppression requiert confirm=True pour sécurité")

        model_filename = f"{name}_v{version}.pkl"
        model_path = self.models_dir / model_filename
        metadata_path = self.metadata_dir / f"{name}_v{version}_metadata.json"

        deleted_files = []
        for path in [model_path, metadata_path]:
            if path.exists():
                path.unlink()
                deleted_files.append(path.name)

        if deleted_files:
            print(f"✅ Fichiers supprimés: {deleted_files}")
        else:
            print(f"⚠️ Aucun fichier trouvé pour {name} v{version}")

    def _generate_version(self, name: str) -> str:
        """Génère une nouvelle version pour un modèle."""
        existing_versions = []

        for metadata_file in self.metadata_dir.glob(f"{name}_v*_metadata.json"):
            try:
                version_str = metadata_file.stem.split(f"{name}_v")[1].split("_metadata")[0]
                existing_versions.append(version_str)
            except (IndexError, ValueError):
                continue

        if not existing_versions:
            return "1.0.0"

        # Trouver la version la plus récente et incrémenter
        try:
            # Trier par version sémantique
            from packaging import version

            versions = [version.parse(v) for v in existing_versions]
            latest = max(versions)

            # Incrémenter version mineure
            return f"{latest.major}.{latest.minor + 1}.0"

        except Exception:
            # Fallback: incrémenter simplement
            return f"1.{len(existing_versions)}.0"

    def _get_latest_version(self, name: str) -> str | None:
        """Récupère la dernière version d'un modèle."""
        versions = []

        for metadata_file in self.metadata_dir.glob(f"{name}_v*_metadata.json"):
            try:
                version_str = metadata_file.stem.split(f"{name}_v")[1].split("_metadata")[0]
                versions.append(version_str)
            except (IndexError, ValueError):
                continue

        if not versions:
            return None

        try:
            from packaging import version

            parsed_versions = [version.parse(v) for v in versions]
            latest = max(parsed_versions)
            return str(latest)
        except Exception:
            # Fallback: trier alphabétiquement
            return sorted(versions)[-1]

    def _log_to_mlflow(self, model: Any, metadata: ModelMetadata, model_path: Path):
        """Log modèle et métadonnées vers MLFlow."""
        try:
            with mlflow.start_run():
                # Log hyperparamètres
                if metadata.hyperparameters:
                    for param, value in metadata.hyperparameters.items():
                        mlflow.log_param(param, value)

                # Log métriques
                metrics_to_log = {
                    "accuracy": metadata.accuracy,
                    "precision": metadata.precision,
                    "recall": metadata.recall,
                    "f1_score": metadata.f1_score,
                }
                for metric, value in metrics_to_log.items():
                    if value is not None:
                        mlflow.log_metric(metric, value)

                # Log tags
                tags = {
                    "model_name": metadata.name,
                    "model_version": metadata.version,
                    "model_type": metadata.model_type,
                    "status": metadata.status,
                    **metadata.tags,
                    **ml_config.mlflow.default_tags,
                }
                mlflow.set_tags(tags)

                # Log artifact (modèle)
                mlflow.log_artifact(str(model_path), artifact_path="models")

                # Log modèle avec format natif si possible
                try:
                    if hasattr(model, "fit"):  # Scikit-learn style
                        mlflow.sklearn.log_model(model, "sklearn_model")
                except Exception:
                    pass  # Ignore si pas supporté

        except Exception as e:
            print(f"⚠️ Erreur logging MLFlow: {e}")


# Instance globale du registry
model_registry = ModelRegistry()
