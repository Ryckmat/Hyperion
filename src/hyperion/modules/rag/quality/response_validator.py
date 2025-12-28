"""
Orchestrateur de validation complète des réponses RAG

Ce module orchestre la validation qualité en combinant :
- Détection d'hallucinations
- Scoring de confiance
- Logging et monitoring
- Décisions d'action
"""

import logging
import os
import time
from datetime import datetime

from .confidence_scorer import ConfidenceScorer
from .hallucination_detector import HallucinationDetector

logger = logging.getLogger(__name__)


class ResponseValidator:
    """
    Orchestrateur principal de validation des réponses RAG

    Coordonne l'analyse complète de qualité et fournit des décisions
    d'action basées sur des seuils configurables.
    """

    def __init__(self, embedding_model):
        """
        Initialiser le validateur

        Args:
            embedding_model: Modèle d'embedding pour analyse sémantique
        """
        self.embedding_model = embedding_model

        # Composants de validation
        self.hallucination_detector = HallucinationDetector(embedding_model)
        self.confidence_scorer = ConfidenceScorer()

        # Configuration des seuils (depuis variables d'environnement)
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self.auto_reject_threshold = float(os.getenv("AUTO_REJECT_THRESHOLD", "0.3"))
        self.hallucination_strict_mode = (
            os.getenv("HALLUCINATION_DETECTION_STRICT", "false").lower() == "true"
        )

        # Configuration du mode de validation
        self.validation_mode = os.getenv("VALIDATION_MODE", "flag")  # "flag" ou "reject"
        self.enable_logging = os.getenv("ENABLE_QUALITY_LOGGING", "true").lower() == "true"

        # Statistiques de session
        self.session_stats = {
            "total_validations": 0,
            "accepted": 0,
            "flagged": 0,
            "rejected": 0,
            "avg_confidence": 0.0,
            "session_start": datetime.now(),
        }

        logger.info(
            f"ResponseValidator initialisé - thresholds: confidence={self.confidence_threshold}, reject={self.auto_reject_threshold}, mode={self.validation_mode}"
        )

    def validate_response(
        self,
        answer: str,
        question: str,
        context_chunks: list[str],
        source_scores: list[float],
        processing_time: float | None = None,
    ) -> dict:
        """
        Validation complète d'une réponse RAG

        Args:
            answer: Réponse générée par le LLM
            question: Question originale de l'utilisateur
            context_chunks: Liste des chunks de contexte utilisés
            source_scores: Scores de similarité des sources Qdrant
            processing_time: Temps de traitement de la requête (optionnel)

        Returns:
            Dictionnaire complet avec résultats validation et recommandations
        """
        validation_start = time.time()

        try:
            # 1. Détection d'hallucinations
            logger.debug(f"Démarrage détection hallucinations pour question: {question[:50]}...")
            hallucination_result = self.hallucination_detector.detect(
                answer, context_chunks, question
            )

            # 2. Calcul score de confiance global
            logger.debug("Calcul score de confiance global...")
            processing_metadata = {
                "processing_time": processing_time,
                "validation_time": None,  # Sera rempli à la fin
            }

            confidence_result = self.confidence_scorer.compute_confidence(
                hallucination_result, source_scores, question, answer, processing_metadata
            )

            # 3. Décision d'action finale
            final_action = self._determine_final_action(
                confidence_result, hallucination_result, answer
            )

            # 4. Enrichissement des métadonnées
            validation_time = time.time() - validation_start
            processing_metadata["validation_time"] = round(validation_time, 3)

            # 5. Construction du résultat final
            validation_result = {
                "action": final_action,
                "confidence": confidence_result["final_confidence"],
                "quality_grade": confidence_result["quality_grade"],
                "should_flag": confidence_result["should_flag"],
                # Détails d'analyse
                "hallucination_analysis": {
                    "is_hallucination": hallucination_result["is_hallucination"],
                    "severity": hallucination_result["severity"],
                    "confidence": hallucination_result["confidence"],
                    "flags": hallucination_result["flags"],
                    "semantic_consistency": hallucination_result.get("semantic_consistency", 0.0),
                },
                "confidence_breakdown": confidence_result["breakdown"],
                "confidence_factors": confidence_result["confidence_factors"],
                # Recommandations
                "recommendations": self._generate_comprehensive_recommendations(
                    confidence_result, hallucination_result, final_action
                ),
                # Métadonnées
                "validation_metadata": {
                    "validator_version": "2.8.0",
                    "validation_time": validation_time,
                    "total_processing_time": processing_time,
                    "thresholds_used": {
                        "confidence": self.confidence_threshold,
                        "auto_reject": self.auto_reject_threshold,
                    },
                    "validation_mode": self.validation_mode,
                    "strict_mode": self.hallucination_strict_mode,
                    "num_context_chunks": len(context_chunks),
                    "num_sources": len(source_scores),
                    "avg_source_score": (
                        sum(source_scores) / len(source_scores) if source_scores else 0.0
                    ),
                    "answer_length": len(answer),
                    "question_length": len(question),
                },
            }

            # 6. Logging et statistiques
            self._log_validation_result(validation_result, question, answer)
            self._update_session_stats(validation_result)

            # 7. Alertes en mode strict
            if self.hallucination_strict_mode and validation_result["action"] == "reject":
                logger.warning(
                    f"STRICT MODE: Réponse rejetée - {validation_result['quality_grade']} - {hallucination_result['severity']}"
                )

            # 8. Nettoyage des types pour sérialisation JSON
            return sanitize_for_json(validation_result)

        except Exception as e:
            logger.error(f"Erreur validation réponse: {e}")
            return self._get_validation_error_fallback(str(e), question, answer)

    def _determine_final_action(
        self, confidence_result: dict, hallucination_result: dict, answer: str
    ) -> str:
        """
        Déterminer l'action finale en combinant tous les critères

        Args:
            confidence_result: Résultat du confidence scorer
            hallucination_result: Résultat du détecteur d'hallucinations
            answer: Réponse pour contexte additionnel

        Returns:
            Action: "accept", "flag", "reject"
        """
        final_confidence = confidence_result["final_confidence"]
        hallucination_severity = hallucination_result["severity"]
        is_hallucination = hallucination_result["is_hallucination"]

        # Règles de rejet strict (priorité absolue)
        if hallucination_severity == "CRITICAL":
            return "reject"

        if self.hallucination_strict_mode and is_hallucination:
            return "reject"

        # Règles basées sur seuils de confiance
        if final_confidence < self.auto_reject_threshold:
            return "reject"

        if final_confidence < self.confidence_threshold:
            return "flag"

        # Règles contextuelles additionnelles
        if len(answer.strip()) < 10:  # Réponse très courte
            return "flag"

        if hallucination_severity in ["HIGH", "MEDIUM"] and final_confidence < 0.8:
            return "flag"

        return "accept"

    def _generate_comprehensive_recommendations(
        self, confidence_result: dict, hallucination_result: dict, final_action: str
    ) -> list[str]:
        """
        Générer recommandations complètes basées sur l'analyse

        Returns:
            Liste de recommandations actionnables
        """
        recommendations = []

        # Recommandations basées sur l'action
        if final_action == "reject":
            recommendations.extend(
                [
                    "Réponse rejetée - validation humaine recommandée",
                    "Vérifier la pertinence des sources sélectionnées",
                    "Considérer reformulation de la question",
                ]
            )
        elif final_action == "flag":
            recommendations.extend(
                ["Réponse flaggée pour review", "Vérifier cohérence avec les sources"]
            )

        # Recommandations spécifiques aux hallucinations
        hallucination_recs = hallucination_result.get("recommendations", [])
        recommendations.extend(hallucination_recs)

        # Recommandations basées sur la faiblesse principale
        primary_weakness = confidence_result["confidence_factors"]["primary_weakness"]

        weakness_recommendations = {
            "hallucination": [
                "Ajuster température du modèle LLM",
                "Renforcer prompt de fidélité aux sources",
            ],
            "source_quality": [
                "Augmenter nombre de chunks récupérés",
                "Améliorer indexation des embeddings",
                "Vérifier pertinence du modèle d'embedding",
            ],
            "semantic_relevance": [
                "Améliorer compréhension de la question",
                "Optimiser sélection de contexte",
                "Considérer expansion de requête",
            ],
            "response_completeness": [
                "Augmenter max_tokens du modèle",
                "Améliorer prompt de structuration",
                "Vérifier que le contexte est suffisant",
            ],
        }

        if primary_weakness in weakness_recommendations:
            recommendations.extend(weakness_recommendations[primary_weakness])

        # Recommandations basées sur les forces (pour maintenir la qualité)
        strengths = confidence_result["confidence_factors"]["strengths"]
        if "high_quality_sources" in strengths:
            recommendations.append("✓ Sources de haute qualité - maintenir cette approche")

        # Déduplication et limitation
        unique_recommendations = list(dict.fromkeys(recommendations))  # Préserve l'ordre
        return unique_recommendations[:8]  # Limiter à 8 recommandations max

    def _log_validation_result(self, validation_result: dict, question: str, answer: str):
        """
        Logger les résultats de validation pour monitoring

        Args:
            validation_result: Résultat complet de validation
            question: Question originale (pour hash anonyme)
            answer: Réponse (pour statistiques)
        """
        if not self.enable_logging:
            return

        # Hash anonyme de la question pour tracking
        question_hash = abs(hash(question)) % 10000

        log_data = {
            "question_hash": question_hash,
            "action": validation_result["action"],
            "confidence": validation_result["confidence"],
            "quality_grade": validation_result["quality_grade"],
            "hallucination_severity": validation_result["hallucination_analysis"]["severity"],
            "answer_length": len(answer),
            "validation_time": validation_result["validation_metadata"]["validation_time"],
            "primary_weakness": validation_result["confidence_factors"]["primary_weakness"],
        }

        # Logging niveau approprié selon action
        if validation_result["action"] == "reject":
            logger.warning(f"Validation REJECT: {log_data}")
        elif validation_result["action"] == "flag":
            logger.info(f"Validation FLAG: {log_data}")
        else:
            logger.debug(f"Validation ACCEPT: {log_data}")

    def _update_session_stats(self, validation_result: dict):
        """
        Mettre à jour statistiques de session

        Args:
            validation_result: Résultat de validation pour statistiques
        """
        self.session_stats["total_validations"] += 1

        action = validation_result["action"]
        if action == "accept":
            self.session_stats["accepted"] += 1
        elif action == "flag":
            self.session_stats["flagged"] += 1
        elif action == "reject":
            self.session_stats["rejected"] += 1

        # Mise à jour moyenne mobile de confiance
        current_confidence = validation_result["confidence"]
        total = self.session_stats["total_validations"]
        prev_avg = self.session_stats["avg_confidence"]

        self.session_stats["avg_confidence"] = (prev_avg * (total - 1) + current_confidence) / total

        # Log statistiques périodiquement
        if total % 10 == 0:  # Tous les 10 validations
            logger.info(f"Session stats: {self.session_stats}")

    def _get_validation_error_fallback(self, error_msg: str, question: str, answer: str) -> dict:
        """
        Résultat de fallback en cas d'erreur de validation

        Args:
            error_msg: Message d'erreur
            question: Question pour contexte
            answer: Réponse pour contexte

        Returns:
            Résultat de validation safe par défaut
        """
        logger.error(f"Fallback validation pour question hash {abs(hash(question)) % 10000}")

        return {
            "action": "flag",  # Action safe en cas d'erreur
            "confidence": 0.5,
            "quality_grade": "UNKNOWN",
            "should_flag": True,
            "hallucination_analysis": {
                "is_hallucination": False,
                "severity": "UNKNOWN",
                "confidence": 0.5,
                "flags": {},
                "semantic_consistency": 0.5,
            },
            "confidence_breakdown": {
                "hallucination": 0.5,
                "source_quality": 0.5,
                "semantic_relevance": 0.5,
                "response_completeness": 0.5,
            },
            "confidence_factors": {"primary_weakness": "validation_error", "strengths": []},
            "recommendations": [
                "Erreur de validation - review humaine recommandée",
                "Vérifier configuration du système de validation",
                "Contacter support technique si problème persiste",
            ],
            "validation_metadata": {
                "validator_version": "2.8.0",
                "error": error_msg,
                "fallback": True,
                "answer_length": len(answer),
                "question_length": len(question),
            },
        }

    def get_session_statistics(self) -> dict:
        """
        Obtenir statistiques de la session courante

        Returns:
            Dictionnaire avec statistiques détaillées
        """
        current_time = datetime.now()
        session_duration = (current_time - self.session_stats["session_start"]).total_seconds()

        stats = self.session_stats.copy()
        stats.update(
            {
                "session_duration_seconds": round(session_duration),
                "validations_per_minute": (
                    round(stats["total_validations"] / (session_duration / 60), 2)
                    if session_duration > 0
                    else 0
                ),
                "acceptance_rate": round(
                    stats["accepted"] / max(stats["total_validations"], 1) * 100, 1
                ),
                "flag_rate": round(stats["flagged"] / max(stats["total_validations"], 1) * 100, 1),
                "rejection_rate": round(
                    stats["rejected"] / max(stats["total_validations"], 1) * 100, 1
                ),
                "current_time": current_time.isoformat(),
            }
        )

        return stats

    def reset_session_statistics(self):
        """Réinitialiser statistiques de session"""
        self.session_stats = {
            "total_validations": 0,
            "accepted": 0,
            "flagged": 0,
            "rejected": 0,
            "avg_confidence": 0.0,
            "session_start": datetime.now(),
        }
        logger.info("Statistiques de session réinitialisées")


def sanitize_for_json(obj):
    """
    Nettoie les types numpy/pandas pour la sérialisation JSON
    """
    import numpy as np

    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif hasattr(obj, "__dict__"):  # Dataclass ou object
        return {k: sanitize_for_json(v) for k, v in obj.__dict__.items()}
    else:
        return obj
