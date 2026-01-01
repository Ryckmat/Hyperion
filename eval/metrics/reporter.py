"""
Générateur de rapports d'évaluation pour Hyperion RAG.

Module pour analyser et présenter les résultats d'évaluation du système RAG.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TestResult:
    """Résultat d'un test individuel."""
    test_id: str
    question: str
    response: str
    latency_ms: float
    confidence_score: float
    hallucination_detected: bool
    sources_used: List[str]
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Rapport complet d'évaluation."""
    suite_name: str
    execution_time: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    avg_latency_ms: float
    avg_confidence: float
    hallucination_rate: float
    test_results: List[TestResult]
    summary_stats: Dict[str, Any] = field(default_factory=dict)


class EvaluationReporter:
    """
    Générateur de rapports d'évaluation RAG.

    Fonctionnalités :
    - Analyse statistique des résultats
    - Génération de rapports HTML/JSON/Markdown
    - Graphiques de performance
    - Comparaison entre exécutions
    - Détection de régressions
    """

    def __init__(self, output_dir: str = "eval/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_results(self, results: List[TestResult], suite_name: str) -> EvaluationReport:
        """
        Analyse les résultats de tests et génère un rapport.

        Args:
            results: Liste des résultats de tests
            suite_name: Nom de la suite de tests

        Returns:
            Rapport d'évaluation complet
        """
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests

        # Calculs statistiques
        latencies = [r.latency_ms for r in results if r.latency_ms is not None]
        confidences = [r.confidence_score for r in results if r.confidence_score is not None]
        hallucinations = sum(1 for r in results if r.hallucination_detected)

        avg_latency = statistics.mean(latencies) if latencies else 0
        avg_confidence = statistics.mean(confidences) if confidences else 0
        hallucination_rate = hallucinations / total_tests if total_tests > 0 else 0
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        # Statistiques détaillées
        summary_stats = self._calculate_detailed_stats(results)

        return EvaluationReport(
            suite_name=suite_name,
            execution_time=datetime.now().isoformat(),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            avg_latency_ms=avg_latency,
            avg_confidence=avg_confidence,
            hallucination_rate=hallucination_rate,
            test_results=results,
            summary_stats=summary_stats
        )

    def _calculate_detailed_stats(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calcule des statistiques détaillées."""
        latencies = [r.latency_ms for r in results if r.latency_ms is not None]
        confidences = [r.confidence_score for r in results if r.confidence_score is not None]

        stats = {}

        if latencies:
            stats["latency"] = {
                "min": min(latencies),
                "max": max(latencies),
                "median": statistics.median(latencies),
                "p95": self._percentile(latencies, 95),
                "p99": self._percentile(latencies, 99),
                "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0
            }

        if confidences:
            stats["confidence"] = {
                "min": min(confidences),
                "max": max(confidences),
                "median": statistics.median(confidences),
                "std_dev": statistics.stdev(confidences) if len(confidences) > 1 else 0
            }

        # Analyse par catégorie si disponible
        categories = {}
        for result in results:
            category = result.metadata.get("category", "unknown")
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}
            categories[category]["total"] += 1
            if result.success:
                categories[category]["passed"] += 1

        for category, data in categories.items():
            data["success_rate"] = data["passed"] / data["total"] if data["total"] > 0 else 0

        stats["by_category"] = categories

        return stats

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calcule un percentile."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_data) - 1)
        weight = index - lower_index
        return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight

    def generate_json_report(self, report: EvaluationReport) -> str:
        """Génère un rapport JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.suite_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        report_data = {
            "metadata": {
                "suite_name": report.suite_name,
                "execution_time": report.execution_time,
                "total_tests": report.total_tests,
                "passed_tests": report.passed_tests,
                "failed_tests": report.failed_tests,
                "success_rate": report.success_rate,
                "avg_latency_ms": report.avg_latency_ms,
                "avg_confidence": report.avg_confidence,
                "hallucination_rate": report.hallucination_rate,
            },
            "summary_stats": report.summary_stats,
            "results": [
                {
                    "test_id": r.test_id,
                    "question": r.question,
                    "response": r.response,
                    "latency_ms": r.latency_ms,
                    "confidence_score": r.confidence_score,
                    "hallucination_detected": r.hallucination_detected,
                    "sources_used": r.sources_used,
                    "success": r.success,
                    "error": r.error,
                    "metadata": r.metadata
                }
                for r in report.test_results
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def generate_markdown_report(self, report: EvaluationReport) -> str:
        """Génère un rapport Markdown."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.suite_name}_{timestamp}.md"
        filepath = self.output_dir / filename

        markdown = self._build_markdown_content(report)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return str(filepath)

    def _build_markdown_content(self, report: EvaluationReport) -> str:
        """Construit le contenu Markdown du rapport."""
        md = f"""# Rapport d'évaluation RAG - {report.suite_name}

**Date d'exécution :** {report.execution_time}

## 📊 Résumé

| Métrique | Valeur | Status |
|----------|--------|--------|
| **Tests totaux** | {report.total_tests} | - |
| **Tests réussis** | {report.passed_tests} | {'✅' if report.success_rate >= 0.8 else '⚠️' if report.success_rate >= 0.6 else '❌'} |
| **Taux de succès** | {report.success_rate:.1%} | {'✅' if report.success_rate >= 0.8 else '⚠️' if report.success_rate >= 0.6 else '❌'} |
| **Latence moyenne** | {report.avg_latency_ms:.0f}ms | {'✅' if report.avg_latency_ms <= 5000 else '⚠️' if report.avg_latency_ms <= 8000 else '❌'} |
| **Confiance moyenne** | {report.avg_confidence:.2f} | {'✅' if report.avg_confidence >= 0.7 else '⚠️' if report.avg_confidence >= 0.5 else '❌'} |
| **Taux d'hallucination** | {report.hallucination_rate:.1%} | {'✅' if report.hallucination_rate <= 0.1 else '⚠️' if report.hallucination_rate <= 0.2 else '❌'} |

## 📈 Statistiques détaillées

"""

        # Statistiques de latence
        if "latency" in report.summary_stats:
            latency_stats = report.summary_stats["latency"]
            md += f"""### Latence

| Percentile | Valeur |
|------------|--------|
| Minimum | {latency_stats['min']:.0f}ms |
| Médiane | {latency_stats['median']:.0f}ms |
| P95 | {latency_stats['p95']:.0f}ms |
| P99 | {latency_stats['p99']:.0f}ms |
| Maximum | {latency_stats['max']:.0f}ms |

"""

        # Analyse par catégorie
        if "by_category" in report.summary_stats:
            md += "### Résultats par catégorie\n\n"
            categories = report.summary_stats["by_category"]
            for category, stats in categories.items():
                success_icon = "✅" if stats["success_rate"] >= 0.8 else "⚠️" if stats["success_rate"] >= 0.6 else "❌"
                md += f"- **{category}** : {stats['passed']}/{stats['total']} ({stats['success_rate']:.1%}) {success_icon}\n"
            md += "\n"

        # Tests échoués
        failed_tests = [r for r in report.test_results if not r.success]
        if failed_tests:
            md += "## ❌ Tests échoués\n\n"
            for test in failed_tests:
                md += f"### {test.test_id}\n"
                md += f"**Question :** {test.question}\n\n"
                if test.error:
                    md += f"**Erreur :** {test.error}\n\n"
                if test.response:
                    md += f"**Réponse :** {test.response[:200]}{'...' if len(test.response) > 200 else ''}\n\n"
                md += f"**Confiance :** {test.confidence_score:.2f} | **Latence :** {test.latency_ms:.0f}ms\n\n"
                md += "---\n\n"

        # Tests les plus lents
        slow_tests = sorted(
            [r for r in report.test_results if r.latency_ms and r.latency_ms > 5000],
            key=lambda x: x.latency_ms,
            reverse=True
        )[:5]

        if slow_tests:
            md += "## 🐌 Tests les plus lents\n\n"
            for test in slow_tests:
                md += f"- **{test.test_id}** : {test.latency_ms:.0f}ms - {test.question[:60]}{'...' if len(test.question) > 60 else ''}\n"
            md += "\n"

        return md

    def generate_html_report(self, report: EvaluationReport) -> str:
        """Génère un rapport HTML avec graphiques."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.suite_name}_{timestamp}.html"
        filepath = self.output_dir / filename

        html_content = self._build_html_content(report)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(filepath)

    def _build_html_content(self, report: EvaluationReport) -> str:
        """Construit le contenu HTML avec graphiques."""
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport RAG - {report.suite_name}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        .metric.success {{ background-color: #e8f5e8; border-color: #4caf50; }}
        .metric.warning {{ background-color: #fff3e0; border-color: #ff9800; }}
        .metric.error {{ background-color: #ffebee; border-color: #f44336; }}
        .metric-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Rapport d'évaluation RAG</h1>
            <h2>{report.suite_name}</h2>
            <p>Exécuté le {report.execution_time}</p>
        </div>

        <div class="metrics">
            <div class="metric {'success' if report.success_rate >= 0.8 else 'warning' if report.success_rate >= 0.6 else 'error'}">
                <div>Taux de succès</div>
                <div class="metric-value">{report.success_rate:.1%}</div>
                <div>{report.passed_tests}/{report.total_tests} tests</div>
            </div>
            <div class="metric {'success' if report.avg_latency_ms <= 5000 else 'warning' if report.avg_latency_ms <= 8000 else 'error'}">
                <div>Latence moyenne</div>
                <div class="metric-value">{report.avg_latency_ms:.0f}ms</div>
            </div>
            <div class="metric {'success' if report.avg_confidence >= 0.7 else 'warning' if report.avg_confidence >= 0.5 else 'error'}">
                <div>Confiance moyenne</div>
                <div class="metric-value">{report.avg_confidence:.2f}</div>
            </div>
            <div class="metric {'success' if report.hallucination_rate <= 0.1 else 'warning' if report.hallucination_rate <= 0.2 else 'error'}">
                <div>Hallucinations</div>
                <div class="metric-value">{report.hallucination_rate:.1%}</div>
            </div>
        </div>

        <div class="chart">
            <div id="latency-chart"></div>
        </div>

        <div class="chart">
            <div id="confidence-chart"></div>
        </div>

        <script>
            // Graphique de latence
            const latencyData = {{
                x: {[f"'{r.test_id}'" for r in report.test_results]},
                y: {[r.latency_ms for r in report.test_results]},
                type: 'scatter',
                mode: 'markers',
                marker: {{ size: 8 }},
                name: 'Latence'
            }};

            Plotly.newPlot('latency-chart', [latencyData], {{
                title: 'Latence par test',
                xaxis: {{ title: 'Test ID' }},
                yaxis: {{ title: 'Latence (ms)' }}
            }});

            // Graphique de confiance
            const confidenceData = {{
                x: {[f"'{r.test_id}'" for r in report.test_results]},
                y: {[r.confidence_score for r in report.test_results]},
                type: 'bar',
                marker: {{
                    color: {['"green" if r.confidence_score >= 0.7 else "orange" if r.confidence_score >= 0.5 else "red"' for r in report.test_results]}
                }},
                name: 'Confiance'
            }};

            Plotly.newPlot('confidence-chart', [confidenceData], {{
                title: 'Score de confiance par test',
                xaxis: {{ title: 'Test ID' }},
                yaxis: {{ title: 'Confiance', range: [0, 1] }}
            }});
        </script>
    </div>
</body>
</html>"""

    def compare_reports(self, current_report: str, previous_report: str) -> Dict[str, Any]:
        """Compare deux rapports pour détecter les régressions."""
        with open(current_report) as f:
            current = json.load(f)
        with open(previous_report) as f:
            previous = json.load(f)

        comparison = {
            "success_rate_delta": current["metadata"]["success_rate"] - previous["metadata"]["success_rate"],
            "latency_delta": current["metadata"]["avg_latency_ms"] - previous["metadata"]["avg_latency_ms"],
            "confidence_delta": current["metadata"]["avg_confidence"] - previous["metadata"]["avg_confidence"],
            "hallucination_delta": current["metadata"]["hallucination_rate"] - previous["metadata"]["hallucination_rate"],
        }

        # Détecter les régressions
        comparison["regressions"] = []
        if comparison["success_rate_delta"] < -0.05:
            comparison["regressions"].append("Régression du taux de succès")
        if comparison["latency_delta"] > 1000:
            comparison["regressions"].append("Dégradation de la latence")
        if comparison["confidence_delta"] < -0.1:
            comparison["regressions"].append("Baisse de confiance")
        if comparison["hallucination_delta"] > 0.05:
            comparison["regressions"].append("Augmentation des hallucinations")

        return comparison