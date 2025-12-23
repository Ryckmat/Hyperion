"""
Tests unitaires pour CodeIndexer.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from pathlib import Path

import pytest

from hyperion.modules.understanding.indexer import CodeIndexer


@pytest.fixture
def sample_file(tmp_path):
    """Crée un fichier Python d'exemple."""
    file_path = tmp_path / "sample.py"
    file_path.write_text(
        '''"""Module docstring."""

def example_function(arg1: str) -> str:
    """Function docstring."""
    # Inline comment
    return arg1.upper()

class ExampleClass:
    """Class docstring."""

    def method(self):
        pass
'''
    )
    return file_path


def test_indexer_initialization(tmp_path):
    """Test initialisation de l'indexeur."""
    indexer = CodeIndexer(tmp_path)
    assert indexer.repo_path == tmp_path
    assert isinstance(indexer.index, dict)


def test_index_file(sample_file):
    """Test indexation d'un fichier."""
    indexer = CodeIndexer(sample_file.parent)
    metadata = indexer.index_file(sample_file)

    assert "path" in metadata
    assert "docstrings" in metadata
    assert "functions" in metadata
    assert "classes" in metadata
    assert "comments" in metadata


def test_extract_docstrings(sample_file):
    """Test extraction des docstrings."""
    indexer = CodeIndexer(sample_file.parent)
    metadata = indexer.index_file(sample_file)

    docstrings = metadata["docstrings"]
    assert "module" in docstrings
    assert "example_function" in docstrings
    assert "ExampleClass" in docstrings


def test_extract_function_signatures(sample_file):
    """Test extraction des signatures de fonctions."""
    indexer = CodeIndexer(sample_file.parent)
    metadata = indexer.index_file(sample_file)

    functions = metadata["functions"]
    assert len(functions) >= 1
    assert any(f["name"] == "example_function" for f in functions)


def test_extract_comments(sample_file):
    """Test extraction des commentaires."""
    indexer = CodeIndexer(sample_file.parent)
    metadata = indexer.index_file(sample_file)

    comments = metadata["comments"]
    assert len(comments) >= 1
    assert any("Inline comment" in c for c in comments)
