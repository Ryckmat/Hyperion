"""
Tests d'intégration pour le workflow impact complet.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import pytest

from hyperion.modules.impact.analyzer import ImpactAnalyzer
from hyperion.modules.impact.predictor import RiskPredictor
from hyperion.modules.impact.report import ImpactReport


@pytest.fixture
def sample_repo(tmp_path):
    """Crée un repository d'exemple pour tests."""
    repo_path = tmp_path / "sample_repo"
    repo_path.mkdir()

    # Fichier principal
    (repo_path / "main.py").write_text(
        """
from utils import helper
from config import settings

def main():
    result = helper()
    print(settings.DEBUG)
"""
    )

    # Utilitaires
    (repo_path / "utils.py").write_text(
        """
def helper():
    return "helper result"
"""
    )

    # Configuration
    (repo_path / "config.py").write_text(
        """
class Settings:
    DEBUG = True

settings = Settings()
"""
    )

    return repo_path


def test_impact_analysis_workflow(sample_repo):
    """Test workflow complet d'analyse d'impact."""
    # 1. Analyse du code
    analyzer = ImpactAnalyzer(sample_repo)
    dependency_graph = analyzer.build_dependency_graph()

    assert len(dependency_graph) >= 3

    # 2. Prédiction risque
    predictor = RiskPredictor()
    modified_file = str(sample_repo / "utils.py")
    risk_level = predictor.predict_risk(modified_file, dependency_graph)
    risk_score = predictor.get_risk_score(modified_file, dependency_graph)

    assert risk_level is not None
    assert 0.0 <= risk_score <= 1.0

    # 3. Génération rapport
    report_gen = ImpactReport()
    impacted_files = list(dependency_graph.get(modified_file, set()))
    dependencies = list(dependency_graph.get(modified_file, set()))

    report = report_gen.create_report(
        file_path=modified_file,
        risk_level=risk_level.value,
        risk_score=risk_score,
        impacted_files=impacted_files,
        dependencies=dependencies,
    )

    assert report.file_path == modified_file
    assert len(report.recommendations) > 0

    # 4. Export rapport
    json_output = report_gen.to_json(report)
    markdown_output = report_gen.to_markdown(report)

    assert modified_file in json_output
    assert modified_file in markdown_output


def test_impact_report_persistence(sample_repo, tmp_path):
    """Test sauvegarde du rapport."""
    analyzer = ImpactAnalyzer(sample_repo)
    dependency_graph = analyzer.build_dependency_graph()

    predictor = RiskPredictor()
    modified_file = str(sample_repo / "config.py")
    risk_level = predictor.predict_risk(modified_file, dependency_graph)
    risk_score = predictor.get_risk_score(modified_file, dependency_graph)

    report_gen = ImpactReport()
    report = report_gen.create_report(
        file_path=modified_file,
        risk_level=risk_level.value,
        risk_score=risk_score,
        impacted_files=[],
        dependencies=[],
    )

    output_path = tmp_path / "reports" / "impact_report"
    report_gen.save_report(report, output_path, format="json")

    assert (tmp_path / "reports" / "impact_report.json").exists()
