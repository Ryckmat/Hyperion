"""
Tests unitaires pour CodeMetrics.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import pytest

from hyperion.modules.anomaly.metrics import CodeMetrics


@pytest.fixture
def sample_file(tmp_path):
    """Crée un fichier Python d'exemple."""
    file_path = tmp_path / "metrics_test.py"
    content = '''
def function1():
    """Docstring."""
    # Comment
    return True

class MyClass:
    def method(self):
        if True:
            pass
'''
    file_path.write_text(content)
    return file_path


def test_metrics_initialization():
    """Test initialisation du calculateur."""
    metrics = CodeMetrics()
    assert metrics is not None


def test_calculate_metrics(sample_file):
    """Test calcul de métriques."""
    metrics = CodeMetrics()
    result = metrics.calculate_metrics(sample_file)

    assert "file" in result
    assert "lines_of_code" in result
    assert "cyclomatic_complexity" in result
    assert "maintainability_index" in result
    assert "comment_ratio" in result
    assert "function_count" in result
    assert "class_count" in result


def test_count_loc(sample_file):
    """Test comptage lignes de code."""
    metrics = CodeMetrics()
    with open(sample_file) as f:
        content = f.read()

    loc = metrics._count_loc(content)
    assert loc > 0


def test_calculate_comment_ratio(sample_file):
    """Test calcul du ratio de commentaires."""
    metrics = CodeMetrics()
    with open(sample_file) as f:
        content = f.read()

    ratio = metrics._calculate_comment_ratio(content)
    assert isinstance(ratio, float)
    assert 0.0 <= ratio <= 1.0
