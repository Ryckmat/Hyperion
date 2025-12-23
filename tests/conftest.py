"""Configuration pytest pour Hyperion v2.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_repo_root():
    """Racine du repository de test."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def project_root():
    """Racine du projet Hyperion."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_repo(tmp_path):
    """
    Créé un repository d'exemple pour tests.
    
    Structure:
        main.py
        utils.py
        api/
            __init__.py
            endpoints.py
        core/
            __init__.py
            business.py
    """
    repo_path = tmp_path / "sample_repo"
    repo_path.mkdir()
    
    # Fichier principal
    (repo_path / "main.py").write_text("""
from utils import helper
from api.endpoints import get_data

def main():
    data = get_data()
    result = helper(data)
    return result
""")
    
    # Utils
    (repo_path / "utils.py").write_text("""
def helper(data):
    \"\"\"Process data.\"\"\"
    return data.upper()
""")
    
    # API
    api_dir = repo_path / "api"
    api_dir.mkdir()
    (api_dir / "__init__.py").write_text("")
    (api_dir / "endpoints.py").write_text("""
from core.business import process

def get_data():
    \"\"\"Get data from source.\"\"\"
    return process("raw_data")
""")
    
    # Core
    core_dir = repo_path / "core"
    core_dir.mkdir()
    (core_dir / "__init__.py").write_text("")
    (core_dir / "business.py").write_text("""
def process(data):
    \"\"\"Business logic.\"\"\"
    return data.strip().lower()
""")
    
    return repo_path


@pytest.fixture
def large_repo(tmp_path):
    """
    Créé un gros repository pour tests de performance.
    
    100 fichiers avec dépendances croisées.
    """
    repo_path = tmp_path / "large_repo"
    repo_path.mkdir()
    
    # Créer 100 fichiers
    for i in range(100):
        module_dir = repo_path / f"module_{i:03d}"
        module_dir.mkdir()
        
        (module_dir / "__init__.py").write_text("")
        
        # Fichier avec imports de 3 autres modules
        imports = "\n".join([
            f"from module_{(i-1) % 100:03d}.logic import func_{(i-1) % 100}"
            for _ in range(3)
        ])
        
        (module_dir / "logic.py").write_text(f"""
{imports}

def func_{i}():
    \"\"\"Function {i}.\"\"\"
    return {i}
""")
    
    return repo_path


@pytest.fixture(scope="session")
def qdrant_test_client():
    """Client Qdrant pour tests (optionnel)."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6334)
        # Vérifier disponibilité
        client.get_collections()
        return client
    except Exception:
        pytest.skip("Qdrant test non disponible")


@pytest.fixture(scope="session")
def neo4j_test_driver():
    """Driver Neo4j pour tests (optionnel)."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            "bolt://localhost:7688",
            auth=("neo4j", "testpassword")
        )
        # Vérifier disponibilité
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except Exception:
        pytest.skip("Neo4j test non disponible")


# Markers personnalisés
def pytest_configure(config):
    """Configuration markers pytest."""
    config.addinivalue_line("markers", "unit: Tests unitaires")
    config.addinivalue_line("markers", "integration: Tests intégration")
    config.addinivalue_line("markers", "e2e: Tests end-to-end")
    config.addinivalue_line("markers", "slow: Tests lents (> 5s)")
    config.addinivalue_line("markers", "benchmark: Benchmarks performance")
