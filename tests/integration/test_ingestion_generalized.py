"""
Tests d'intégration pour l'ingestion généralisée.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

# Import relatif pour éviter l'exécution du script
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "maintenance"))
from ingest_generalized import GeneralizedIngestion


@pytest.fixture
def sample_repo(tmp_path):
    """Crée un repository d'exemple."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "main.py").write_text("def main(): pass")
    return repo_path


@pytest.fixture
def sample_docs(tmp_path):
    """Crée de la documentation d'exemple."""
    docs_path = tmp_path / "docs"
    docs_path.mkdir()
    (docs_path / "README.md").write_text("# Documentation\n\nExample doc.")
    (docs_path / "guide.md").write_text("# Guide\n\nExample guide.")
    return docs_path


def test_ingestion_initialization():
    """Test initialisation de l'ingestion."""
    ingestion = GeneralizedIngestion()
    assert ingestion.qdrant_host == "localhost"
    assert ingestion.qdrant_port == 6333
    assert isinstance(ingestion.stats, dict)


def test_ingest_documentation(sample_docs):
    """Test ingestion de documentation."""
    ingestion = GeneralizedIngestion()
    count = ingestion.ingest_documentation(sample_docs)

    assert count >= 2  # README + guide
    assert ingestion.stats["docs"] == count


def test_ingest_code_analysis(sample_repo):
    """Test ingestion d'analyse de code."""
    ingestion = GeneralizedIngestion()
    count = ingestion.ingest_code_analysis(sample_repo)

    assert count >= 1  # main.py
    assert ingestion.stats["code"] == count


def test_run_complete_workflow(sample_repo, sample_docs):
    """Test workflow complet d'ingestion."""
    ingestion = GeneralizedIngestion()

    stats = ingestion.run(repo_path=sample_repo, docs_path=sample_docs, tickets_api=None)

    assert "git" in stats
    assert "docs" in stats
    assert "code" in stats
    assert stats["docs"] >= 2
    assert stats["code"] >= 1
