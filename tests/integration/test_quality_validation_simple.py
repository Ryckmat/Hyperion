#!/usr/bin/env python3
"""
Test simple de validation du système de qualité

Ce script teste le système de validation qualité sans nécessiter
de services externes (Qdrant, Neo4j, etc.)
"""

import os
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configurer variables d'environnement pour test
os.environ["ENABLE_RESPONSE_VALIDATION"] = "true"
os.environ["VALIDATION_MODE"] = "flag"
os.environ["CONFIDENCE_THRESHOLD"] = "0.7"
os.environ["AUTO_REJECT_THRESHOLD"] = "0.3"


def test_hallucination_detector():
    """Test détecteur d'hallucinations"""
    print("🔍 Test HallucinationDetector...")

    # Mock embedding model
    class MockEmbeddingModel:
        def encode(self, texts):
            return [
                [0.1, 0.2, 0.3, 0.4] for _ in range(len(texts) if isinstance(texts, list) else 1)
            ]

    from hyperion.modules.rag.quality.hallucination_detector import HallucinationDetector

    detector = HallucinationDetector(MockEmbeddingModel())

    # Test hallucination évidente
    result = detector.detect(
        answer="Selon mes sources, je pense que probablement le projet a 999 contributeurs.",
        context_chunks=["Le projet a 5 contributeurs principaux."],
        question="Combien de contributeurs ?",
    )

    assert result["is_hallucination"]
    assert result["confidence"] < 0.6
    assert len(result["flags"].suspicious_patterns) > 0

    print(
        f"  ✅ Hallucination détectée: confiance={result['confidence']:.2f}, sévérité={result['severity']}"
    )

    # Test bonne réponse
    result2 = detector.detect(
        answer="Le projet a 5 contributeurs principaux.",
        context_chunks=["Le projet a 5 contributeurs principaux avec plus de 100 commits."],
        question="Combien de contributeurs ?",
    )

    assert not result2["is_hallucination"]
    assert result2["confidence"] > 0.6

    print(
        f"  ✅ Bonne réponse validée: confiance={result2['confidence']:.2f}, sévérité={result2['severity']}"
    )


def test_confidence_scorer():
    """Test système de scoring"""
    print("📊 Test ConfidenceScorer...")

    from hyperion.modules.rag.quality.confidence_scorer import ConfidenceScorer

    scorer = ConfidenceScorer()

    # Test excellente qualité
    good_hallucination = {"confidence": 0.9, "is_hallucination": False, "severity": "LOW"}

    result = scorer.compute_confidence(
        hallucination_result=good_hallucination,
        source_scores=[0.92, 0.88],
        question="Quel est le langage principal ?",
        answer="Le langage principal est Python selon l'analyse.",
    )

    assert result["final_confidence"] > 0.8
    assert result["quality_grade"] in ["EXCELLENT", "GOOD"]
    assert result["action"] == "accept"

    print(
        f"  ✅ Excellente qualité: confiance={result['final_confidence']:.2f}, grade={result['quality_grade']}"
    )

    # Test faible qualité
    bad_hallucination = {"confidence": 0.3, "is_hallucination": True, "severity": "HIGH"}

    result2 = scorer.compute_confidence(
        hallucination_result=bad_hallucination,
        source_scores=[0.4],
        question="Combien de fichiers ?",
        answer="Pas sûr",
    )

    assert result2["final_confidence"] < 0.6
    assert result2["action"] in ["flag", "reject"]

    print(
        f"  ✅ Faible qualité détectée: confiance={result2['final_confidence']:.2f}, grade={result2['quality_grade']}"
    )


def test_response_validator():
    """Test orchestrateur de validation"""
    print("🎯 Test ResponseValidator...")

    # Mock embedding model
    class MockEmbeddingModel:
        def encode(self, texts):
            return [
                [0.1, 0.2, 0.3, 0.4] for _ in range(len(texts) if isinstance(texts, list) else 1)
            ]

    from hyperion.modules.rag.quality.response_validator import ResponseValidator

    validator = ResponseValidator(MockEmbeddingModel())

    # Test validation complète
    result = validator.validate_response(
        answer="Le repository contient 5 contributeurs principaux selon l'analyse Git.",
        question="Combien de contributeurs ?",
        context_chunks=["Analyse Git: 5 contributeurs avec plus de 100 commits."],
        source_scores=[0.9],
        processing_time=1.5,
    )

    assert "action" in result
    assert "confidence" in result
    assert "hallucination_analysis" in result
    assert "confidence_breakdown" in result

    print(
        f"  ✅ Validation complète: action={result['action']}, confiance={result['confidence']:.2f}"
    )
    print(f"  ✅ Hallucination: {result['hallucination_analysis']['severity']}")
    print(f"  ✅ Recommandations: {len(result['recommendations'])} suggestions")


def test_quality_metrics():
    """Test système de métriques"""
    print("📈 Test QualityMetricsTracker...")

    import tempfile

    from hyperion.modules.rag.monitoring.quality_metrics import QualityMetricsTracker

    # Base temporaire
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db = tmp.name

    try:
        tracker = QualityMetricsTracker(db_path=temp_db)

        # Mock validation result
        validation_result = {
            "confidence": 0.85,
            "quality_grade": "GOOD",
            "action": "accept",
            "should_flag": False,
            "hallucination_analysis": {
                "is_hallucination": False,
                "severity": "LOW",
                "semantic_consistency": 0.9,
            },
            "confidence_factors": {"primary_weakness": "none"},
            "validation_metadata": {
                "validation_time": 0.15,
                "num_sources": 2,
                "avg_source_score": 0.8,
                "answer_length": 50,
                "question_length": 20,
                "validator_version": "2.8.0",
            },
        }

        # Track réponse
        tracker.track_response(
            validation_result=validation_result,
            processing_time=1.2,
            question="Test question",
            repo="test-repo",
        )

        # Vérifier métriques
        summary = tracker.get_metrics_summary(hours=1)
        assert summary["total_responses"] == 1
        assert summary["acceptance_rate"] == 100.0

        print(f"  ✅ Métriques trackées: {summary['total_responses']} réponses")
        print(f"  ✅ Taux acceptation: {summary['acceptance_rate']}%")
        print(f"  ✅ Confiance moyenne: {summary['avg_confidence']:.2f}")

    finally:
        # Cleanup
        os.unlink(temp_db)


def main():
    """Fonction principale de test"""
    print("🚀 Test système de validation qualité")
    print("=" * 50)

    try:
        test_hallucination_detector()
        test_confidence_scorer()
        test_response_validator()
        test_quality_metrics()

        print("\n" + "=" * 50)
        print("✅ TOUS LES TESTS PASSÉS - Système qualité opérationnel !")
        print("\n🎯 Prêt pour intégration dans Hyperion")
        print("📊 Fonctionnalités validées :")
        print("   - Détection d'hallucinations multi-niveaux")
        print("   - Scoring de confiance global")
        print("   - Validation orchestrée complète")
        print("   - Monitoring et métriques qualité")

        return True

    except Exception as e:
        print(f"\n❌ ERREUR DANS LES TESTS: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
