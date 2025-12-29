"""
Hyperion v2.9 - Response Optimizer
Optimisation des réponses RAG avec techniques avancées
"""

import logging
import re
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Résultat d'optimisation de réponse"""

    original_response: str
    optimized_response: str
    optimization_score: float
    techniques_applied: list[str]
    processing_time: float


@dataclass
class OptimizationConfig:
    """Configuration pour l'optimisation des réponses"""

    enable_clarity_enhancement: bool = True
    enable_conciseness: bool = True
    enable_coherence_check: bool = True
    enable_factual_verification: bool = True
    target_length_words: int | None = None
    readability_target: str = "intermediate"  # basic, intermediate, advanced


class ResponseOptimizer:
    """Optimiseur de réponses RAG"""

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.optimization_cache = {}

        # Patterns pour l'optimisation
        self.redundancy_patterns = [
            r"\b(\w+)\s+\1\b",  # Mots répétés
            r"(\b\w+\b)(?:\s+\w+){0,5}\s+\1",  # Répétitions proches
            r"\b(et|and|or|ou)\s+\1\b",  # Connecteurs répétés
        ]

        self.clarity_patterns = {
            "passive_voice": r"\b(was|were|is|are|been)\s+\w+ed\b",
            "filler_words": r"\b(actually|basically|literally|really|very|quite|rather)\b",
            "complex_phrases": r"\b(in order to|as a matter of fact|it should be noted that)\b",
        }

    async def optimize_response(
        self, response: str, context: dict | None = None
    ) -> OptimizationResult:
        """Optimise une réponse RAG"""
        start_time = time.time()

        # Vérifier le cache
        cache_key = f"{hash(response)}_{hash(str(context))}"
        if cache_key in self.optimization_cache:
            logger.debug("Réponse trouvée en cache")
            return self.optimization_cache[cache_key]

        original_response = response
        optimized_response = response
        techniques_applied = []

        try:
            # 1. Élimination des redondances
            if self.config.enable_conciseness:
                optimized_response, redundancy_removed = self._remove_redundancy(optimized_response)
                if redundancy_removed:
                    techniques_applied.append("redundancy_removal")

            # 2. Amélioration de la clarté
            if self.config.enable_clarity_enhancement:
                optimized_response, clarity_improved = self._enhance_clarity(optimized_response)
                if clarity_improved:
                    techniques_applied.append("clarity_enhancement")

            # 3. Vérification de cohérence
            if self.config.enable_coherence_check:
                optimized_response, coherence_improved = await self._improve_coherence(
                    optimized_response
                )
                if coherence_improved:
                    techniques_applied.append("coherence_improvement")

            # 4. Ajustement de longueur
            if self.config.target_length_words:
                optimized_response, length_adjusted = self._adjust_length(
                    optimized_response, self.config.target_length_words
                )
                if length_adjusted:
                    techniques_applied.append("length_adjustment")

            # 5. Optimisation de lisibilité
            optimized_response, readability_improved = self._improve_readability(
                optimized_response, self.config.readability_target
            )
            if readability_improved:
                techniques_applied.append("readability_improvement")

            # Calculer le score d'optimisation
            optimization_score = self._calculate_optimization_score(
                original_response, optimized_response
            )

            processing_time = time.time() - start_time

            result = OptimizationResult(
                original_response=original_response,
                optimized_response=optimized_response,
                optimization_score=optimization_score,
                techniques_applied=techniques_applied,
                processing_time=processing_time,
            )

            # Mettre en cache
            self.optimization_cache[cache_key] = result

            logger.info(
                f"Réponse optimisée: score={optimization_score:.2f}, techniques={len(techniques_applied)}"
            )
            return result

        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation: {e}")
            # Retourner la réponse originale en cas d'erreur
            return OptimizationResult(
                original_response=original_response,
                optimized_response=original_response,
                optimization_score=0.0,
                techniques_applied=[],
                processing_time=time.time() - start_time,
            )

    def _remove_redundancy(self, text: str) -> tuple[str, bool]:
        """Supprime les redondances du texte"""
        original_text = text

        for pattern in self.redundancy_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                text = re.sub(pattern, r"\1", text, flags=re.IGNORECASE)

        # Supprimer les phrases répétitives
        sentences = text.split(".")
        unique_sentences = []
        seen_sentences = set()

        for sentence in sentences:
            sentence_clean = sentence.strip().lower()
            if sentence_clean and sentence_clean not in seen_sentences:
                unique_sentences.append(sentence.strip())
                seen_sentences.add(sentence_clean)

        text = ". ".join(unique_sentences)
        if text and not text.endswith("."):
            text += "."

        return text, text != original_text

    def _enhance_clarity(self, text: str) -> tuple[str, bool]:
        """Améliore la clarté du texte"""
        original_text = text

        # Simplifier les phrases passives
        passive_matches = re.findall(self.clarity_patterns["passive_voice"], text)
        if passive_matches:
            # Conversion simple: remplacer par des formes actives
            text = re.sub(r"\bwas (\w+)ed by\b", r"\\1", text)
            text = re.sub(r"\bwere (\w+)ed by\b", r"\\1", text)

        # Supprimer les mots de remplissage
        for filler_word in ["actually", "basically", "literally", "really", "quite", "rather"]:
            text = re.sub(f"\\b{filler_word}\\s+", "", text, flags=re.IGNORECASE)

        # Simplifier les phrases complexes
        replacements = {
            "in order to": "to",
            "as a matter of fact": "in fact",
            "it should be noted that": "",
            "with regard to": "about",
            "in the event that": "if",
        }

        for complex_phrase, simple_phrase in replacements.items():
            text = re.sub(
                f"\\b{re.escape(complex_phrase)}\\b", simple_phrase, text, flags=re.IGNORECASE
            )

        # Nettoyer les espaces multiples
        text = re.sub(r"\s+", " ", text).strip()

        return text, text != original_text

    async def _improve_coherence(self, text: str) -> tuple[str, bool]:
        """Améliore la cohérence du texte"""
        original_text = text
        sentences = text.split(".")

        if len(sentences) < 2:
            return text, False

        # Ajouter des connecteurs logiques si nécessaire
        improved_sentences = [sentences[0]]

        for i, sentence in enumerate(sentences[1:], 1):
            sentence = sentence.strip()
            if not sentence:
                continue

            prev_sentence = sentences[i - 1].strip()

            # Détecter le type de relation et ajouter un connecteur si nécessaire
            connector = self._suggest_connector(prev_sentence, sentence)
            if connector:
                sentence = f"{connector} {sentence.lower()}"

            improved_sentences.append(sentence)

        improved_text = ". ".join(improved_sentences)
        if improved_text and not improved_text.endswith("."):
            improved_text += "."

        return improved_text, improved_text != original_text

    def _suggest_connector(self, prev_sentence: str, current_sentence: str) -> str | None:
        """Suggère un connecteur logique entre deux phrases"""
        prev_lower = prev_sentence.lower()
        current_lower = current_sentence.lower()

        # Règles simples pour les connecteurs
        if any(word in prev_lower for word in ["however", "but", "although"]) and not any(
            word in current_lower for word in ["therefore", "thus", "consequently"]
        ):
            return None  # Pas besoin d'autre connecteur

        if any(word in prev_lower for word in ["first", "initially", "begin"]):
            if any(word in current_lower for word in ["second", "then", "next", "additionally"]):
                return None
            return "Additionally"

        if any(word in current_lower for word in ["example", "instance", "specifically"]):
            return "For example"

        if any(word in current_lower for word in ["result", "conclusion", "therefore"]):
            return None  # Déjà explicite

        return None

    def _adjust_length(self, text: str, target_words: int) -> tuple[str, bool]:
        """Ajuste la longueur du texte"""
        words = text.split()
        current_length = len(words)

        if current_length <= target_words:
            return text, False

        # Réduire progressivement
        sentences = text.split(".")

        # D'abord, supprimer les phrases les moins importantes
        if len(sentences) > 1:
            # Garder les phrases avec le plus d'informations
            sentence_scores = []
            for sentence in sentences:
                if not sentence.strip():
                    continue
                score = self._calculate_sentence_importance(sentence)
                sentence_scores.append((sentence, score))

            # Trier par importance
            sentence_scores.sort(key=lambda x: x[1], reverse=True)

            # Garder les phrases jusqu'à atteindre la cible
            kept_sentences = []
            word_count = 0

            for sentence, _score in sentence_scores:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= target_words:
                    kept_sentences.append(sentence.strip())
                    word_count += sentence_words
                else:
                    break

            if kept_sentences:
                adjusted_text = ". ".join(kept_sentences)
                if not adjusted_text.endswith("."):
                    adjusted_text += "."
                return adjusted_text, True

        # Si une seule phrase, tronquer intelligemment
        words = words[:target_words]

        # Essayer de finir sur une phrase complète
        truncated_text = " ".join(words)
        last_period = truncated_text.rfind(".")
        if last_period > len(truncated_text) * 0.8:  # Si le dernier point est dans les 20% finaux
            truncated_text = truncated_text[: last_period + 1]
        else:
            truncated_text += "..."

        return truncated_text, True

    def _calculate_sentence_importance(self, sentence: str) -> float:
        """Calcule l'importance d'une phrase"""
        # Critères d'importance
        score = 0.0

        # Longueur (phrases moyennes sont souvent plus informatives)
        word_count = len(sentence.split())
        if 10 <= word_count <= 25:
            score += 1.0
        elif word_count < 5:
            score -= 0.5

        # Présence de mots-clés techniques
        technical_words = [
            "algorithm",
            "method",
            "technique",
            "approach",
            "implementation",
            "configuration",
        ]
        for word in technical_words:
            if word in sentence.lower():
                score += 0.5

        # Position (première phrase souvent importante)
        if sentence.strip().startswith(("The", "This", "It", "To")):
            score += 0.3

        return score

    def _improve_readability(self, text: str, target_level: str) -> tuple[str, bool]:
        """Améliore la lisibilité selon le niveau cible"""
        original_text = text

        if target_level == "basic":
            # Simplifier au maximum
            text = self._simplify_vocabulary(text)
            text = self._shorten_sentences(text)
        elif target_level == "intermediate":
            # Équilibre entre simplicité et précision
            text = self._moderate_simplification(text)
        # Pour "advanced", pas de simplification

        return text, text != original_text

    def _simplify_vocabulary(self, text: str) -> str:
        """Simplifie le vocabulaire"""
        replacements = {
            "utilize": "use",
            "implement": "use",
            "methodology": "method",
            "optimization": "improvement",
            "configuration": "setup",
            "subsequently": "then",
            "therefore": "so",
            "furthermore": "also",
            "consequently": "so",
        }

        for complex_word, simple_word in replacements.items():
            text = re.sub(f"\\b{complex_word}\\b", simple_word, text, flags=re.IGNORECASE)

        return text

    def _shorten_sentences(self, text: str) -> str:
        """Raccourcit les phrases longues"""
        sentences = text.split(".")
        shortened = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()
            if len(words) > 20:
                # Diviser en plusieurs phrases
                mid_point = len(words) // 2

                # Trouver un point de coupure naturel
                for i in range(mid_point - 5, mid_point + 5):
                    if i < len(words) and words[i].lower() in ["and", "but", "or", "so", "then"]:
                        first_part = " ".join(words[:i])
                        second_part = " ".join(words[i + 1 :])
                        shortened.extend([first_part, second_part])
                        break
                else:
                    shortened.append(sentence)
            else:
                shortened.append(sentence)

        return ". ".join(shortened) + ("." if not text.endswith(".") else "")

    def _moderate_simplification(self, text: str) -> str:
        """Simplification modérée"""
        # Remplacer seulement les termes les plus complexes
        replacements = {"subsequently": "then", "furthermore": "also", "consequently": "therefore"}

        for complex_word, simple_word in replacements.items():
            text = re.sub(f"\\b{complex_word}\\b", simple_word, text, flags=re.IGNORECASE)

        return text

    def _calculate_optimization_score(self, original: str, optimized: str) -> float:
        """Calcule un score d'optimisation"""
        if not original or not optimized:
            return 0.0

        # Facteurs de score
        length_improvement = self._calculate_length_score(original, optimized)
        clarity_improvement = self._calculate_clarity_score(original, optimized)

        # Score global (0-1)
        total_score = (length_improvement + clarity_improvement) / 2
        return min(1.0, max(0.0, total_score))

    def _calculate_length_score(self, original: str, optimized: str) -> float:
        """Score basé sur l'amélioration de longueur"""
        original_words = len(original.split())
        optimized_words = len(optimized.split())

        if original_words <= optimized_words:
            return 0.0

        reduction_ratio = (original_words - optimized_words) / original_words
        return min(1.0, reduction_ratio * 2)  # Score max à 50% de réduction

    def _calculate_clarity_score(self, original: str, optimized: str) -> float:
        """Score basé sur l'amélioration de clarté"""
        # Compter les améliorations de clarté
        improvements = 0

        # Moins de voix passive
        original_passive = len(re.findall(self.clarity_patterns["passive_voice"], original))
        optimized_passive = len(re.findall(self.clarity_patterns["passive_voice"], optimized))
        if optimized_passive < original_passive:
            improvements += 1

        # Moins de mots de remplissage
        original_fillers = len(re.findall(self.clarity_patterns["filler_words"], original))
        optimized_fillers = len(re.findall(self.clarity_patterns["filler_words"], optimized))
        if optimized_fillers < original_fillers:
            improvements += 1

        # Moins de phrases complexes
        original_complex = len(re.findall(self.clarity_patterns["complex_phrases"], original))
        optimized_complex = len(re.findall(self.clarity_patterns["complex_phrases"], optimized))
        if optimized_complex < original_complex:
            improvements += 1

        return improvements / 3.0  # Normaliser sur 3 critères


# Instance globale avec configuration par défaut
default_optimizer = ResponseOptimizer()
