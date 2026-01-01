#!/usr/bin/env python3
"""
Runner principal pour l'évaluation RAG Hyperion.

Point d'entrée pour exécuter les suites d'évaluation et générer les rapports.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml

from eval.metrics.reporter import EvaluationReporter, TestResult


class RAGEvaluator:
    """
    Évaluateur principal pour le système RAG d'Hyperion.

    Exécute les suites de tests et collecte les métriques de performance.
    """

    def __init__(self):
        self.reporter = EvaluationReporter()
        self.rag_engine = None
        self.quality_tracker = None

    def _load_rag_engine(self):
        """Charge le moteur RAG de façon lazy."""
        if self.rag_engine is None:
            try:
                from hyperion.modules.rag.query import RAGQueryEngine
                self.rag_engine = RAGQueryEngine()
                click.echo("✅ Moteur RAG chargé")
            except Exception as e:
                click.echo(f"❌ Erreur chargement RAG : {e}")
                raise

    def _load_quality_tracker(self):
        """Charge le tracker de qualité de façon lazy."""
        if self.quality_tracker is None:
            try:
                from hyperion.modules.rag.monitoring.quality_metrics import QualityMetricsTracker
                self.quality_tracker = QualityMetricsTracker()
                click.echo("✅ Tracker qualité chargé")
            except Exception as e:
                click.echo(f"⚠️ Tracker qualité non disponible : {e}")
                self.quality_tracker = None

    def load_test_suite(self, suite_path: str) -> Dict[str, Any]:
        """Charge une suite de tests depuis un fichier YAML."""
        with open(suite_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_questions_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Charge le dataset de questions."""
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def execute_test(self, test_config: Dict[str, Any]) -> TestResult:
        """
        Exécute un test individuel.

        Args:
            test_config: Configuration du test

        Returns:
            Résultat du test
        """
        test_id = test_config["id"]
        question = test_config["question"]

        click.echo(f"   Exécution : {test_id}")

        start_time = time.time()
        success = True
        error_msg = None
        response = ""
        confidence_score = 0.0
        hallucination_detected = False
        sources_used = []

        try:
            # Exécution de la requête RAG
            if self.rag_engine:
                rag_result = await asyncio.to_thread(
                    self.rag_engine.query,
                    question,
                    repo_name="hyperion"  # Repository par défaut pour les tests
                )

                response = rag_result.get("answer", "")
                sources_used = rag_result.get("sources", [])
                confidence_score = rag_result.get("confidence", 0.0)

                # Vérification de qualité si disponible
                if self.quality_tracker:
                    quality_result = self.quality_tracker.validate_response(
                        question, response, sources_used
                    )
                    hallucination_detected = quality_result.get("hallucination_detected", False)
                    confidence_score = quality_result.get("confidence_score", confidence_score)

            else:
                # Mode simulation si RAG non disponible
                response = f"Simulation de réponse pour : {question}"
                confidence_score = 0.5

            # Validation des critères de test
            success = self._validate_test_criteria(test_config, response, confidence_score)

        except Exception as e:
            success = False
            error_msg = str(e)
            click.echo(f"      ❌ Erreur : {error_msg}")

        latency_ms = (time.time() - start_time) * 1000

        return TestResult(
            test_id=test_id,
            question=question,
            response=response,
            latency_ms=latency_ms,
            confidence_score=confidence_score,
            hallucination_detected=hallucination_detected,
            sources_used=sources_used,
            success=success,
            error=error_msg,
            metadata={
                "category": test_config.get("tags", []),
                "expected_type": test_config.get("expected_type"),
                "min_confidence": test_config.get("min_confidence"),
                "max_latency_ms": test_config.get("max_latency_ms")
            }
        )

    def _validate_test_criteria(self, test_config: Dict[str, Any], response: str, confidence: float) -> bool:
        """
        Valide les critères de réussite d'un test.

        Args:
            test_config: Configuration du test
            response: Réponse générée
            confidence: Score de confiance

        Returns:
            True si le test réussit
        """
        # Critère de confiance minimum
        min_confidence = test_config.get("min_confidence", 0.0)
        if confidence < min_confidence:
            return False

        # Critère de longueur minimum
        min_length = test_config.get("min_length", 0)
        if len(response) < min_length:
            return False

        # Critère de longueur maximum
        max_length = test_config.get("max_length", float('inf'))
        if len(response) > max_length:
            return False

        # Vérification de contenu attendu
        expected_contains = test_config.get("expected_contains", [])
        for expected in expected_contains:
            if expected.lower() not in response.lower():
                return False

        # Pattern regex si spécifié
        expected_pattern = test_config.get("expected_pattern")
        if expected_pattern:
            import re
            if not re.search(expected_pattern, response, re.IGNORECASE):
                return False

        return True

    async def run_test_suite(self, suite_path: str, questions_path: Optional[str] = None) -> List[TestResult]:
        """
        Exécute une suite complète de tests.

        Args:
            suite_path: Chemin vers la suite de tests
            questions_path: Chemin optionnel vers le dataset de questions

        Returns:
            Liste des résultats de tests
        """
        # Charger les composants
        self._load_rag_engine()
        self._load_quality_tracker()

        # Charger la configuration
        suite_config = self.load_test_suite(suite_path)
        suite_name = suite_config["name"]

        click.echo(f"🧪 Exécution de la suite : {suite_name}")
        click.echo(f"   Description : {suite_config.get('description', 'N/A')}")

        tests = suite_config.get("tests", [])
        click.echo(f"   Nombre de tests : {len(tests)}")

        # Ajouter les tests d'hallucination si présents
        hallucination_tests = suite_config.get("hallucination_tests", [])
        tests.extend(hallucination_tests)

        click.echo("   Démarrage des tests...")

        results = []
        for i, test_config in enumerate(tests, 1):
            click.echo(f"   [{i}/{len(tests)}]", nl=False)
            result = await self.execute_test(test_config)
            results.append(result)

            # Affichage du résultat
            status_icon = "✅" if result.success else "❌"
            click.echo(f" {status_icon} {result.latency_ms:.0f}ms (conf: {result.confidence_score:.2f})")

        click.echo(f"\n📊 Tests terminés : {sum(1 for r in results if r.success)}/{len(results)} réussis")

        return results

    def generate_reports(self, results: List[TestResult], suite_name: str, output_formats: List[str]) -> List[str]:
        """
        Génère les rapports dans les formats demandés.

        Args:
            results: Résultats des tests
            suite_name: Nom de la suite
            output_formats: Formats de sortie ('json', 'markdown', 'html')

        Returns:
            Liste des chemins des rapports générés
        """
        report = self.reporter.analyze_results(results, suite_name)
        generated_files = []

        click.echo("\n📋 Génération des rapports...")

        if "json" in output_formats:
            json_file = self.reporter.generate_json_report(report)
            generated_files.append(json_file)
            click.echo(f"   ✅ Rapport JSON : {json_file}")

        if "markdown" in output_formats:
            md_file = self.reporter.generate_markdown_report(report)
            generated_files.append(md_file)
            click.echo(f"   ✅ Rapport Markdown : {md_file}")

        if "html" in output_formats:
            html_file = self.reporter.generate_html_report(report)
            generated_files.append(html_file)
            click.echo(f"   ✅ Rapport HTML : {html_file}")

        return generated_files


# ============================================================================
# Interface CLI
# ============================================================================

@click.group()
def cli():
    """Outil d'évaluation RAG pour Hyperion."""
    pass


@cli.command()
@click.argument("suite", type=click.Path(exists=True))
@click.option("--questions", type=click.Path(exists=True), help="Dataset de questions optionnel")
@click.option("--format", "formats", multiple=True, default=["json", "markdown"],
              type=click.Choice(["json", "markdown", "html"]), help="Formats de rapport")
@click.option("--verbose", "-v", is_flag=True, help="Mode verbeux")
def run(suite: str, questions: Optional[str], formats: List[str], verbose: bool):
    """
    Exécute une suite d'évaluation RAG.

    Exemple:
        python eval/run.py run eval/suites/core.yaml --format json markdown
    """
    if verbose:
        click.echo("Mode verbeux activé")

    evaluator = RAGEvaluator()

    async def main():
        results = await evaluator.run_test_suite(suite, questions)

        # Analyser le nom de la suite depuis le fichier
        suite_config = evaluator.load_test_suite(suite)
        suite_name = suite_config["name"]

        # Générer les rapports
        report_files = evaluator.generate_reports(results, suite_name, list(formats))

        click.echo(f"\n🎉 Évaluation terminée ! Rapports générés :")
        for file in report_files:
            click.echo(f"   📄 {file}")

    # Exécution asynchrone
    asyncio.run(main())


@cli.command()
@click.argument("report1", type=click.Path(exists=True))
@click.argument("report2", type=click.Path(exists=True))
def compare(report1: str, report2: str):
    """
    Compare deux rapports d'évaluation.

    Exemple:
        python eval/run.py compare report1.json report2.json
    """
    evaluator = RAGEvaluator()
    comparison = evaluator.reporter.compare_reports(report1, report2)

    click.echo("📊 Comparaison des rapports")
    click.echo(f"   Taux de succès : {comparison['success_rate_delta']:+.1%}")
    click.echo(f"   Latence : {comparison['latency_delta']:+.0f}ms")
    click.echo(f"   Confiance : {comparison['confidence_delta']:+.2f}")
    click.echo(f"   Hallucinations : {comparison['hallucination_delta']:+.1%}")

    if comparison["regressions"]:
        click.echo("\n⚠️ Régressions détectées :")
        for regression in comparison["regressions"]:
            click.echo(f"   - {regression}")
    else:
        click.echo("\n✅ Aucune régression détectée")


@cli.command()
@click.option("--suite-dir", default="eval/suites", help="Dossier des suites")
def list_suites(suite_dir: str):
    """Liste les suites d'évaluation disponibles."""
    suite_path = Path(suite_dir)
    if not suite_path.exists():
        click.echo("❌ Dossier des suites non trouvé")
        return

    suites = list(suite_path.glob("*.yaml"))
    if not suites:
        click.echo("Aucune suite trouvée")
        return

    click.echo("📋 Suites d'évaluation disponibles :")
    for suite_file in suites:
        try:
            with open(suite_file) as f:
                config = yaml.safe_load(f)
            name = config.get("name", suite_file.stem)
            description = config.get("description", "Pas de description")
            test_count = len(config.get("tests", []))

            click.echo(f"   • {name} ({test_count} tests)")
            click.echo(f"     {description}")
        except Exception as e:
            click.echo(f"   • {suite_file.name} (erreur: {e})")


if __name__ == "__main__":
    cli()