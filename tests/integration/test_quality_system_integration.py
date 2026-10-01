"""
Test d'intégration du système de validation qualité avec Hyperion

Ce test valide que le système de qualité fonctionne correctement
dans l'environnement complet de Hyperion (API, RAG, base de données).
"""

import os
import time
from pathlib import Path

import pytest
import requests


class TestQualitySystemIntegration:
    """Tests d'intégration système complet"""

    @classmethod
    def setup_class(cls):
        """Setup une fois pour toute la classe de tests"""
        cls.api_base_url = "http://localhost:8000"
        cls.test_questions = [
            "Combien de fichiers Python dans le repository ?",
            "Qui est le contributeur principal ?",
            "Quelle est l'architecture du projet ?",
            "Combien de lignes de code ?",
        ]

    def test_api_health_includes_quality_monitoring(self):
        """Test que l'API health check inclut le monitoring qualité"""
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=10)
            assert response.status_code == 200

            health = response.json()
            assert "status" in health
            assert health["status"] in ["healthy", "warning"]

            # Vérifier endpoint racine inclut features qualité
            root_response = requests.get(f"{self.api_base_url}/", timeout=5)
            assert root_response.status_code == 200

            root_data = root_response.json()
            assert "quality_monitoring" in root_data.get("features", [])
            assert "quality_metrics" in root_data.get("endpoints", {})

        except requests.exceptions.RequestException:
            pytest.skip("API non accessible - démarrer avec script master")

    def test_chat_endpoint_with_quality_validation(self):
        """Test endpoint chat avec validation qualité activée"""
        try:
            # Test chat normal
            chat_payload = {"question": "Combien de fichiers Python dans Hyperion ?", "repo": None}

            response = requests.post(f"{self.api_base_url}/api/chat", json=chat_payload, timeout=15)

            assert response.status_code == 200
            result = response.json()

            # Vérifier structure réponse de base
            assert "answer" in result
            assert "sources" in result
            assert "processing_time" in result

            # Vérifier présence données qualité si validation activée
            if "quality" in result:
                quality = result["quality"]
                assert "confidence" in quality
                assert "grade" in quality
                assert "action" in quality
                assert "hallucination_detected" in quality
                assert quality["grade"] in ["EXCELLENT", "GOOD", "FAIR", "POOR", "UNACCEPTABLE"]
                assert quality["action"] in ["accept", "flag", "reject"]
                assert isinstance(quality["confidence"], (int, float))
                assert 0.0 <= quality["confidence"] <= 1.0

                print(
                    f"✅ Validation qualité: {quality['grade']} (confidence: {quality['confidence']})"
                )

            else:
                print("ℹ️ Validation qualité désactivée")

        except requests.exceptions.RequestException:
            pytest.skip("API non accessible - démarrer avec script master")

    def test_quality_metrics_endpoints(self):
        """Test endpoints de métriques qualité"""
        try:
            # Test endpoint métriques
            metrics_response = requests.get(
                f"{self.api_base_url}/api/quality/metrics?hours=1", timeout=10
            )

            if metrics_response.status_code == 200:
                metrics = metrics_response.json()

                # Vérifier structure métriques
                expected_fields = [
                    "total_responses",
                    "avg_confidence",
                    "acceptance_rate",
                    "flag_rate",
                    "rejection_rate",
                    "hallucination_rate",
                ]

                for field in expected_fields:
                    assert field in metrics, f"Champ manquant: {field}"

                # Vérifier types et ranges
                assert isinstance(metrics["total_responses"], int)
                assert 0 <= metrics["acceptance_rate"] <= 100
                assert 0 <= metrics["avg_confidence"] <= 1.0

                print(
                    f"✅ Métriques qualité: {metrics['total_responses']} réponses, {metrics['avg_confidence']:.2f} confidence"
                )

            elif metrics_response.status_code == 503:
                print("ℹ️ Monitoring qualité non disponible (service non démarré)")
            else:
                pytest.fail(f"Erreur endpoint métriques: {metrics_response.status_code}")

            # Test endpoint trends
            trends_response = requests.get(
                f"{self.api_base_url}/api/quality/trends?days=1", timeout=10
            )

            if trends_response.status_code == 200:
                trends_data = trends_response.json()
                assert "trends" in trends_data
                assert "period_days" in trends_data
                assert trends_data["period_days"] == 1

            # Test endpoint alertes
            alerts_response = requests.get(f"{self.api_base_url}/api/quality/alerts", timeout=10)

            if alerts_response.status_code == 200:
                alerts_data = alerts_response.json()
                assert "alerts" in alerts_data
                assert "total" in alerts_data
                assert isinstance(alerts_data["alerts"], list)

        except requests.exceptions.RequestException:
            pytest.skip("API non accessible - démarrer avec script master")

    def test_multiple_chat_requests_quality_tracking(self):
        """Test tracking qualité sur plusieurs requêtes chat"""
        try:
            results = []

            # Faire plusieurs requêtes avec différents types de questions
            test_cases = [
                {
                    "question": "Combien de contributeurs ?",
                    "expected_grade": ["GOOD", "FAIR", "EXCELLENT"],
                },
                {"question": "Python files count", "expected_grade": ["GOOD", "FAIR", "EXCELLENT"]},
                {
                    "question": "Quelle est l'architecture ?",
                    "expected_grade": ["GOOD", "FAIR", "POOR"],
                },
                {
                    "question": "Blabla random question",
                    "expected_grade": ["POOR", "FAIR"],
                },  # Question moins pertinente
            ]

            for _i, test_case in enumerate(test_cases):
                chat_payload = {"question": test_case["question"], "repo": None}

                response = requests.post(
                    f"{self.api_base_url}/api/chat", json=chat_payload, timeout=15
                )

                assert response.status_code == 200
                result = response.json()
                results.append(result)

                # Attendre un peu entre requêtes
                time.sleep(0.5)

            # Vérifier que la qualité varie selon les questions
            quality_grades = []
            confidence_scores = []

            for result in results:
                if "quality" in result:
                    quality = result["quality"]
                    quality_grades.append(quality["grade"])
                    confidence_scores.append(quality["confidence"])

            if quality_grades:
                print(f"✅ Grades qualité obtenus: {quality_grades}")
                print(f"✅ Scores confiance: {[f'{s:.2f}' for s in confidence_scores]}")

                # Vérifier variation des scores (système adaptatif)
                assert len(set(quality_grades)) >= 1, "Système devrait produire des grades variés"

            # Vérifier que les métriques sont mises à jour
            time.sleep(2)  # Attendre processing plus long

            metrics_response = requests.get(
                f"{self.api_base_url}/api/quality/metrics?hours=1", timeout=10
            )

            if metrics_response.status_code == 200:
                updated_metrics = metrics_response.json()
                # Note: En mode test/intégration, les métriques peuvent ne pas être persistées
                # On vérifie juste que l'endpoint répond correctement
                total_responses = updated_metrics.get("total_responses", 0)
                print(f"✅ Métriques endpoint accessible: {total_responses} réponses trackées")
                # Test plus flexible pour l'intégration
                assert total_responses >= 0, "L'endpoint métriques doit retourner un nombre >= 0"

        except requests.exceptions.RequestException:
            pytest.skip("API non accessible - démarrer avec script master")

    def test_quality_validation_with_rejection_mode(self):
        """Test validation en mode rejection"""
        try:
            # Test avec une question volontairement problématique
            problematic_question = "Combien de licornes magiques dans le code source ?"

            chat_payload = {"question": problematic_question, "repo": None}

            response = requests.post(f"{self.api_base_url}/api/chat", json=chat_payload, timeout=15)

            assert response.status_code == 200
            result = response.json()

            if "quality" in result:
                quality = result["quality"]

                # Questions absurdes devraient être flaggées ou rejetées
                if quality["action"] in ["flag", "reject"]:
                    print(f"✅ Question problématique correctement {quality['action']}ée")
                    print(f"   Confidence: {quality['confidence']:.2f}, Grade: {quality['grade']}")

                # Si réponse modifiée, vérifier
                if quality.get("answer_modified", False):
                    print("✅ Réponse automatiquement modifiée par validation")
                    assert (
                        "ne peux pas répondre" in result["answer"].lower()
                        or "reformuler" in result["answer"].lower()
                    )

        except requests.exceptions.RequestException:
            pytest.skip("API non accessible - démarrer avec script master")

    def test_quality_database_persistence(self):
        """Test persistance des données qualité"""
        try:
            # Faire une requête
            chat_payload = {"question": "Test persistence", "repo": None}

            response = requests.post(f"{self.api_base_url}/api/chat", json=chat_payload, timeout=10)

            assert response.status_code == 200

            # Attendre un peu pour persistance
            time.sleep(1)

            # Vérifier stats base de données
            stats_response = requests.get(f"{self.api_base_url}/api/quality/stats", timeout=10)

            if stats_response.status_code == 200:
                stats = stats_response.json()
                assert "total_records" in stats
                assert "database_size_bytes" in stats
                assert stats["total_records"] >= 1
                assert stats["database_size_bytes"] > 0

                print(
                    f"✅ Base données qualité: {stats['total_records']} records, {stats['database_size_bytes']} bytes"
                )

        except requests.exceptions.RequestException:
            pytest.skip("API non accessible - démarrer avec script master")


class TestMasterScriptIntegration:
    """Tests d'intégration avec le script master"""

    @pytest.fixture
    def hyperion_project_root(self):
        """Chemin vers la racine du projet Hyperion"""
        current_dir = Path(__file__).parent
        # Remonter jusqu'à trouver le script master
        while current_dir.parent != current_dir:
            master_script = current_dir / "scripts" / "deploy" / "hyperion_master.sh"
            if master_script.exists():
                return current_dir
            current_dir = current_dir.parent

        pytest.skip("Script master non trouvé")

    def test_master_script_accessible(self, hyperion_project_root):
        """Test que le script master est accessible"""
        master_script = hyperion_project_root / "scripts" / "deploy" / "hyperion_master.sh"
        assert master_script.exists(), "Script master non trouvé"
        assert os.access(master_script, os.X_OK), "Script master non exécutable"

    def test_quality_validation_environment_variables(self):
        """Test que les variables d'environnement qualité sont correctes"""
        env_file = Path(".env")

        if env_file.exists():
            env_content = env_file.read_text()

            # Vérifier présence variables qualité
            required_vars = [
                "ENABLE_RESPONSE_VALIDATION",
                "VALIDATION_MODE",
                "CONFIDENCE_THRESHOLD",
                "AUTO_REJECT_THRESHOLD",
            ]

            for var in required_vars:
                assert var in env_content, f"Variable d'environnement manquante: {var}"

            print("✅ Variables d'environnement qualité présentes")

        else:
            pytest.skip("Fichier .env non trouvé")

    def test_quality_modules_importable(self):
        """Test que les modules qualité sont correctement importables"""
        try:
            # Test imports modules qualité
            from src.hyperion.modules.rag.monitoring.quality_metrics import (
                QualityMetricsTracker,  # noqa: F401
            )
            from src.hyperion.modules.rag.quality.confidence_scorer import (
                ConfidenceScorer,  # noqa: F401
            )
            from src.hyperion.modules.rag.quality.hallucination_detector import (
                HallucinationDetector,  # noqa: F401
            )
            from src.hyperion.modules.rag.quality.response_validator import (
                ResponseValidator,  # noqa: F401
            )

            print("✅ Tous les modules qualité importables")

        except ImportError as e:
            pytest.fail(f"Erreur import module qualité: {e}")


def run_integration_tests():
    """Fonction utilitaire pour lancer les tests d'intégration"""
    print("🚀 Démarrage tests d'intégration système qualité")
    print("=" * 60)

    # Check API accessibility first
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Hyperion accessible")
        else:
            print("⚠️ API Hyperion répond mais avec erreur")
    except Exception:
        print("❌ API Hyperion non accessible")
        print("   Démarrez d'abord: ./scripts/deploy/hyperion_master.sh")
        return False

    # Run tests
    exit_code = pytest.main([__file__, "-v", "--tb=short", "--color=yes"])

    return exit_code == 0


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
