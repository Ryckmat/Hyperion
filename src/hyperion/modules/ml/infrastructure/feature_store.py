"""
Feature Store pour gestion centralisée des features ML.

Stockage, versioning et récupération des features calculées pour:
- Éviter recalculs coûteux
- Garantir cohérence des features entre entraînement/prédiction
- Historique et versioning des features
- Partage entre différents modèles
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .ml_config import ml_config


class FeatureMetadata(BaseModel):
    """Métadonnées d'un ensemble de features."""

    feature_set_id: str
    source_file: str
    repository: str
    extracted_at: datetime
    feature_names: list[str]
    n_features: int
    extraction_version: str = "3.0.0"

    # Hash pour détection de changements
    content_hash: str
    source_hash: str  # Hash du fichier source

    # Métadonnées supplémentaires
    tags: dict[str, str] = {}
    extraction_time_ms: float | None = None

    class Config:
        arbitrary_types_allowed = True


class FeatureStore:
    """
    Feature Store professionnel pour gestion des features ML.

    Fonctionnalités:
    - Stockage features par fichier/repository
    - Versioning et invalidation automatique
    - Cache avec TTL configurable
    - Recherche et filtrage
    - Métadonnées complètes
    """

    def __init__(self, ttl_hours: float = 24):
        """
        Initialise le feature store.

        Args:
            ttl_hours: Durée de vie du cache en heures
        """
        self.store_dir = ml_config.data_dir / "feature_store"
        self.metadata_dir = self.store_dir / "metadata"
        self.cache_dir = self.store_dir / "cache"

        # Créer dossiers
        for directory in [self.store_dir, self.metadata_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self.ttl = timedelta(hours=ttl_hours)

    def store_features(
        self,
        features: dict[str, Any],
        source_file: str,
        repository: str,
        feature_names: list[str] | None = None,
        tags: dict[str, str] | None = None,
        extraction_time_ms: float | None = None,
    ) -> str:
        """
        Stocke un ensemble de features avec métadonnées.

        Args:
            features: Dictionnaire des features calculées
            source_file: Chemin du fichier source
            repository: Nom du repository
            feature_names: Liste explicite des noms de features
            tags: Tags additionnels
            extraction_time_ms: Temps d'extraction en millisecondes

        Returns:
            ID unique du feature set stocké
        """
        # Générer ID unique basé sur fichier + repository
        feature_set_id = self._generate_feature_set_id(source_file, repository)

        # Calculer hash du contenu
        content_hash = self._calculate_content_hash(features)
        source_hash = (
            self._calculate_file_hash(source_file) if Path(source_file).exists() else "unknown"
        )

        # Préparer métadonnées
        if feature_names is None:
            feature_names = list(features.keys())

        metadata = FeatureMetadata(
            feature_set_id=feature_set_id,
            source_file=source_file,
            repository=repository,
            extracted_at=datetime.now(),
            feature_names=feature_names,
            n_features=len(features),
            content_hash=content_hash,
            source_hash=source_hash,
            tags=tags or {},
            extraction_time_ms=extraction_time_ms,
        )

        try:
            # Sauvegarder features
            features_path = self.cache_dir / f"{feature_set_id}.pkl"
            with open(features_path, "wb") as f:
                pickle.dump(features, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Sauvegarder métadonnées
            metadata_path = self.metadata_dir / f"{feature_set_id}_metadata.json"
            metadata_dict = metadata.dict()
            # Convertir datetime en string pour JSON
            if "extracted_at" in metadata_dict and isinstance(
                metadata_dict["extracted_at"], datetime
            ):
                metadata_dict["extracted_at"] = metadata_dict["extracted_at"].isoformat()

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

            print(f"✅ Features stockées: {feature_set_id}")
            print(f"   📁 {len(features)} features pour {source_file}")

            return feature_set_id

        except Exception as e:
            print(f"❌ Erreur stockage features: {e}")
            raise

    def get_features(
        self,
        source_file: str,
        repository: str,
        check_freshness: bool = True,
        return_metadata: bool = False,
    ) -> dict[str, Any] | None | tuple[dict[str, Any] | None, FeatureMetadata | None]:
        """
        Récupère des features stockées.

        Args:
            source_file: Chemin du fichier source
            repository: Nom du repository
            check_freshness: Vérifier fraîcheur (TTL + hash fichier)
            return_metadata: Retourner aussi les métadonnées

        Returns:
            Features (et métadonnées si demandées) ou None si non trouvées/expirées
        """
        feature_set_id = self._generate_feature_set_id(source_file, repository)

        # Chemins
        features_path = self.cache_dir / f"{feature_set_id}.pkl"
        metadata_path = self.metadata_dir / f"{feature_set_id}_metadata.json"

        # Vérifier existence
        if not features_path.exists() or not metadata_path.exists():
            return (None, None) if return_metadata else None

        try:
            # Charger métadonnées
            with open(metadata_path, encoding="utf-8") as f:
                metadata_dict = json.load(f)

            # Convertir string datetime en datetime object
            if "extracted_at" in metadata_dict and isinstance(metadata_dict["extracted_at"], str):
                metadata_dict["extracted_at"] = datetime.fromisoformat(
                    metadata_dict["extracted_at"]
                )

            metadata = FeatureMetadata(**metadata_dict)

            # Vérifier fraîcheur si demandé
            if check_freshness and not self._is_fresh(metadata, source_file):
                print(f"📅 Features expirées pour {source_file}")
                return (None, None) if return_metadata else None

            # Charger features
            with open(features_path, "rb") as f:
                features: dict[str, Any] = pickle.load(f)

            print(f"✅ Features récupérées du cache: {feature_set_id}")

            if return_metadata:
                return features, metadata
            else:
                return features

        except Exception as e:
            print(f"❌ Erreur chargement features: {e}")
            return (None, None) if return_metadata else None

    def list_feature_sets(
        self, repository: str | None = None, include_expired: bool = False
    ) -> list[dict[str, Any]]:
        """
        Liste les ensembles de features disponibles.

        Args:
            repository: Filtrer par repository
            include_expired: Inclure les features expirées

        Returns:
            Liste des métadonnées des feature sets
        """
        feature_sets = []

        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata_dict = json.load(f)

                # Convertir string datetime en datetime object
                if "extracted_at" in metadata_dict and isinstance(
                    metadata_dict["extracted_at"], str
                ):
                    metadata_dict["extracted_at"] = datetime.fromisoformat(
                        metadata_dict["extracted_at"]
                    )

                metadata = FeatureMetadata(**metadata_dict)

                # Filtrer par repository si spécifié
                if repository and metadata.repository != repository:
                    continue

                # Vérifier fraîcheur si demandé
                if not include_expired and not self._is_fresh(metadata, metadata.source_file):
                    continue

                # Ajouter informations supplémentaires
                info = metadata.dict()
                info["is_fresh"] = self._is_fresh(metadata, metadata.source_file)

                # Taille du cache
                features_path = self.cache_dir / f"{metadata.feature_set_id}.pkl"
                if features_path.exists():
                    info["cache_size_mb"] = round(features_path.stat().st_size / (1024 * 1024), 2)

                feature_sets.append(info)

            except Exception as e:
                print(f"⚠️ Erreur lecture métadonnées {metadata_file}: {e}")
                continue

        # Trier par date de création
        feature_sets.sort(key=lambda x: x["extracted_at"], reverse=True)
        return feature_sets

    def cleanup_expired(self) -> int:
        """
        Nettoie les features expirées.

        Returns:
            Nombre de feature sets supprimés
        """
        deleted_count = 0

        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata_dict = json.load(f)

                # Convertir string datetime en datetime object
                if "extracted_at" in metadata_dict and isinstance(
                    metadata_dict["extracted_at"], str
                ):
                    metadata_dict["extracted_at"] = datetime.fromisoformat(
                        metadata_dict["extracted_at"]
                    )

                metadata = FeatureMetadata(**metadata_dict)

                # Vérifier si expiré
                if not self._is_fresh(metadata, metadata.source_file):
                    # Supprimer fichiers associés
                    feature_set_id = metadata.feature_set_id
                    features_path = self.cache_dir / f"{feature_set_id}.pkl"

                    files_deleted = []
                    for path in [features_path, metadata_file]:
                        if path.exists():
                            path.unlink()
                            files_deleted.append(path.name)

                    if files_deleted:
                        deleted_count += 1
                        print(f"🗑️ Supprimé feature set expiré: {feature_set_id}")

            except Exception as e:
                print(f"⚠️ Erreur nettoyage {metadata_file}: {e}")
                continue

        if deleted_count > 0:
            print(f"✅ Nettoyage terminé: {deleted_count} feature sets supprimés")
        else:
            print("📝 Aucun feature set expiré à nettoyer")

        return deleted_count

    def get_feature_statistics(self) -> dict[str, Any]:
        """Récupère des statistiques sur le feature store."""
        all_sets = self.list_feature_sets(include_expired=True)
        fresh_sets = self.list_feature_sets(include_expired=False)

        repositories = {fs["repository"] for fs in all_sets}
        total_cache_size = sum(fs.get("cache_size_mb", 0) for fs in all_sets)

        # Statistiques par repository
        repo_stats = {}
        for repo in repositories:
            repo_sets = [fs for fs in all_sets if fs["repository"] == repo]
            repo_stats[repo] = {
                "total_feature_sets": len(repo_sets),
                "fresh_feature_sets": len([fs for fs in repo_sets if fs.get("is_fresh", False)]),
                "cache_size_mb": sum(fs.get("cache_size_mb", 0) for fs in repo_sets),
            }

        return {
            "total_feature_sets": len(all_sets),
            "fresh_feature_sets": len(fresh_sets),
            "expired_feature_sets": len(all_sets) - len(fresh_sets),
            "total_cache_size_mb": total_cache_size,
            "unique_repositories": len(repositories),
            "repository_stats": repo_stats,
            "most_recent_extraction": (
                max(fs["extracted_at"] for fs in all_sets) if all_sets else None
            ),
        }

    def search_features(
        self, query: str, search_in: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Recherche des feature sets par query.

        Args:
            query: Terme de recherche
            search_in: Champs dans lesquels chercher

        Returns:
            Feature sets correspondants
        """
        if search_in is None:
            search_in = ["source_file", "feature_names", "tags"]
        results = []
        all_sets = self.list_feature_sets(include_expired=True)

        query_lower = query.lower()

        for feature_set in all_sets:
            match_found = False

            # Rechercher dans les champs spécifiés
            for field in search_in:
                if field == "source_file" and query_lower in feature_set["source_file"].lower():
                    match_found = True
                    break
                elif field == "feature_names":
                    if any(query_lower in fname.lower() for fname in feature_set["feature_names"]):
                        match_found = True
                        break
                elif field == "tags":
                    tags_text = " ".join(f"{k}:{v}" for k, v in feature_set["tags"].items())
                    if query_lower in tags_text.lower():
                        match_found = True
                        break

            if match_found:
                results.append(feature_set)

        return results

    def _generate_feature_set_id(self, source_file: str, repository: str) -> str:
        """Génère un ID unique pour un ensemble de features."""
        # Normaliser les chemins
        normalized_file = str(Path(source_file).resolve())
        content = f"{repository}::{normalized_file}"

        # Hash pour ID court mais unique
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _calculate_content_hash(self, features: dict[str, Any]) -> str:
        """Calcule le hash du contenu des features."""
        # Sérialiser de manière déterministe
        content_str = str(sorted(features.items()))
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcule le hash MD5 d'un fichier."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return "unknown"

    def _is_fresh(self, metadata: FeatureMetadata, source_file: str) -> bool:
        """
        Vérifie si des features sont encore fraîches.

        Args:
            metadata: Métadonnées des features
            source_file: Fichier source

        Returns:
            True si les features sont fraîches
        """
        now = datetime.now()

        # Vérifier TTL
        if now - metadata.extracted_at > self.ttl:
            return False

        # Vérifier si le fichier source a changé
        if Path(source_file).exists():
            current_hash = self._calculate_file_hash(source_file)
            if current_hash != metadata.source_hash and current_hash != "unknown":
                return False

        return True


# Instance globale du feature store
feature_store = FeatureStore()
