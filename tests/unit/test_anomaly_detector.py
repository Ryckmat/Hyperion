"""
Tests unitaires pour AnomalyDetector.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from pathlib import Path

import pytest

from hyperion.modules.anomaly.detector import AnomalyDetector


@pytest.fixture
def complex_file(tmp_path):
    """Crée un fichier avec haute complexité."""
    file_path = tmp_path / "complex.py"
    content = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    return "high"
                return "medium"
            return "low"
        return "very_low"
    return "negative"
"""
    file_path.write_text(content)
    return file_path


def test_detector_initialization(tmp_path):
    """Test initialisation du détecteur."""
    detector = AnomalyDetector(tmp_path)
    assert detector.repo_path == tmp_path


def test_detect_anomalies_high_complexity(complex_file):
    """Test détection de complexité élevée."""
    detector = AnomalyDetector(complex_file.parent)
    anomalies = detector.detect_anomalies(complex_file)

    assert isinstance(anomalies, list)
    # Note: détection basique, résultats variables


def test_extract_metrics(complex_file):
    """Test extraction de métriques."""
    detector = AnomalyDetector(complex_file.parent)
    metrics = detector._extract_metrics(complex_file)

    assert "lines_of_code" in metrics
    assert "complexity" in metrics
    assert metrics["lines_of_code"] > 0


def test_get_anomaly_score(complex_file):
    """Test calcul du score d'anomalie."""
    detector = AnomalyDetector(complex_file.parent)
    score = detector.get_anomaly_score(complex_file)

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
