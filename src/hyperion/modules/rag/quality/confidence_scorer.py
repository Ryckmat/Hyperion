"""
Système de scoring de confiance pour les réponses RAG

Ce module calcule un score de confiance global en combinant plusieurs facteurs :
- Score d'hallucination
- Qualité des sources
- Pertinence sémantique
- Complétude de la réponse
"""

from typing import Dict, List, Optional
import logging
import re
import numpy as np

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Calculateur de score de confiance global pour réponses RAG

    Combine plusieurs métriques pour produire un score de confiance final
    et des recommandations d'action.
    """

    def __init__(self):
        """Initialiser le scorer avec poids par défaut"""
        # Poids des différents facteurs (doivent sommer à 1.0)
        self.weights = {
            "hallucination": 0.4,        # Le plus critique
            "source_quality": 0.25,      # Qualité des sources récupérées
            "semantic_relevance": 0.2,   # Pertinence sémantique question-réponse
            "response_completeness": 0.15 # Complétude et structure de la réponse
        }

        # Seuils de qualité
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.8,
            "fair": 0.7,
            "poor": 0.5,
            "unacceptable": 0.0
        }

    def compute_confidence(self,
                          hallucination_result: Dict,
                          source_scores: List[float],
                          question: str,
                          answer: str,
                          processing_metadata: Optional[Dict] = None) -> Dict:
        """
        Calculer score de confiance final en combinant tous les facteurs

        Args:
            hallucination_result: Résultat du détecteur d'hallucinations
            source_scores: Scores de similarité des sources utilisées
            question: Question originale
            answer: Réponse générée
            processing_metadata: Métadonnées de traitement (optionnel)

        Returns:
            Dictionnaire avec score final et breakdown détaillé
        """
        try:
            # 1. Score hallucination (déjà calculé)
            hallucination_score = hallucination_result.get("confidence", 0.5)

            # 2. Score qualité des sources
            source_quality_score = self._calculate_source_quality(source_scores)

            # 3. Score pertinence sémantique
            relevance_score = self._calculate_semantic_relevance(question, answer)

            # 4. Score complétude de la réponse
            completeness_score = self._calculate_response_completeness(answer, question)

            # 5. Score final pondéré
            final_confidence = (
                self.weights["hallucination"] * hallucination_score +
                self.weights["source_quality"] * source_quality_score +
                self.weights["semantic_relevance"] * relevance_score +
                self.weights["response_completeness"] * completeness_score
            )

            # 6. Ajustements contextuels
            final_confidence = self._apply_contextual_adjustments(
                final_confidence, hallucination_result, source_scores, answer
            )

            # 7. Grade et recommandations
            quality_grade = self._get_quality_grade(final_confidence)
            action_recommendation = self._determine_action(final_confidence, hallucination_result)

            return {
                "final_confidence": round(final_confidence, 3),
                "quality_grade": quality_grade,
                "action": action_recommendation,
                "should_flag": final_confidence < self.quality_thresholds["fair"],
                "breakdown": {
                    "hallucination": round(hallucination_score, 3),
                    "source_quality": round(source_quality_score, 3),
                    "semantic_relevance": round(relevance_score, 3),
                    "response_completeness": round(completeness_score, 3)
                },
                "confidence_factors": {
                    "primary_weakness": self._identify_primary_weakness(
                        hallucination_score, source_quality_score,
                        relevance_score, completeness_score
                    ),
                    "strengths": self._identify_strengths(
                        hallucination_score, source_quality_score,
                        relevance_score, completeness_score
                    )
                },
                "metadata": {
                    "scorer_version": "2.8.0",
                    "weights_used": self.weights.copy(),
                    "num_sources": len(source_scores),
                    "processing_metadata": processing_metadata or {}
                }
            }

        except Exception as e:
            logger.error(f"Erreur calcul confidence: {e}")
            return self._get_error_fallback_score(str(e))

    def _calculate_source_quality(self, source_scores: List[float]) -> float:
        """
        Calculer score qualité des sources basé sur scores de similarité

        Args:
            source_scores: Liste des scores de similarité Qdrant

        Returns:
            Score entre 0.0 et 1.0
        """
        if not source_scores:
            logger.warning("Aucune source disponible pour calcul qualité")
            return 0.0

        # Moyenne pondérée avec bonus pour scores élevés
        scores_array = np.array(source_scores)

        # Score de base : moyenne
        base_score = np.mean(scores_array)

        # Bonus si score max > 0.8 (source très pertinente)
        max_score = np.max(scores_array)
        high_quality_bonus = 0.1 if max_score > 0.8 else 0.0

        # Pénalité si tous les scores < 0.5 (sources peu pertinentes)
        low_quality_penalty = 0.2 if np.all(scores_array < 0.5) else 0.0

        # Bonus diversité si plusieurs sources de bonne qualité
        diversity_bonus = 0.05 if len([s for s in source_scores if s > 0.6]) > 1 else 0.0

        final_score = base_score + high_quality_bonus + diversity_bonus - low_quality_penalty

        return max(0.0, min(1.0, final_score))

    def _calculate_semantic_relevance(self, question: str, answer: str) -> float:
        """
        Calculer score pertinence sémantique question-réponse

        Args:
            question: Question originale
            answer: Réponse générée

        Returns:
            Score entre 0.0 et 1.0
        """
        if not question or not answer:
            return 0.0

        question = question.strip()
        answer = answer.strip()

        # 1. Analyse mots-clés communs
        question_words = set(re.findall(r'\w+', question.lower()))
        answer_words = set(re.findall(r'\w+', answer.lower()))

        # Retirer stopwords basiques
        stopwords = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'et', 'ou', 'the', 'a', 'an', 'and', 'or'}
        question_words -= stopwords
        answer_words -= stopwords

        if len(question_words) == 0:
            keyword_overlap = 0.0
        else:
            common_words = question_words & answer_words
            keyword_overlap = len(common_words) / len(question_words)

        # 2. Analyse ratio de longueur (éviter réponses trop courtes/longues)
        length_ratio = len(answer) / max(len(question), 1)

        if length_ratio < 0.3:  # Réponse très courte
            length_score = 0.4
        elif length_ratio > 8:   # Réponse très longue
            length_score = 0.6
        elif 0.8 <= length_ratio <= 4:  # Longueur appropriée
            length_score = 1.0
        else:
            length_score = 0.8

        # 3. Détection de réponse directe vs tangentielle
        directness_score = self._assess_directness(question, answer)

        # Score final pondéré
        relevance_score = (
            0.5 * keyword_overlap +
            0.3 * length_score +
            0.2 * directness_score
        )

        return max(0.0, min(1.0, relevance_score))

    def _calculate_response_completeness(self, answer: str, question: str) -> float:
        """
        Évaluer complétude et structure de la réponse

        Args:
            answer: Réponse générée
            question: Question pour contexte

        Returns:
            Score entre 0.0 et 1.0
        """
        if not answer or not answer.strip():
            return 0.0

        answer = answer.strip()

        # 1. Score longueur appropriée
        length_score = self._assess_response_length(answer)

        # 2. Score structure (phrases complètes, ponctuation)
        structure_score = self._assess_response_structure(answer)

        # 3. Score informatif vs vague
        informativeness_score = self._assess_informativeness(answer)

        # 4. Bonus pour citations/références aux sources
        citation_bonus = 0.1 if self._has_source_references(answer) else 0.0

        # Score final
        completeness = (
            0.4 * length_score +
            0.3 * structure_score +
            0.3 * informativeness_score +
            citation_bonus
        )

        return max(0.0, min(1.0, completeness))

    def _assess_directness(self, question: str, answer: str) -> float:
        """Évaluer si la réponse répond directement à la question"""
        # Patterns de questions spécifiques
        question_patterns = {
            r'\bcombien\b|\bhow many\b|\bhow much\b': 'quantitative',
            r'\bquoi\b|\bque\b|\bwhat\b': 'descriptive',
            r'\bcomment\b|\bhow\b': 'procedural',
            r'\bpourquoi\b|\bwhy\b': 'causal',
            r'\boù\b|\bwhere\b': 'locative',
            r'\bquand\b|\bwhen\b': 'temporal'
        }

        question_type = 'general'
        for pattern, qtype in question_patterns.items():
            if re.search(pattern, question.lower()):
                question_type = qtype
                break

        # Vérifier si la réponse contient des éléments appropriés
        directness_indicators = {
            'quantitative': [r'\b\d+\b', r'\bfichiers?\b', r'\blignes?\b'],
            'descriptive': [r'\best\b', r'\butilise\b', r'\bcontient\b'],
            'procedural': [r'\bpour\b', r'\bavec\b', r'\ben utilisant\b'],
            'causal': [r'\bcar\b', r'\bparce que\b', r'\bgrâce à\b'],
            'locative': [r'\bdans\b', r'\bsous\b', r'\brépertoire\b'],
            'temporal': [r'\bquand\b', r'\blors\b', r'\bpendant\b']
        }

        if question_type in directness_indicators:
            indicators = directness_indicators[question_type]
            matches = sum(1 for pattern in indicators if re.search(pattern, answer.lower()))
            return min(1.0, matches * 0.4)

        return 0.6  # Score neutre pour questions générales

    def _assess_response_length(self, answer: str) -> float:
        """Évaluer appropriété de la longueur de réponse"""
        length = len(answer)

        if length < 10:
            return 0.1  # Trop courte
        elif length < 30:
            return 0.5  # Courte mais acceptable
        elif length <= 200:
            return 1.0  # Longueur idéale pour Hyperion
        elif length <= 400:
            return 0.9  # Un peu longue mais OK
        else:
            return 0.6  # Trop longue pour contexte RAG

    def _assess_response_structure(self, answer: str) -> float:
        """Évaluer structure grammaticale de la réponse"""
        # Vérifications basiques de structure
        has_punctuation = bool(re.search(r'[.!?]', answer))
        has_capital_start = answer[0].isupper() if answer else False
        not_all_caps = answer != answer.upper()
        proper_spacing = not bool(re.search(r'\w{50,}', answer))  # Pas de mots trop longs

        structure_elements = [has_punctuation, has_capital_start, not_all_caps, proper_spacing]
        return sum(structure_elements) / len(structure_elements)

    def _assess_informativeness(self, answer: str) -> float:
        """Évaluer caractère informatif vs vague de la réponse"""
        # Patterns de réponses vagues à pénaliser
        vague_patterns = [
            r'\bje ne sais pas\b',
            r'\bpas d\'information\b',
            r'\bimpossible de dire\b',
            r'\bdifficile à déterminer\b',
            r'\bvariable\b',
            r'\bdépend\b.*\bdépend\b'  # "ça dépend" répété
        ]

        # Patterns informatifs à valoriser
        informative_patterns = [
            r'\b\d+\b',  # Chiffres spécifiques
            r'\bfichier\b|\blignes?\b|\bfonctions?\b',  # Éléments techniques spécifiques
            r'\bprincipal\b|\bmajeur\b|\bprincipal\b',  # Qualificatifs précis
            r'\banalyse\b|\bcode\b|\brepository\b'  # Vocabulaire technique approprié
        ]

        answer_lower = answer.lower()

        # Pénalités pour contenu vague
        vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, answer_lower))
        vague_penalty = min(0.5, vague_count * 0.2)

        # Bonus pour contenu informatif
        informative_count = sum(1 for pattern in informative_patterns if re.search(pattern, answer_lower))
        informative_bonus = min(0.4, informative_count * 0.1)

        base_score = 0.6
        return max(0.0, min(1.0, base_score - vague_penalty + informative_bonus))

    def _has_source_references(self, answer: str) -> bool:
        """Vérifier si la réponse fait référence aux sources"""
        source_refs = [
            r'\bselon\b.*\banalyse\b',
            r'\bd\'après\b.*\bcode\b',
            r'\bdans le repository\b',
            r'\bbasé sur\b',
            r'\bd\'après les données\b'
        ]

        return any(re.search(pattern, answer.lower()) for pattern in source_refs)

    def _apply_contextual_adjustments(self, base_confidence: float,
                                    hallucination_result: Dict,
                                    source_scores: List[float],
                                    answer: str) -> float:
        """Appliquer ajustements contextuels au score de confiance"""
        adjusted = base_confidence

        # Pénalité sévère si hallucination critique détectée
        if hallucination_result.get("severity") == "CRITICAL":
            adjusted *= 0.5

        # Bonus si sources multiples de haute qualité
        if len(source_scores) > 1 and np.mean(source_scores) > 0.7:
            adjusted += 0.05

        # Pénalité si réponse très courte et sources de qualité
        if len(answer) < 20 and source_scores and np.max(source_scores) > 0.8:
            adjusted -= 0.1

        return max(0.0, min(1.0, adjusted))

    def _identify_primary_weakness(self, hall_score: float, source_score: float,
                                  rel_score: float, comp_score: float) -> str:
        """Identifier la faiblesse principale pour recommandations ciblées"""
        scores = {
            "hallucination": hall_score,
            "source_quality": source_score,
            "semantic_relevance": rel_score,
            "response_completeness": comp_score
        }

        return min(scores.items(), key=lambda x: x[1])[0]

    def _identify_strengths(self, hall_score: float, source_score: float,
                           rel_score: float, comp_score: float) -> List[str]:
        """Identifier les points forts de la réponse"""
        strengths = []

        if hall_score > 0.8:
            strengths.append("low_hallucination_risk")
        if source_score > 0.8:
            strengths.append("high_quality_sources")
        if rel_score > 0.8:
            strengths.append("semantically_relevant")
        if comp_score > 0.8:
            strengths.append("well_structured_response")

        return strengths

    def _get_quality_grade(self, confidence: float) -> str:
        """Convertir score numérique en grade lisible"""
        for grade, threshold in sorted(self.quality_thresholds.items(), key=lambda x: x[1], reverse=True):
            if confidence >= threshold:
                return grade.upper()
        return "UNACCEPTABLE"

    def _determine_action(self, confidence: float, hallucination_result: Dict) -> str:
        """Déterminer l'action recommandée basée sur le score et l'analyse"""
        # Rejet immédiat si hallucination critique
        if hallucination_result.get("severity") == "CRITICAL":
            return "reject"

        # Basé sur seuils de confiance
        if confidence < 0.3:
            return "reject"
        elif confidence < 0.7:
            return "flag"
        else:
            return "accept"

    def _get_error_fallback_score(self, error_msg: str) -> Dict:
        """Score de fallback en cas d'erreur de calcul"""
        return {
            "final_confidence": 0.5,
            "quality_grade": "UNKNOWN",
            "action": "flag",
            "should_flag": True,
            "breakdown": {
                "hallucination": 0.5,
                "source_quality": 0.5,
                "semantic_relevance": 0.5,
                "response_completeness": 0.5
            },
            "confidence_factors": {
                "primary_weakness": "calculation_error",
                "strengths": []
            },
            "metadata": {
                "scorer_version": "2.8.0",
                "error": error_msg,
                "fallback": True
            }
        }