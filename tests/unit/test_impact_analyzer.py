"""
Tests unitaires pour ImpactAnalyzer.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import pytest

from hyperion.modules.impact.analyzer import ImpactAnalyzer


@pytest.fixture
def temp_repo(tmp_path):
    """Crée un repository temporaire pour tests."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Créer des fichiers Python test
    (repo_path / "main.py").write_text(
        """
import utils

def main():
    utils.helper()
"""
    )

    (repo_path / "utils.py").write_text(
        """
def helper():
    pass
"""
    )

    return repo_path


def test_analyzer_initialization(temp_repo):
    """Test initialisation de l'analyseur."""
    analyzer = ImpactAnalyzer(temp_repo)
    assert analyzer.repo_path == temp_repo
    assert isinstance(analyzer.dependency_graph, dict)


def test_analyze_file(temp_repo):
    """Test analyse d'un fichier Python."""
    analyzer = ImpactAnalyzer(temp_repo)
    file_path = temp_repo / "main.py"

    result = analyzer.analyze_file(file_path)

    assert "file" in result
    assert "imports" in result
    assert "functions" in result
    assert "classes" in result
    assert "main" in result["functions"]


def test_extract_imports(temp_repo):
    """Test extraction des imports."""
    analyzer = ImpactAnalyzer(temp_repo)
    file_path = temp_repo / "main.py"

    result = analyzer.analyze_file(file_path)

    assert "utils" in result["imports"]


def test_build_dependency_graph(temp_repo):
    """Test construction du graphe de dépendances."""
    analyzer = ImpactAnalyzer(temp_repo)
    graph = analyzer.build_dependency_graph()

    assert isinstance(graph, dict)
    assert len(graph) >= 2  # main.py + utils.py


def test_get_impacted_files_empty(temp_repo):
    """Test récupération fichiers impactés (cas vide)."""
    analyzer = ImpactAnalyzer(temp_repo)
    impacted = analyzer.get_impacted_files(temp_repo / "utils.py")

    assert isinstance(impacted, set)
