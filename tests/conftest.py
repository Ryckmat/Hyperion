"""Configuration pytest."""
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Racine du projet Hyperion."""
    return Path(__file__).parent.parent

@pytest.fixture
def sample_profile_yaml(project_root):
    """Fichier profile.yaml de test (requests)."""
    profile = project_root / "data" / "repositories" / "requests" / "profile.yaml"
    if profile.exists():
        return profile
    pytest.skip("Fichier profile.yaml non disponible")

@pytest.fixture
def templates_dir(project_root):
    """Répertoire templates."""
    return project_root / "templates"
