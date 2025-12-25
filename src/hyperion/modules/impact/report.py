"""
Génération de rapports d'impact.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ImpactReportData:
    """Données structurées d'un rapport d'impact."""

    file_path: str
    timestamp: str
    risk_level: str
    risk_score: float
    impacted_files: list[str]
    dependencies: list[str]
    recommendations: list[str]


class ImpactReport:
    """
    Génère des rapports d'impact en JSON/HTML.

    Formats supportés: JSON, HTML, Markdown.
    """

    def __init__(self):
        """Initialise le générateur de rapports."""
        self.reports: list[ImpactReportData] = []

    def create_report(
        self,
        file_path: str,
        risk_level: str,
        risk_score: float,
        impacted_files: list[str],
        dependencies: list[str],
    ) -> ImpactReportData:
        """
        Crée un rapport d'impact.

        Args:
            file_path: Fichier modifié
            risk_level: Niveau de risque (low/medium/high/critical)
            risk_score: Score numérique [0, 1]
            impacted_files: Fichiers impactés
            dependencies: Dépendances directes

        Returns:
            Rapport structuré
        """
        recommendations = self._generate_recommendations(risk_level, len(impacted_files))

        report = ImpactReportData(
            file_path=file_path,
            timestamp=datetime.now().isoformat(),
            risk_level=risk_level,
            risk_score=risk_score,
            impacted_files=impacted_files,
            dependencies=dependencies,
            recommendations=recommendations,
        )

        self.reports.append(report)
        return report

    def _generate_recommendations(self, risk_level: str, num_impacted: int) -> list[str]:
        """Génère des recommandations basées sur le risque."""
        recommendations = []

        if risk_level == "critical":
            recommendations.append("⚠️ CRITIQUE: Review approfondie requise")
            recommendations.append("✅ Tests E2E obligatoires avant merge")
            recommendations.append("👥 Review par 2+ développeurs seniors")

        elif risk_level == "high":
            recommendations.append("⚠️ ÉLEVÉ: Tests unitaires + intégration requis")
            recommendations.append("📋 Documentation des changements")

        elif risk_level == "medium":
            recommendations.append("✅ Tests unitaires recommandés")
            recommendations.append("📝 Update documentation si API change")

        else:  # low
            recommendations.append("✅ Change safe, tests de base suffisants")

        if num_impacted > 10:
            recommendations.append(f"📊 {num_impacted} fichiers impactés - coordination nécessaire")

        return recommendations

    def to_json(self, report: ImpactReportData) -> str:
        """
        Exporte le rapport en JSON.

        Args:
            report: Rapport à exporter

        Returns:
            JSON string
        """
        return json.dumps(asdict(report), indent=2, ensure_ascii=False)

    def to_markdown(self, report: ImpactReportData) -> str:
        """
        Exporte le rapport en Markdown.

        Args:
            report: Rapport à exporter

        Returns:
            Markdown string
        """
        md = f"""# 📊 Impact Analysis Report

**File**: `{report.file_path}`
**Timestamp**: {report.timestamp}
**Risk Level**: {report.risk_level.upper()} ({report.risk_score:.2f})

## 🎯 Impact Scope

- **Impacted Files**: {len(report.impacted_files)}
- **Direct Dependencies**: {len(report.dependencies)}

## 📁 Impacted Files

"""
        for f in report.impacted_files[:10]:  # Top 10
            md += f"- `{f}`\n"

        if len(report.impacted_files) > 10:
            md += f"\n... and {len(report.impacted_files) - 10} more\n"

        md += "\n## 💡 Recommendations\n\n"
        for rec in report.recommendations:
            md += f"- {rec}\n"

        return md

    def save_report(self, report: ImpactReportData, output_path: Path, format: str = "json"):
        """
        Sauvegarde le rapport sur disque.

        Args:
            report: Rapport à sauvegarder
            output_path: Chemin de sortie
            format: Format (json/markdown)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            content = self.to_json(report)
            suffix = ".json"
        elif format == "markdown":
            content = self.to_markdown(report)
            suffix = ".md"
        else:
            raise ValueError(f"Format non supporté: {format}")

        output_file = output_path.with_suffix(suffix)
        output_file.write_text(content, encoding="utf-8")
