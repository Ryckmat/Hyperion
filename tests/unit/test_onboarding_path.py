"""
Tests unitaires pour LearningPathGenerator.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from hyperion.modules.onboarding.path_generator import LearningPathGenerator


def test_generator_initialization(tmp_path):
    """Test initialisation du générateur."""
    generator = LearningPathGenerator(tmp_path)
    assert generator.repo_path == tmp_path


def test_generate_path():
    """Test génération d'un parcours."""
    generator = LearningPathGenerator("/tmp/repo")
    path = generator.generate_path(target_role="backend", experience_level="junior")

    assert "role" in path
    assert "level" in path
    assert "duration_weeks" in path
    assert "steps" in path
    assert path["role"] == "backend"
    assert len(path["steps"]) > 0
