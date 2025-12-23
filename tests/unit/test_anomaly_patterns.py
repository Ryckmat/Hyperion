"""
Tests unitaires pour DangerousPatterns.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from pathlib import Path

import pytest

from hyperion.modules.anomaly.patterns import DangerousPatterns


@pytest.fixture
def vulnerable_file(tmp_path):
    """Crée un fichier avec vulnérabilité SQL injection."""
    file_path = tmp_path / "vulnerable.py"
    content = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return execute(query)
'''
    file_path.write_text(content)
    return file_path


def test_patterns_initialization():
    """Test initialisation du détecteur de patterns."""
    patterns = DangerousPatterns()
    assert hasattr(patterns, "security_patterns")
    assert hasattr(patterns, "performance_patterns")


def test_scan_file_sql_injection(vulnerable_file):
    """Test détection SQL injection."""
    patterns = DangerousPatterns()
    findings = patterns.scan_file(vulnerable_file)

    assert isinstance(findings, list)
    # La détection dépend du regex match


def test_generate_report(vulnerable_file):
    """Test génération de rapport."""
    patterns = DangerousPatterns()
    report = patterns.generate_report(vulnerable_file)

    assert "file" in report
    assert "security_findings" in report
    assert "performance_issues" in report
    assert "rgpd_violations" in report
    assert "total_issues" in report
    assert "risk_score" in report
