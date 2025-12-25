"""
Tests pour le Feature Store d'Hyperion.

Teste le stockage, versioning et récupération des features.
"""

import time
from datetime import datetime, timedelta

import pytest

from hyperion.modules.ml.infrastructure.feature_store import (
    FeatureMetadata,
    FeatureStore,
)


class TestFeatureMetadata:
    """Tests pour les métadonnées des features."""

    def test_feature_metadata_creation(self):
        """Test création métadonnées features."""
        metadata = FeatureMetadata(
            feature_set_id="test_123",
            source_file="/path/to/file.py",
            repository="hyperion",
            extracted_at=datetime.now(),
            feature_names=["feature1", "feature2"],
            n_features=2,
            content_hash="abc123",
            source_hash="def456",
        )

        assert metadata.feature_set_id == "test_123"
        assert metadata.source_file == "/path/to/file.py"
        assert metadata.repository == "hyperion"
        assert metadata.n_features == 2
        assert len(metadata.feature_names) == 2

    def test_feature_metadata_defaults(self):
        """Test valeurs par défaut métadonnées."""
        metadata = FeatureMetadata(
            feature_set_id="test_123",
            source_file="/path/to/file.py",
            repository="hyperion",
            extracted_at=datetime.now(),
            feature_names=["feature1"],
            n_features=1,
            content_hash="abc123",
            source_hash="def456",
        )

        assert metadata.extraction_version == "3.0.0"
        assert metadata.tags == {}
        assert metadata.extraction_time_ms is None

    def test_feature_metadata_with_tags(self):
        """Test métadonnées avec tags."""
        metadata = FeatureMetadata(
            feature_set_id="test_123",
            source_file="/path/to/file.py",
            repository="hyperion",
            extracted_at=datetime.now(),
            feature_names=["feature1"],
            n_features=1,
            content_hash="abc123",
            source_hash="def456",
            tags={"version": "1.0", "author": "test"},
            extraction_time_ms=150.5,
        )

        assert metadata.tags["version"] == "1.0"
        assert metadata.tags["author"] == "test"
        assert metadata.extraction_time_ms == 150.5


class TestFeatureStore:
    """Tests pour le Feature Store principal."""

    def test_feature_store_initialization(self, mock_feature_store):
        """Test initialisation Feature Store."""
        store = mock_feature_store

        assert store.store_dir.exists()
        assert store.metadata_dir.exists()
        assert store.cache_dir.exists()
        assert store.ttl.total_seconds() == 24 * 3600  # 24 heures

    def test_store_and_retrieve_features(self, mock_feature_store, sample_features):
        """Test stockage et récupération features."""
        store = mock_feature_store

        # Stocker features
        feature_set_id = store.store_features(
            features=sample_features,
            source_file="/test/file.py",
            repository="test_repo",
        )

        assert feature_set_id is not None
        assert len(feature_set_id) > 0

        # Récupérer features
        retrieved_features = store.get_features(
            source_file="/test/file.py", repository="test_repo"
        )

        assert retrieved_features is not None
        assert retrieved_features == sample_features

    def test_store_features_with_metadata(self, mock_feature_store, sample_features):
        """Test stockage avec métadonnées complètes."""
        store = mock_feature_store

        store.store_features(
            features=sample_features,
            source_file="/test/file.py",
            repository="test_repo",
            feature_names=list(sample_features.keys()),
            tags={"version": "1.0", "test": "true"},
            extraction_time_ms=123.45,
        )

        # Récupérer avec métadonnées
        features, metadata = store.get_features(
            source_file="/test/file.py", repository="test_repo", return_metadata=True
        )

        assert features == sample_features
        assert metadata.tags["version"] == "1.0"
        assert metadata.extraction_time_ms == 123.45
        assert metadata.n_features == len(sample_features)

    def test_get_nonexistent_features(self, mock_feature_store):
        """Test récupération features inexistantes."""
        store = mock_feature_store

        features = store.get_features(
            source_file="/nonexistent/file.py", repository="test_repo"
        )

        assert features is None

    def test_get_features_without_freshness_check(
        self, mock_feature_store, sample_features
    ):
        """Test récupération sans vérification fraîcheur."""
        store = mock_feature_store

        # Stocker features
        store.store_features(
            features=sample_features,
            source_file="/test/file.py",
            repository="test_repo",
        )

        # Récupérer sans check fraîcheur
        features = store.get_features(
            source_file="/test/file.py", repository="test_repo", check_freshness=False
        )

        assert features == sample_features

    def test_list_feature_sets_empty(self, mock_feature_store):
        """Test listage feature sets vide."""
        store = mock_feature_store

        feature_sets = store.list_feature_sets()
        assert feature_sets == []

    def test_list_feature_sets_with_data(self, mock_feature_store, sample_features):
        """Test listage avec données."""
        store = mock_feature_store

        # Stocker plusieurs feature sets
        store.store_features(sample_features, "/file1.py", "repo1")
        store.store_features(sample_features, "/file2.py", "repo1")
        store.store_features(sample_features, "/file3.py", "repo2")

        # Lister tous
        all_sets = store.list_feature_sets()
        assert len(all_sets) == 3

        # Filtrer par repository
        repo1_sets = store.list_feature_sets(repository="repo1")
        assert len(repo1_sets) == 2

        repo2_sets = store.list_feature_sets(repository="repo2")
        assert len(repo2_sets) == 1

    def test_cleanup_expired_no_expired(self, mock_feature_store, sample_features):
        """Test nettoyage sans features expirées."""
        store = mock_feature_store

        # Stocker features récentes
        store.store_features(sample_features, "/file1.py", "repo1")

        # Nettoyer
        deleted_count = store.cleanup_expired()
        assert deleted_count == 0

    def test_get_feature_statistics_empty(self, mock_feature_store):
        """Test statistiques store vide."""
        store = mock_feature_store

        stats = store.get_feature_statistics()

        assert stats["total_feature_sets"] == 0
        assert stats["fresh_feature_sets"] == 0
        assert stats["expired_feature_sets"] == 0
        assert stats["unique_repositories"] == 0

    def test_get_feature_statistics_with_data(
        self, mock_feature_store, sample_features
    ):
        """Test statistiques avec données."""
        store = mock_feature_store

        # Stocker features
        store.store_features(sample_features, "/file1.py", "repo1")
        store.store_features(sample_features, "/file2.py", "repo2")

        stats = store.get_feature_statistics()

        assert stats["total_feature_sets"] == 2
        assert stats["fresh_feature_sets"] == 2
        assert stats["expired_feature_sets"] == 0
        assert stats["unique_repositories"] == 2
        assert "repo1" in stats["repository_stats"]
        assert "repo2" in stats["repository_stats"]

    def test_search_features_empty(self, mock_feature_store):
        """Test recherche dans store vide."""
        store = mock_feature_store

        results = store.search_features("test")
        assert results == []

    def test_search_features_by_source_file(self, mock_feature_store, sample_features):
        """Test recherche par fichier source."""
        store = mock_feature_store

        store.store_features(sample_features, "/path/to/important_file.py", "repo1")
        store.store_features(sample_features, "/path/to/other_file.py", "repo1")

        # Rechercher par nom fichier
        results = store.search_features("important")
        assert len(results) == 1
        assert "important_file.py" in results[0]["source_file"]

    def test_search_features_by_feature_names(self, mock_feature_store):
        """Test recherche par noms de features."""
        store = mock_feature_store

        features1 = {"complexity_metric": 10, "bug_count": 5}
        features2 = {"performance_score": 8, "maintainability": 9}

        store.store_features(features1, "/file1.py", "repo1")
        store.store_features(features2, "/file2.py", "repo1")

        # Rechercher par feature
        results = store.search_features("complexity")
        assert len(results) == 1

        results = store.search_features("performance")
        assert len(results) == 1

    def test_search_features_by_tags(self, mock_feature_store, sample_features):
        """Test recherche par tags."""
        store = mock_feature_store

        store.store_features(
            sample_features,
            "/file1.py",
            "repo1",
            tags={"version": "1.0", "environment": "production"},
        )

        store.store_features(
            sample_features,
            "/file2.py",
            "repo1",
            tags={"version": "2.0", "environment": "development"},
        )

        # Rechercher par tag
        results = store.search_features("production")
        assert len(results) == 1

        results = store.search_features("development")
        assert len(results) == 1

    def test_feature_set_id_generation(self, mock_feature_store):
        """Test génération ID feature set."""
        store = mock_feature_store

        # Mêmes paramètres doivent donner même ID
        id1 = store._generate_feature_set_id("/path/file.py", "repo")
        id2 = store._generate_feature_set_id("/path/file.py", "repo")
        assert id1 == id2

        # Paramètres différents doivent donner IDs différents
        id3 = store._generate_feature_set_id("/other/file.py", "repo")
        assert id1 != id3

        id4 = store._generate_feature_set_id("/path/file.py", "other_repo")
        assert id1 != id4

    def test_content_hash_calculation(self, mock_feature_store):
        """Test calcul hash contenu."""
        store = mock_feature_store

        features1 = {"a": 1, "b": 2}
        features2 = {"a": 1, "b": 2}
        features3 = {"a": 1, "b": 3}

        hash1 = store._calculate_content_hash(features1)
        hash2 = store._calculate_content_hash(features2)
        hash3 = store._calculate_content_hash(features3)

        # Même contenu = même hash
        assert hash1 == hash2

        # Contenu différent = hash différent
        assert hash1 != hash3

    def test_file_hash_calculation(self, mock_feature_store, tmp_path):
        """Test calcul hash fichier."""
        store = mock_feature_store

        # Créer fichier temporaire
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash1 = store._calculate_file_hash(str(test_file))
        assert hash1 != "unknown"

        # Même fichier = même hash
        hash2 = store._calculate_file_hash(str(test_file))
        assert hash1 == hash2

        # Modifier fichier
        test_file.write_text("Different content")
        hash3 = store._calculate_file_hash(str(test_file))
        assert hash1 != hash3

        # Fichier inexistant
        hash_nonexistent = store._calculate_file_hash("/nonexistent/file.txt")
        assert hash_nonexistent == "unknown"


class TestFeatureStoreFreshness:
    """Tests pour la gestion de fraîcheur des features."""

    def test_freshness_check_recent(self, mock_feature_store, sample_features):
        """Test features récentes sont fraîches."""
        store = mock_feature_store

        # Stocker features
        store.store_features(sample_features, "/file.py", "repo")

        # Récupérer immédiatement (doit être frais)
        features = store.get_features("/file.py", "repo", check_freshness=True)
        assert features is not None

    def test_freshness_check_expired_ttl(self, mock_feature_store, sample_features):
        """Test features expirées par TTL."""
        # Store avec TTL très court
        store = FeatureStore(ttl_hours=0.001)  # ~3.6 secondes
        store.store_dir = mock_feature_store.store_dir
        store.metadata_dir = mock_feature_store.metadata_dir
        store.cache_dir = mock_feature_store.cache_dir

        # Stocker features
        store.store_features(sample_features, "/file.py", "repo")

        # Attendre expiration
        time.sleep(0.1)  # 100ms > 3.6 secondes en test

        # Mock expiration en modifiant TTL pour simulation
        store.ttl = timedelta(microseconds=1)

        # Récupérer (doit être expiré)
        features = store.get_features("/file.py", "repo", check_freshness=True)
        assert features is None

    def test_is_fresh_method(self, mock_feature_store):
        """Test méthode _is_fresh."""
        store = mock_feature_store

        # Métadonnées récentes
        recent_metadata = FeatureMetadata(
            feature_set_id="test",
            source_file="/test.py",
            repository="repo",
            extracted_at=datetime.now(),
            feature_names=["f1"],
            n_features=1,
            content_hash="abc",
            source_hash="def",
        )

        assert store._is_fresh(recent_metadata, "/nonexistent.py") is True

        # Métadonnées anciennes
        old_metadata = FeatureMetadata(
            feature_set_id="test",
            source_file="/test.py",
            repository="repo",
            extracted_at=datetime.now() - timedelta(days=30),
            feature_names=["f1"],
            n_features=1,
            content_hash="abc",
            source_hash="def",
        )

        assert store._is_fresh(old_metadata, "/nonexistent.py") is False


class TestFeatureStoreIntegration:
    """Tests d'intégration Feature Store."""

    def test_complete_workflow(self, mock_feature_store, sample_features):
        """Test workflow complet Feature Store."""
        store = mock_feature_store

        # 1. Stocker features
        store.store_features(
            features=sample_features,
            source_file="/project/src/main.py",
            repository="hyperion",
            tags={"branch": "main", "commit": "abc123"},
        )

        # 2. Lister feature sets
        feature_sets = store.list_feature_sets()
        assert len(feature_sets) == 1
        assert feature_sets[0]["repository"] == "hyperion"

        # 3. Rechercher
        search_results = store.search_features("main")
        assert len(search_results) == 1

        # 4. Récupérer avec métadonnées
        features, metadata = store.get_features(
            "/project/src/main.py", "hyperion", return_metadata=True
        )
        assert features == sample_features
        assert metadata.tags["branch"] == "main"

        # 5. Statistiques
        stats = store.get_feature_statistics()
        assert stats["total_feature_sets"] == 1
        assert stats["unique_repositories"] == 1

    def test_multiple_repositories_workflow(self, mock_feature_store, sample_features):
        """Test workflow avec plusieurs repositories."""
        store = mock_feature_store

        # Stocker pour différents repos
        repos = ["repo1", "repo2", "repo3"]
        for i, repo in enumerate(repos):
            store.store_features(
                sample_features, f"/project{i}/file.py", repo, tags={"index": str(i)}
            )

        # Vérifier séparation par repo
        for repo in repos:
            repo_sets = store.list_feature_sets(repository=repo)
            assert len(repo_sets) == 1
            assert repo_sets[0]["repository"] == repo

        # Statistiques globales
        stats = store.get_feature_statistics()
        assert stats["total_feature_sets"] == 3
        assert stats["unique_repositories"] == 3

    def test_error_handling(self, mock_feature_store):
        """Test gestion d'erreurs."""
        store = mock_feature_store

        # Features invalides
        with pytest.raises(Exception):
            store.store_features(
                features=None, source_file="/file.py", repository="repo"
            )  # Invalide

        # Récupération avec paramètres invalides
        features = store.get_features("", "")
        assert features is None
