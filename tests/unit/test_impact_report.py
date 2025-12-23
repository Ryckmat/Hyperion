"""
Tests unitaires pour ImpactReport.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import json

import pytest

from hyperion.modules.impact.report import ImpactReport, ImpactReportData


def test_report_initialization():
    """Test initialisation du générateur de rapports."""
    report_gen = ImpactReport()
    assert isinstance(report_gen.reports, list)
    assert len(report_gen.reports) == 0


def test_create_report():
    """Test création d'un rapport."""
    report_gen = ImpactReport()
    report = report_gen.create_report(
        file_path="test.py",
        risk_level="high",
        risk_score=0.8,
        impacted_files=["dep1.py", "dep2.py"],
        dependencies=["util.py"],
    )

    assert isinstance(report, ImpactReportData)
    assert report.file_path == "test.py"
    assert report.risk_level == "high"
    assert report.risk_score == 0.8
    assert len(report.impacted_files) == 2
    assert len(report.recommendations) > 0


def test_to_json():
    """Test export JSON."""
    report_gen = ImpactReport()
    report = report_gen.create_report(
        file_path="test.py", risk_level="low", risk_score=0.2, impacted_files=[], dependencies=[]
    )

    json_output = report_gen.to_json(report)
    parsed = json.loads(json_output)

    assert parsed["file_path"] == "test.py"
    assert parsed["risk_level"] == "low"


def test_to_markdown():
    """Test export Markdown."""
    report_gen = ImpactReport()
    report = report_gen.create_report(
        file_path="test.py", risk_level="medium", risk_score=0.5, impacted_files=["dep.py"], dependencies=[]
    )

    markdown = report_gen.to_markdown(report)

    assert "# 📊 Impact Analysis Report" in markdown
    assert "test.py" in markdown
    assert "medium" in markdown.lower()


def test_generate_recommendations_critical():
    """Test génération recommandations niveau critique."""
    report_gen = ImpactReport()
    recs = report_gen._generate_recommendations("critical", 25)

    assert len(recs) > 0
    assert any("CRITIQUE" in r for r in recs)


def test_save_report(tmp_path):
    """Test sauvegarde rapport sur disque."""
    report_gen = ImpactReport()
    report = report_gen.create_report(
        file_path="test.py", risk_level="low", risk_score=0.1, impacted_files=[], dependencies=[]
    )

    output_path = tmp_path / "report"
    report_gen.save_report(report, output_path, format="json")

    assert (tmp_path / "report.json").exists()
