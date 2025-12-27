"""
Tests unitaires pour le système de validation qualité v2.8

Tests couvrant :
- Détecteur d'hallucinations
- Système de scoring de confiance
- Orchestrateur de validation
- Métriques et monitoring
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from sentence_transformers import SentenceTransformer

# Import des modules à tester
from src.hyperion.modules.rag.quality.hallucination_detector import HallucinationDetector, HallucinationFlags
from src.hyperion.modules.rag.quality.confidence_scorer import ConfidenceScorer
from src.hyperion.modules.rag.quality.response_validator import ResponseValidator
from src.hyperion.modules.rag.monitoring.quality_metrics import QualityMetricsTracker


class TestHallucinationDetector:
    """Tests pour le détecteur d'hallucinations"""

    @pytest.fixture
    def embedding_model(self):
        """Mock du modèle d'embedding pour les tests"""
        model = MagicMock()
        # Simuler encode() retournant des embeddings dummy
        model.encode.return_value = [[0.1, 0.2, 0.3, 0.4]]
        return model

    @pytest.fixture
    def detector(self, embedding_model):
        """Instance du détecteur pour tests"""
        return HallucinationDetector(embedding_model)

    def test_detect_obvious_hallucination(self, detector):
        """Test détection hallucination évidente"""
        answer = "Selon mes sources, je pense que probablement le projet a 999 contributeurs et utilise Python 42."
        context = ["Le projet a 5 contributeurs principaux avec Python."]
        question = "Combien de contributeurs ?"

        result = detector.detect(answer, context, question)

        # Vérifications
        assert result["is_hallucination"] == True
        assert result["confidence"] < 0.5
        assert result["severity"] in ["HIGH", "CRITICAL"]
        assert len(result["flags"].suspicious_patterns) > 0
        assert any("999" in detail for detail in result["flags"].invented_details)

    def test_detect_good_response(self, detector):
        """Test bonne réponse factuelle"""
        answer = "Le projet a 5 contributeurs principaux utilisant Python."
        context = ["Le projet a 5 contributeurs principaux avec plus de 100 commits en Python."]
        question = "Combien de contributeurs ?"

        result = detector.detect(answer, context, question)

        # Vérifications
        assert result["is_hallucination"] == False
        assert result["confidence"] > 0.6
        assert result["severity"] in ["LOW", "MINIMAL"]
        assert len(result["flags"].suspicious_patterns) == 0

    def test_detect_empty_answer(self, detector):
        """Test réponse vide"""
        result = detector.detect("", ["contexte"], "question")

        assert result["is_hallucination"] == True
        assert result["confidence"] == 0.0
        assert result["severity"] == "CRITICAL"

    def test_novel_content_analysis(self, detector):
        """Test analyse contenu novel"""
        answer = "Le projet utilise des microservices avec Kubernetes et Docker"
        context = ["Le projet utilise Python et FastAPI"]

        novel_ratio = detector._analyze_novel_content(answer, [context])

        # Should detect significant novel content
        assert novel_ratio > 0.3
        assert novel_ratio <= 1.0

    def test_invented_details_detection(self, detector):
        """Test détection détails inventés"""
        answer = "Le projet a été créé en 2023 et compte 1500 lignes de code"
        context = ["Le projet utilise Python pour l'analyse de données"]

        invented = detector._detect_invented_details(answer, [context])

        # Should detect invented year and line count
        assert len(invented) > 0
        assert any("2023" in detail or "1500" in detail for detail in invented)

    def test_suspicious_patterns_detection(self, detector):
        """Test détection patterns suspects"""
        answer = "Je pense que selon mes connaissances le projet est probablement écrit en Java"

        patterns = detector._detect_suspicious_patterns(answer)

        # Should detect multiple suspicious patterns
        assert len(patterns) >= 2
        assert "je pense que" in patterns
        assert "probablement" in patterns


class TestConfidenceScorer:
    """Tests pour le système de scoring de confiance"""

    @pytest.fixture
    def scorer(self):
        """Instance du scorer pour tests"""
        return ConfidenceScorer()

    def test_excellent_quality_response(self, scorer):
        """Test réponse excellente qualité"""
        hallucination_result = {
            "confidence": 0.95,
            "is_hallucination": False,
            "severity": "LOW"
        }
        source_scores = [0.92, 0.88]
        question = "Quel est le langage principal ?"
        answer = "Le langage principal est Python selon l'analyse du repository."

        result = scorer.compute_confidence(
            hallucination_result, source_scores, question, answer
        )

        # Vérifications
        assert result["final_confidence"] > 0.8
        assert result["quality_grade"] in ["EXCELLENT", "GOOD"]
        assert result["action"] == "accept"
        assert result["should_flag"] == False

    def test_poor_quality_response(self, scorer):
        """Test réponse faible qualité"""
        hallucination_result = {
            "confidence": 0.3,
            "is_hallucination": True,
            "severity": "HIGH"
        }
        source_scores = [0.4]
        question = "Combien de fichiers ?"
        answer = "Pas sûr"

        result = scorer.compute_confidence(
            hallucination_result, source_scores, question, answer
        )

        # Vérifications
        assert result["final_confidence"] < 0.6
        assert result["quality_grade"] in ["POOR", "UNACCEPTABLE"]
        assert result["action"] in ["flag", "reject"]
        assert result["should_flag"] == True

    def test_source_quality_scoring(self, scorer):
        """Test scoring qualité sources"""
        # Sources haute qualité
        high_quality = scorer._calculate_source_quality([0.9, 0.85, 0.8])
        assert high_quality > 0.8

        # Sources faible qualité
        low_quality = scorer._calculate_source_quality([0.3, 0.2, 0.1])
        assert low_quality < 0.5

        # Aucune source
        no_sources = scorer._calculate_source_quality([])
        assert no_sources == 0.0

    def test_semantic_relevance_scoring(self, scorer):
        """Test scoring pertinence sémantique"""
        # Question et réponse cohérentes
        relevance = scorer._calculate_semantic_relevance(
            "Combien de fichiers Python ?",
            "Le repository contient 25 fichiers Python"
        )
        assert relevance > 0.6

        # Question et réponse incohérentes
        irrelevance = scorer._calculate_semantic_relevance(
            "Quel est le langage principal ?",
            "La météo est belle aujourd'hui"
        )
        assert irrelevance < 0.4

    def test_response_completeness_scoring(self, scorer):
        """Test scoring complétude réponse"""
        # Réponse complète et informative
        complete = scorer._calculate_response_completeness(
            "Le repository utilise Python comme langage principal avec 150 fichiers.",
            "Quel langage ?"
        )
        assert complete > 0.7

        # Réponse trop courte
        incomplete = scorer._calculate_response_completeness("OK", "Combien de fichiers ?")
        assert incomplete < 0.5

        # Réponse vide
        empty = scorer._calculate_response_completeness("", "Question ?")
        assert empty == 0.0


class TestResponseValidator:
    """Tests pour l'orchestrateur de validation"""

    @pytest.fixture
    def embedding_model(self):
        """Mock du modèle d'embedding"""
        model = MagicMock()
        model.encode.return_value = [[0.1, 0.2, 0.3, 0.4]]
        return model

    @pytest.fixture
    def validator(self, embedding_model):
        """Instance du validateur pour tests"""
        # Mock environment variables
        with patch.dict(os.environ, {
            'CONFIDENCE_THRESHOLD': '0.7',
            'AUTO_REJECT_THRESHOLD': '0.3',
            'VALIDATION_MODE': 'flag'
        }):
            return ResponseValidator(embedding_model)

    def test_validate_good_response(self, validator):
        """Test validation réponse de bonne qualité"""
        answer = "Le repository contient 5 contributeurs principaux."
        question = "Combien de contributeurs ?"
        context = ["Analyse: 5 contributeurs avec plus de 100 commits."]
        source_scores = [0.9]

        result = validator.validate_response(answer, question, context, source_scores)

        # Vérifications
        assert result["action"] == "accept"
        assert result["confidence"] > 0.6
        assert result["should_flag"] == False
        assert "hallucination_analysis" in result
        assert "confidence_breakdown" in result

    def test_validate_poor_response(self, validator):
        """Test validation réponse de faible qualité"""
        answer = "Je pense que probablement il y a beaucoup de contributeurs avec 999 commits."
        question = "Combien de contributeurs ?"
        context = ["Le repository a 3 contributeurs."]
        source_scores = [0.3]

        result = validator.validate_response(answer, question, context, source_scores)

        # Vérifications
        assert result["action"] in ["flag", "reject"]
        assert result["confidence"] < 0.6
        assert result["should_flag"] == True
        assert result["hallucination_analysis"]["is_hallucination"] == True

    def test_validation_error_handling(self, validator):
        """Test gestion erreurs validation"""
        # Simuler erreur dans détecteur
        with patch.object(validator.hallucination_detector, 'detect', side_effect=Exception("Test error")):
            result = validator.validate_response("answer", "question", ["context"], [0.8])

            # Should return safe fallback
            assert result["action"] == "flag"
            assert result["confidence"] == 0.5
            assert "error" in result["validation_metadata"]

    def test_session_statistics(self, validator):
        """Test statistiques de session"""
        # Simuler quelques validations
        validator.validate_response("good answer", "question", ["context"], [0.9])
        validator.validate_response("bad answer", "question", ["context"], [0.2])

        stats = validator.get_session_statistics()

        assert stats["total_validations"] == 2
        assert stats["validations_per_minute"] >= 0
        assert 0 <= stats["acceptance_rate"] <= 100


class TestQualityMetricsTracker:
    """Tests pour le tracker de métriques qualité"""

    @pytest.fixture
    def temp_db(self):
        """Base de données temporaire pour tests"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)

    @pytest.fixture
    def tracker(self, temp_db):
        """Instance du tracker pour tests"""
        return QualityMetricsTracker(db_path=temp_db)

    def test_track_response(self, tracker):
        """Test tracking d'une réponse"""
        validation_result = {
            "confidence": 0.85,
            "quality_grade": "GOOD",
            "action": "accept",
            "should_flag": False,
            "hallucination_analysis": {
                "is_hallucination": False,
                "severity": "LOW",
                "semantic_consistency": 0.9
            },
            "confidence_factors": {
                "primary_weakness": "none"
            },
            "validation_metadata": {
                "validation_time": 0.15,
                "num_sources": 2,
                "avg_source_score": 0.8,
                "answer_length": 50,
                "question_length": 20,
                "validator_version": "2.8.0"
            }
        }

        # Track response
        tracker.track_response(
            validation_result=validation_result,
            processing_time=1.2,
            question="Test question",
            repo="test-repo"
        )

        # Vérifier que les métriques sont enregistrées
        summary = tracker.get_metrics_summary(hours=1)
        assert summary["total_responses"] == 1
        assert summary["acceptance_rate"] == 100.0
        assert summary["avg_confidence"] == 0.85

    def test_metrics_summary(self, tracker):
        """Test calcul résumé des métriques"""
        # Ajouter quelques réponses fictives
        good_result = {
            "confidence": 0.9, "quality_grade": "EXCELLENT", "action": "accept",
            "should_flag": False, "hallucination_analysis": {"is_hallucination": False, "severity": "LOW"},
            "confidence_factors": {"primary_weakness": "none"},
            "validation_metadata": {"validation_time": 0.1, "num_sources": 2, "avg_source_score": 0.9,
                                   "answer_length": 100, "question_length": 30, "validator_version": "2.8.0"}
        }

        bad_result = {
            "confidence": 0.3, "quality_grade": "POOR", "action": "reject",
            "should_flag": True, "hallucination_analysis": {"is_hallucination": True, "severity": "HIGH"},
            "confidence_factors": {"primary_weakness": "hallucination"},
            "validation_metadata": {"validation_time": 0.2, "num_sources": 1, "avg_source_score": 0.3,
                                   "answer_length": 20, "question_length": 25, "validator_version": "2.8.0"}
        }

        tracker.track_response(good_result, 1.0, "good question", "repo1")
        tracker.track_response(bad_result, 2.0, "bad question", "repo2")

        summary = tracker.get_metrics_summary(hours=24)

        # Vérifications
        assert summary["total_responses"] == 2
        assert summary["acceptance_rate"] == 50.0  # 1 accept, 1 reject
        assert summary["rejection_rate"] == 50.0
        assert summary["hallucination_rate"] == 50.0
        assert 0.5 < summary["avg_confidence"] < 0.7  # Moyenne de 0.9 et 0.3

    def test_trend_data(self, tracker):
        """Test données de tendance"""
        # Ajouter une réponse test
        result = {
            "confidence": 0.8, "quality_grade": "GOOD", "action": "accept",
            "should_flag": False, "hallucination_analysis": {"is_hallucination": False, "severity": "LOW"},
            "confidence_factors": {"primary_weakness": "none"},
            "validation_metadata": {"validation_time": 0.1, "num_sources": 1, "avg_source_score": 0.8,
                                   "answer_length": 50, "question_length": 20, "validator_version": "2.8.0"}
        }

        tracker.track_response(result, 1.5, "test question")

        trends = tracker.get_trend_data(days=1)

        # Should have at least one data point for today
        assert len(trends) >= 1
        assert all(isinstance(point["avg_confidence"], float) for point in trends)

    def test_quality_alerts(self, tracker):
        """Test système d'alertes qualité"""
        # Simuler plusieurs réponses de mauvaise qualité pour déclencher alerte
        bad_result = {
            "confidence": 0.2, "quality_grade": "UNACCEPTABLE", "action": "reject",
            "should_flag": True, "hallucination_analysis": {"is_hallucination": True, "severity": "CRITICAL"},
            "confidence_factors": {"primary_weakness": "hallucination"},
            "validation_metadata": {"validation_time": 0.3, "num_sources": 1, "avg_source_score": 0.2,
                                   "answer_length": 10, "question_length": 20, "validator_version": "2.8.0"}
        }

        # Track plusieurs mauvaises réponses pour déclencher alertes
        for i in range(6):  # 6 responses pour dépasser seuils
            tracker.track_response(bad_result, 2.0, f"bad question {i}")

        # Vérifier alertes
        alerts = tracker.get_quality_alerts()
        assert len(alerts) > 0

        # Vérifier qu'au moins une alerte concerne les hallucinations
        alert_types = [alert["alert_type"] for alert in alerts]
        assert any("HALLUCINATION" in alert_type for alert_type in alert_types)

    def test_database_stats(self, tracker):
        """Test statistiques base de données"""
        # Ajouter quelques enregistrements
        result = {
            "confidence": 0.8, "quality_grade": "GOOD", "action": "accept",
            "should_flag": False, "hallucination_analysis": {"is_hallucination": False, "severity": "LOW"},
            "confidence_factors": {"primary_weakness": "none"},
            "validation_metadata": {"validation_time": 0.1, "num_sources": 1, "avg_source_score": 0.8,
                                   "answer_length": 50, "question_length": 20, "validator_version": "2.8.0"}
        }

        tracker.track_response(result, 1.0, "test1")
        tracker.track_response(result, 1.0, "test2")

        stats = tracker.get_database_stats()

        assert stats["total_records"] == 2
        assert stats["database_size_bytes"] > 0
        assert "database_path" in stats


class TestIntegration:
    """Tests d'intégration end-to-end"""

    def test_full_validation_pipeline(self):
        """Test pipeline complet de validation"""
        # Mock embedding model
        embedding_model = MagicMock()
        embedding_model.encode.return_value = [[0.1, 0.2, 0.3]]

        # Créer validateur
        with patch.dict(os.environ, {
            'CONFIDENCE_THRESHOLD': '0.7',
            'AUTO_REJECT_THRESHOLD': '0.3'
        }):
            validator = ResponseValidator(embedding_model)

        # Test avec bonne réponse
        good_result = validator.validate_response(
            answer="Le repository contient 5 fichiers Python principaux.",
            question="Combien de fichiers Python ?",
            context_chunks=["Analyse: 5 fichiers .py dans le repository principal."],
            source_scores=[0.9]
        )

        # Vérifier résultat complet
        assert "action" in good_result
        assert "confidence" in good_result
        assert "hallucination_analysis" in good_result
        assert "confidence_breakdown" in good_result
        assert "recommendations" in good_result
        assert "validation_metadata" in good_result

        # Test avec mauvaise réponse
        bad_result = validator.validate_response(
            answer="Je suppose qu'il y a probablement 999 fichiers Java inventés.",
            question="Combien de fichiers Python ?",
            context_chunks=["Analyse: 5 fichiers .py dans le repository."],
            source_scores=[0.2]
        )

        # Vérifier détection de problèmes
        assert bad_result["action"] in ["flag", "reject"]
        assert bad_result["confidence"] < 0.6
        assert bad_result["hallucination_analysis"]["is_hallucination"] == True


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])