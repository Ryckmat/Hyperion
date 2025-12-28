"""
Détecteur d'hallucinations multi-niveaux pour le système RAG Hyperion

Ce module détecte les hallucinations potentielles dans les réponses du LLM
en analysant plusieurs dimensions :
- Patterns de langage suspects (certitude artificielle)
- Contenu novel non présent dans les sources
- Cohérence sémantique avec le contexte
- Détails inventés (chiffres, dates)
"""

import logging
import re
from dataclasses import dataclass, field

from sentence_transformers import util

logger = logging.getLogger(__name__)


@dataclass
class HallucinationFlags:
    """Flags détectés lors de l'analyse d'hallucinations"""

    suspicious_patterns: list[str] = field(default_factory=list)
    novel_content_ratio: float = 0.0
    factual_inconsistencies: list[str] = field(default_factory=list)
    confidence_markers: list[str] = field(default_factory=list)
    invented_details: list[str] = field(default_factory=list)
    semantic_mismatch: bool = False


class HallucinationDetector:
    """
    Détecteur d'hallucinations multi-niveaux pour RAG

    Utilise plusieurs heuristiques pour identifier les réponses potentiellement
    hallucinées ou non fiables du modèle de langage.
    """

    def __init__(self, embedding_model):
        """
        Initialiser le détecteur

        Args:
            embedding_model: Modèle d'embedding pour calculer la similarité sémantique
        """
        self.embedding_model = embedding_model

        # Patterns suspects français et anglais
        self.suspicious_patterns = [
            # Français - Certitude artificielle
            r"selon mes sources",
            r"d'après mes connaissances",
            r"je pense que",
            r"il me semble",
            r"probablement",
            r"peut-être",
            r"je suppose",
            r"en général",
            r"il est possible que",
            r"dans ma compréhension",
            # Anglais - Artificial certainty
            r"based on my training",
            r"i think that",
            r"it seems",
            r"probably",
            r"might be",
            r"in my understanding",
            r"from what i know",
            r"as far as i know",
        ]

        # Stopwords français/anglais pour analyse contenu novel
        self.stopwords = {
            # Français
            "le",
            "la",
            "les",
            "un",
            "une",
            "des",
            "de",
            "du",
            "et",
            "ou",
            "mais",
            "donc",
            "car",
            "ni",
            "se",
            "ce",
            "il",
            "elle",
            "on",
            "nous",
            "vous",
            "ils",
            "elles",
            "je",
            "tu",
            "mon",
            "ton",
            "son",
            "ma",
            "ta",
            "sa",
            "mes",
            "tes",
            "ses",
            "notre",
            "votre",
            "leur",
            "dans",
            "sur",
            "avec",
            "pour",
            "par",
            "sans",
            "sous",
            "vers",
            "chez",
            "entre",
            "contre",
            "depuis",
            "pendant",
            "selon",
            "après",
            "avant",
            "jusque",
            # Anglais
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "this",
            "that",
            "these",
            "those",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
        }

    def detect(self, answer: str, context_chunks: list[str], question: str) -> dict:  # noqa: ARG002
        """
        Analyser hallucinations potentielles dans une réponse

        Args:
            answer: Réponse générée par le LLM
            context_chunks: Chunks de contexte utilisés pour générer la réponse
            question: Question originale

        Returns:
            Dictionnaire avec résultats de l'analyse d'hallucinations
        """
        if not answer or not answer.strip():
            return {
                "is_hallucination": True,
                "confidence": 0.0,
                "severity": "CRITICAL",
                "flags": HallucinationFlags(),
                "recommendations": ["Réponse vide détectée"],
            }

        try:
            flags = HallucinationFlags()
            confidence = 1.0

            # 1. Détecter patterns suspects
            flags.suspicious_patterns = self._detect_suspicious_patterns(answer)
            confidence -= len(flags.suspicious_patterns) * 0.1

            # 2. Analyser contenu novel (hors contexte)
            flags.novel_content_ratio = self._analyze_novel_content(answer, context_chunks)
            confidence -= flags.novel_content_ratio * 0.3

            # 3. Vérifier cohérence sémantique
            semantic_consistency = self._check_semantic_consistency(answer, context_chunks)
            if semantic_consistency < 0.4:  # Seuil de cohérence sémantique
                flags.semantic_mismatch = True
                confidence -= (1.0 - semantic_consistency) * 0.4

            # 4. Détecter détails inventés
            flags.invented_details = self._detect_invented_details(answer, context_chunks)
            confidence -= len(flags.invented_details) * 0.15

            # 5. Analyser proportion de longueur
            length_inconsistency = self._check_length_consistency(answer, context_chunks)
            if length_inconsistency:
                flags.factual_inconsistencies.append(length_inconsistency)
                confidence -= 0.2

            # 6. Vérifier marqueurs d'incertitude vs certitude
            uncertainty_score = self._check_uncertainty_markers(answer)
            confidence += uncertainty_score * 0.1  # Bonus pour marqueurs d'incertitude appropriés

            # Clamp confidence entre 0 et 1
            confidence = max(0.0, min(1.0, confidence))

            return {
                "is_hallucination": confidence < 0.6,
                "confidence": round(confidence, 3),
                "flags": flags,
                "severity": self._get_severity(confidence),
                "recommendations": self._get_recommendations(confidence, flags),
                "semantic_consistency": round(semantic_consistency, 3),
                "analysis_metadata": {
                    "detector_version": "2.8.0",
                    "context_chunks_analyzed": len(context_chunks),
                    "answer_length": len(answer),
                },
            }

        except Exception as e:
            logger.error(f"Erreur détection hallucination: {e}")
            return {
                "is_hallucination": False,  # Failsafe: ne pas rejeter en cas d'erreur
                "confidence": 0.5,
                "severity": "UNKNOWN",
                "flags": HallucinationFlags(),
                "recommendations": ["Erreur analyse - validation manuelle recommandée"],
                "error": str(e),
            }

    def _detect_suspicious_patterns(self, text: str) -> list[str]:
        """Détecter patterns de langage suspects"""
        found = []
        text_lower = text.lower()

        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower):
                found.append(pattern)

        return found

    def _analyze_novel_content(self, answer: str, context_chunks: list[str]) -> float:
        """
        Calculer le ratio de contenu non présent dans les sources

        Returns:
            Float entre 0.0 et 1.0 (0.0 = tout est dans le contexte, 1.0 = rien n'est dans le contexte)
        """
        if not context_chunks:
            return 1.0

        # Extraire mots significatifs de la réponse
        answer_words = set(re.findall(r"\w+", answer.lower()))

        # Extraire mots du contexte combiné
        context_text = " ".join(context_chunks).lower()
        context_words = set(re.findall(r"\w+", context_text))

        # Retirer stopwords
        significant_answer_words = answer_words - self.stopwords
        significant_context_words = context_words - self.stopwords

        # Calculer ratio de mots novel
        if len(significant_answer_words) == 0:
            return 0.0

        novel_words = significant_answer_words - significant_context_words
        novel_ratio = len(novel_words) / len(significant_answer_words)

        logger.debug(
            f"Novel content analysis: {len(novel_words)}/{len(significant_answer_words)} = {novel_ratio:.3f}"
        )
        return novel_ratio

    def _check_semantic_consistency(self, answer: str, context_chunks: list[str]) -> float:
        """
        Vérifier cohérence sémantique avec embedding similarity

        Returns:
            Float entre 0.0 et 1.0 (1.0 = parfaitement cohérent)
        """
        if not context_chunks:
            return 0.0

        try:
            # Générer embeddings
            answer_embedding = self.embedding_model.encode([answer])
            context_embeddings = self.embedding_model.encode(context_chunks)

            # Calculer similarité avec chaque chunk
            similarities = util.cos_sim(answer_embedding, context_embeddings)[0]

            # Prendre la similarité maximale
            max_similarity = float(similarities.max())

            logger.debug(f"Semantic consistency: max_sim={max_similarity:.3f}")
            return max_similarity

        except Exception as e:
            logger.warning(f"Erreur calcul similarité sémantique: {e}")
            return 0.5  # Score neutre en cas d'erreur

    def _detect_invented_details(self, answer: str, context_chunks: list[str]) -> list[str]:
        """Détecter chiffres/dates/détails spécifiques non présents dans contexte"""
        invented = []

        # Extraire patterns spécifiques de la réponse
        answer_numbers = set(re.findall(r"\b\d+\b", answer))
        answer_dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b", answer))
        answer_emails = set(
            re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", answer)
        )
        answer_urls = set(re.findall(r"https?://[^\s]+", answer))

        # Extraire du contexte combiné
        context_text = " ".join(context_chunks)
        context_numbers = set(re.findall(r"\b\d+\b", context_text))
        context_dates = set(
            re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b", context_text)
        )
        context_emails = set(
            re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", context_text)
        )
        context_urls = set(re.findall(r"https?://[^\s]+", context_text))

        # Identifier détails inventés
        invented_numbers = answer_numbers - context_numbers
        if invented_numbers:
            invented.append(f"Chiffres inventés: {', '.join(list(invented_numbers)[:3])}...")

        invented_dates = answer_dates - context_dates
        if invented_dates:
            invented.append(f"Dates inventées: {', '.join(list(invented_dates)[:2])}...")

        invented_emails = answer_emails - context_emails
        if invented_emails:
            invented.append(f"Emails inventés: {len(invented_emails)} email(s)")

        invented_urls = answer_urls - context_urls
        if invented_urls:
            invented.append(f"URLs inventées: {len(invented_urls)} URL(s)")

        return invented

    def _check_length_consistency(self, answer: str, context_chunks: list[str]) -> str | None:
        """Vérifier cohérence de longueur réponse vs contexte"""
        if not context_chunks:
            return None

        total_context_length = sum(len(chunk) for chunk in context_chunks)
        answer_length = len(answer)

        # Réponse anormalement plus longue que le contexte
        if answer_length > total_context_length * 1.5:
            return f"Réponse trop longue vs contexte ({answer_length} > {total_context_length * 1.5:.0f})"

        return None

    def _check_uncertainty_markers(self, answer: str) -> float:
        """
        Vérifier présence appropriée de marqueurs d'incertitude

        Returns:
            Float entre 0.0 et 1.0 (1.0 = marqueurs appropriés présents)
        """
        appropriate_uncertainty = [
            r"selon le code",
            r"d'après l'analyse",
            r"dans ce repository",
            r"basé sur les sources",
            r"selon les données",
            r"based on the code",
            r"according to the analysis",
        ]

        score = 0.0
        text_lower = answer.lower()

        for pattern in appropriate_uncertainty:
            if re.search(pattern, text_lower):
                score += 0.3

        return min(1.0, score)

    def _get_severity(self, confidence: float) -> str:
        """Déterminer niveau de sévérité selon confidence"""
        if confidence < 0.2:
            return "CRITICAL"
        elif confidence < 0.4:
            return "HIGH"
        elif confidence < 0.6:
            return "MEDIUM"
        elif confidence < 0.8:
            return "LOW"
        else:
            return "MINIMAL"

    def _get_recommendations(self, confidence: float, flags: HallucinationFlags) -> list[str]:
        """Générer recommandations d'amélioration basées sur l'analyse"""
        recommendations = []

        if confidence < 0.3:
            recommendations.append("Rejeter la réponse - validation humaine requise")
        elif confidence < 0.6:
            recommendations.append("Flaguer pour review humaine")

        if flags.novel_content_ratio > 0.5:
            recommendations.append("Augmenter nombre de chunks RAG récupérés")
            recommendations.append("Vérifier pertinence des sources sélectionnées")

        if flags.suspicious_patterns:
            recommendations.append(
                "Ajuster prompt système pour éviter marqueurs de certitude artificielle"
            )

        if flags.invented_details:
            recommendations.append("Renforcer instructions de fidélité aux sources")
            recommendations.append("Ajouter validation factuelle post-génération")

        if flags.semantic_mismatch:
            recommendations.append("Améliorer sélection de contexte pertinent")
            recommendations.append("Vérifier cohérence thématique question-sources")

        if not recommendations:
            recommendations.append("Qualité acceptable - monitoring continu")

        return recommendations
