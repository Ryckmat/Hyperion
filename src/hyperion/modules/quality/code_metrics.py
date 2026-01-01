"""
Analyseur de métriques de qualité de code avec radon et pylint.

Module pour analyser la qualité du code Python avec différents outils.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hyperion.modules.monitoring.logging.json_logger import get_logger

logger = get_logger("hyperion.quality.code_metrics")


@dataclass
class ComplexityResult:
    """Résultat d'analyse de complexité."""

    name: str
    type: str  # function, method, class
    lineno: int
    complexity: int
    rank: str  # A, B, C, D, E, F
    file_path: str


@dataclass
class MaintainabilityResult:
    """Résultat d'analyse de maintenabilité."""

    file_path: str
    maintainability_index: float
    rank: str  # A, B, C, D, E, F


@dataclass
class PylintResult:
    """Résultat d'analyse Pylint."""

    type: str  # convention, refactor, warning, error, fatal
    module: str
    obj: str
    line: int
    column: int
    path: str
    symbol: str
    message: str
    message_id: str


@dataclass
class CodeQualityReport:
    """Rapport complet de qualité de code."""

    file_path: str
    complexity_results: list[ComplexityResult] = field(default_factory=list)
    maintainability_result: MaintainabilityResult | None = None
    pylint_results: list[PylintResult] = field(default_factory=list)
    raw_metrics: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    issues_count: dict[str, int] = field(default_factory=dict)


class CodeMetricsAnalyzer:
    """
    Analyseur de qualité du code avec outils multiples.

    Fonctionnalités :
    - Complexité cyclomatique (radon)
    - Index de maintenabilité (radon)
    - Analyse statique (pylint)
    - Métriques de code (radon)
    - Score de qualité global
    - Rapports détaillés
    """

    def __init__(self):
        self.logger = get_logger("hyperion.quality.code_metrics")
        self._check_tools_availability()

    def _check_tools_availability(self) -> None:
        """Vérifie la disponibilité des outils."""
        self.radon_available = self._check_tool("radon")
        self.pylint_available = self._check_tool("pylint")

        self.logger.info(
            "Outils qualité disponibles", radon=self.radon_available, pylint=self.pylint_available
        )

    def _check_tool(self, tool: str) -> bool:
        """Vérifie si un outil est disponible."""
        try:
            result = subprocess.run([tool, "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def analyze_file(self, file_path: str | Path) -> CodeQualityReport:
        """
        Analyse complète d'un fichier Python.

        Args:
            file_path: Chemin vers le fichier à analyser

        Returns:
            Rapport de qualité complet
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.error(f"Fichier non trouvé : {file_path}")
            return CodeQualityReport(file_path=str(file_path))

        self.logger.info(f"Analyse qualité : {file_path}")

        report = CodeQualityReport(file_path=str(file_path))

        # Analyse radon
        if self.radon_available:
            try:
                report.complexity_results = self._analyze_complexity(file_path)
                report.maintainability_result = self._analyze_maintainability(file_path)
                report.raw_metrics = self._get_raw_metrics(file_path)
            except Exception as e:
                self.logger.error(f"Erreur radon pour {file_path} : {e}")

        # Analyse pylint
        if self.pylint_available:
            try:
                report.pylint_results = self._analyze_pylint(file_path)
            except Exception as e:
                self.logger.error(f"Erreur pylint pour {file_path} : {e}")

        # Calcul du score de qualité
        report.quality_score = self._calculate_quality_score(report)
        report.issues_count = self._count_issues(report)

        return report

    def analyze_directory(
        self, directory: str | Path, recursive: bool = True
    ) -> dict[str, CodeQualityReport]:
        """
        Analyse tous les fichiers Python d'un répertoire.

        Args:
            directory: Répertoire à analyser
            recursive: Analyse récursive

        Returns:
            Rapports de qualité par fichier
        """
        directory = Path(directory)
        reports = {}

        if not directory.exists():
            self.logger.error(f"Répertoire non trouvé : {directory}")
            return reports

        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory.glob(pattern))

        self.logger.info(f"Analyse qualité répertoire {directory}", files_found=len(python_files))

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            try:
                report = self.analyze_file(file_path)
                relative_path = str(file_path.relative_to(directory))
                reports[relative_path] = report
            except Exception as e:
                self.logger.error(f"Erreur analyse {file_path} : {e}")

        return reports

    def _analyze_complexity(self, file_path: Path) -> list[ComplexityResult]:
        """Analyse la complexité cyclomatique avec radon."""
        results = []

        try:
            # Radon complexité cyclomatique
            cmd = ["radon", "cc", str(file_path), "-j"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                data = json.loads(result.stdout)

                for file_data in data.values():
                    for item in file_data:
                        results.append(
                            ComplexityResult(
                                name=item["name"],
                                type=item["type"],
                                lineno=item["lineno"],
                                complexity=item["complexity"],
                                rank=item["rank"],
                                file_path=str(file_path),
                            )
                        )

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.logger.warning(f"Erreur analyse complexité {file_path} : {e}")

        return results

    def _analyze_maintainability(self, file_path: Path) -> MaintainabilityResult | None:
        """Analyse l'index de maintenabilité avec radon."""
        try:
            # Radon maintenabilité
            cmd = ["radon", "mi", str(file_path), "-j"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                data = json.loads(result.stdout)

                for _file_key, file_data in data.items():
                    if file_data:
                        return MaintainabilityResult(
                            file_path=str(file_path),
                            maintainability_index=file_data["mi"],
                            rank=file_data["rank"],
                        )

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.logger.warning(f"Erreur analyse maintenabilité {file_path} : {e}")

        return None

    def _get_raw_metrics(self, file_path: Path) -> dict[str, Any]:
        """Obtient les métriques brutes avec radon."""
        metrics = {}

        try:
            # Métriques Halstead
            cmd = ["radon", "hal", str(file_path), "-j"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                data = json.loads(result.stdout)
                for _file_key, file_data in data.items():
                    if file_data:
                        metrics["halstead"] = file_data

        except Exception as e:
            self.logger.debug(f"Erreur métriques Halstead {file_path} : {e}")

        try:
            # Métriques brutes (LOC, LLOC, etc.)
            cmd = ["radon", "raw", str(file_path), "-j"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                data = json.loads(result.stdout)
                for _file_key, file_data in data.items():
                    metrics["raw"] = file_data

        except Exception as e:
            self.logger.debug(f"Erreur métriques brutes {file_path} : {e}")

        return metrics

    def _analyze_pylint(self, file_path: Path) -> list[PylintResult]:
        """Analyse avec pylint."""
        results = []

        try:
            # Configuration pylint minimale pour éviter les erreurs
            pylint_config = [
                "--disable=import-error,no-member,missing-module-docstring",
                "--output-format=json",
                "--reports=no",
                "--score=no",
            ]

            cmd = ["pylint"] + pylint_config + [str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Pylint retourne code 0 si pas d'erreur, mais on veut quand même les warnings
            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)

                    for item in data:
                        results.append(
                            PylintResult(
                                type=item.get("type", "unknown"),
                                module=item.get("module", ""),
                                obj=item.get("obj", ""),
                                line=item.get("line", 0),
                                column=item.get("column", 0),
                                path=item.get("path", str(file_path)),
                                symbol=item.get("symbol", ""),
                                message=item.get("message", ""),
                                message_id=item.get("message-id", ""),
                            )
                        )

                except json.JSONDecodeError as e:
                    self.logger.warning(f"Erreur parsing JSON pylint {file_path} : {e}")

        except Exception as e:
            self.logger.warning(f"Erreur pylint {file_path} : {e}")

        return results

    def _calculate_quality_score(self, report: CodeQualityReport) -> float:
        """
        Calcule un score de qualité global (0-100).

        Pondération :
        - Complexité : 30%
        - Maintenabilité : 25%
        - Issues pylint : 25%
        - Couverture métriques : 20%
        """
        score = 0.0
        weight_total = 0.0

        # Score complexité (30%)
        if report.complexity_results:
            complexity_score = self._score_complexity(report.complexity_results)
            score += complexity_score * 0.30
            weight_total += 0.30

        # Score maintenabilité (25%)
        if report.maintainability_result:
            maintainability_score = self._score_maintainability(report.maintainability_result)
            score += maintainability_score * 0.25
            weight_total += 0.25

        # Score pylint (25%)
        if report.pylint_results is not None:  # Peut être une liste vide
            pylint_score = self._score_pylint(report.pylint_results)
            score += pylint_score * 0.25
            weight_total += 0.25

        # Score métriques (20%)
        if report.raw_metrics:
            metrics_score = self._score_metrics(report.raw_metrics)
            score += metrics_score * 0.20
            weight_total += 0.20

        # Normaliser par le poids total
        return score / weight_total if weight_total > 0 else 0.0

    def _score_complexity(self, complexity_results: list[ComplexityResult]) -> float:
        """Score basé sur la complexité cyclomatique."""
        if not complexity_results:
            return 100.0

        # Convertir les ranks en scores
        rank_scores = {"A": 100, "B": 80, "C": 60, "D": 40, "E": 20, "F": 0}

        total_score = sum(rank_scores.get(result.rank, 0) for result in complexity_results)
        avg_score = total_score / len(complexity_results)

        return avg_score

    def _score_maintainability(self, maintainability_result: MaintainabilityResult) -> float:
        """Score basé sur l'index de maintenabilité."""
        # Index de maintenabilité est sur une échelle 0-100
        return max(0, min(100, maintainability_result.maintainability_index))

    def _score_pylint(self, pylint_results: list[PylintResult]) -> float:
        """Score basé sur les issues pylint."""
        if not pylint_results:
            return 100.0  # Pas d'issues = score parfait

        # Pondération par type d'issue
        weights = {"error": 10, "warning": 5, "refactor": 3, "convention": 1, "fatal": 15}

        total_penalty = sum(weights.get(issue.type, 1) for issue in pylint_results)

        # Score = 100 - pénalités (minimum 0)
        score = max(0, 100 - total_penalty)

        return score

    def _score_metrics(self, raw_metrics: dict[str, Any]) -> float:
        """Score basé sur les métriques brutes."""
        score = 50.0  # Score de base

        # Bonus pour métriques disponibles
        if "raw" in raw_metrics:
            raw = raw_metrics["raw"]

            # LOC ratio (logical vs physical)
            if "loc" in raw and "lloc" in raw and raw["loc"] > 0:
                ratio = raw["lloc"] / raw["loc"]
                if 0.6 <= ratio <= 0.8:  # Ratio optimal
                    score += 10

            # Commentaires ratio
            if "comments" in raw and "loc" in raw and raw["loc"] > 0:
                comment_ratio = raw["comments"] / raw["loc"]
                if comment_ratio >= 0.1:  # Au moins 10% de commentaires
                    score += 15

        if "halstead" in raw_metrics:
            # Métriques Halstead disponibles
            score += 10

        return min(100, score)

    def _count_issues(self, report: CodeQualityReport) -> dict[str, int]:
        """Compte les issues par type."""
        issues = {
            "total": 0,
            "error": 0,
            "warning": 0,
            "refactor": 0,
            "convention": 0,
            "fatal": 0,
            "high_complexity": 0,
        }

        # Issues pylint
        for pylint_result in report.pylint_results:
            issues["total"] += 1
            issue_type = pylint_result.type
            if issue_type in issues:
                issues[issue_type] += 1

        # Complexité élevée (rang D, E, F)
        for complexity_result in report.complexity_results:
            if complexity_result.rank in ["D", "E", "F"]:
                issues["high_complexity"] += 1
                issues["total"] += 1

        return issues

    def generate_summary_report(self, reports: dict[str, CodeQualityReport]) -> dict[str, Any]:
        """
        Génère un rapport de synthèse pour plusieurs fichiers.

        Args:
            reports: Rapports par fichier

        Returns:
            Rapport de synthèse
        """
        if not reports:
            return {}

        summary = {
            "files_analyzed": len(reports),
            "average_quality_score": 0.0,
            "total_issues": 0,
            "issues_by_type": {},
            "top_issues": [],
            "quality_distribution": {},
            "recommendations": [],
        }

        # Calcul des moyennes
        quality_scores = [r.quality_score for r in reports.values()]
        summary["average_quality_score"] = sum(quality_scores) / len(quality_scores)

        # Aggregation des issues
        all_issues = {}
        for report in reports.values():
            for issue_type, count in report.issues_count.items():
                all_issues[issue_type] = all_issues.get(issue_type, 0) + count

        summary["total_issues"] = all_issues.get("total", 0)
        summary["issues_by_type"] = all_issues

        # Distribution qualité
        quality_ranges = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for score in quality_scores:
            if score >= 90:
                quality_ranges["excellent"] += 1
            elif score >= 75:
                quality_ranges["good"] += 1
            elif score >= 50:
                quality_ranges["fair"] += 1
            else:
                quality_ranges["poor"] += 1

        summary["quality_distribution"] = quality_ranges

        # Recommandations
        recommendations = []
        if all_issues.get("high_complexity", 0) > 0:
            recommendations.append("Réduire la complexité cyclomatique des fonctions critiques")
        if all_issues.get("error", 0) > 0:
            recommendations.append("Corriger les erreurs critiques détectées par pylint")
        if summary["average_quality_score"] < 60:
            recommendations.append("Améliorer la qualité générale du code")

        summary["recommendations"] = recommendations

        return summary

    def export_report(
        self,
        reports: dict[str, CodeQualityReport],
        output_path: str | Path,
        format_type: str = "json",
    ) -> None:
        """
        Exporte les rapports dans différents formats.

        Args:
            reports: Rapports à exporter
            output_path: Chemin de sortie
            format_type: Format (json, html, markdown)
        """
        output_path = Path(output_path)

        if format_type == "json":
            self._export_json(reports, output_path)
        elif format_type == "html":
            self._export_html(reports, output_path)
        elif format_type == "markdown":
            self._export_markdown(reports, output_path)
        else:
            raise ValueError(f"Format non supporté : {format_type}")

        self.logger.info(f"Rapport exporté : {output_path}")

    def _export_json(self, reports: dict[str, CodeQualityReport], output_path: Path) -> None:
        """Exporte en JSON."""
        data = {"summary": self.generate_summary_report(reports), "files": {}}

        for file_path, report in reports.items():
            data["files"][file_path] = {
                "quality_score": report.quality_score,
                "issues_count": report.issues_count,
                "maintainability_index": (
                    report.maintainability_result.maintainability_index
                    if report.maintainability_result
                    else None
                ),
                "complexity_results": [
                    {"name": c.name, "complexity": c.complexity, "rank": c.rank, "lineno": c.lineno}
                    for c in report.complexity_results
                ],
                "pylint_issues": len(report.pylint_results),
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_html(self, reports: dict[str, CodeQualityReport], output_path: Path) -> None:
        """Exporte en HTML."""
        summary = self.generate_summary_report(reports)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Rapport Qualité Code - Hyperion</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .file {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; }}
        .score {{ font-weight: bold; font-size: 1.2em; }}
        .good {{ color: green; }}
        .fair {{ color: orange; }}
        .poor {{ color: red; }}
    </style>
</head>
<body>
    <h1>Rapport Qualité Code</h1>

    <div class="summary">
        <h2>Résumé</h2>
        <p>Fichiers analysés : {summary['files_analyzed']}</p>
        <p>Score moyen : <span class="score">{summary['average_quality_score']:.1f}</span></p>
        <p>Issues totales : {summary['total_issues']}</p>
    </div>

    <h2>Détail par fichier</h2>
"""

        for file_path, report in reports.items():
            score_class = (
                "good"
                if report.quality_score >= 75
                else "fair" if report.quality_score >= 50 else "poor"
            )
            html_content += f"""
    <div class="file">
        <h3>{file_path}</h3>
        <p>Score : <span class="score {score_class}">{report.quality_score:.1f}</span></p>
        <p>Issues : {report.issues_count.get('total', 0)}</p>
    </div>
"""

        html_content += """
</body>
</html>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _export_markdown(self, reports: dict[str, CodeQualityReport], output_path: Path) -> None:
        """Exporte en Markdown."""
        summary = self.generate_summary_report(reports)

        md_content = f"""# Rapport Qualité Code - Hyperion

## Résumé

- **Fichiers analysés** : {summary['files_analyzed']}
- **Score moyen** : {summary['average_quality_score']:.1f}/100
- **Issues totales** : {summary['total_issues']}

## Distribution qualité

| Niveau | Fichiers |
|--------|----------|
| Excellent (90+) | {summary['quality_distribution']['excellent']} |
| Bon (75-89) | {summary['quality_distribution']['good']} |
| Moyen (50-74) | {summary['quality_distribution']['fair']} |
| Faible (<50) | {summary['quality_distribution']['poor']} |

## Détail par fichier

| Fichier | Score | Issues | Status |
|---------|-------|--------|--------|
"""

        for file_path, report in reports.items():
            status = (
                "✅" if report.quality_score >= 75 else "⚠️" if report.quality_score >= 50 else "❌"
            )
            md_content += f"| {file_path} | {report.quality_score:.1f} | {report.issues_count.get('total', 0)} | {status} |\n"

        if summary["recommendations"]:
            md_content += "\n## Recommandations\n\n"
            for rec in summary["recommendations"]:
                md_content += f"- {rec}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
