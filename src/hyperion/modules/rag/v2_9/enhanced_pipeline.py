"""
Enhanced RAG Pipeline for Hyperion v2.9

Pipeline RAG amélioré avec optimisations et nouvelles fonctionnalités.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration pour le pipeline RAG v2.9"""

    # Récupération
    max_chunks: int = 10
    min_similarity: float = 0.7
    chunk_overlap_ratio: float = 0.1

    # Génération
    max_tokens: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9

    # Optimisations v2.9
    enable_semantic_reranking: bool = True
    enable_context_compression: bool = True
    enable_progressive_retrieval: bool = True
    enable_answer_fusion: bool = True

    # Cache et performance
    enable_embedding_cache: bool = True
    max_concurrent_retrievals: int = 3
    retrieval_timeout: float = 30.0


@dataclass
class RetrievalResult:
    """Résultat de récupération enrichi"""

    content: str
    score: float
    source: str
    metadata: dict[str, Any]
    chunk_id: str

    # Nouvelles métriques v2.9
    semantic_score: float = 0.0
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    authority_score: float = 0.0
    combined_score: float = 0.0


@dataclass
class RAGResponse:
    """Réponse RAG enrichie v2.9"""

    answer: str
    sources: list[RetrievalResult]
    confidence: float
    processing_time: float

    # Métriques de qualité v2.9
    coherence_score: float = 0.0
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    factuality_score: float = 0.0

    # Métadonnées de traitement
    retrieval_stats: dict[str, Any] = field(default_factory=dict)
    generation_stats: dict[str, Any] = field(default_factory=dict)


class EnhancedRAGPipeline:
    """
    Pipeline RAG amélioré pour Hyperion v2.9

    Nouvelles fonctionnalités :
    - Récupération sémantique multi-étapes
    - Reranking intelligent des résultats
    - Compression de contexte pour optimiser les tokens
    - Fusion de réponses multiples
    - Cache d'embeddings pour performance
    - Retrieval progressif avec feedback
    """

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()

        # Composants du pipeline
        self.embeddings_cache: dict[str, np.ndarray] = {}
        self.response_cache: dict[str, RAGResponse] = {}

        # Stats et métriques
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_retrieval_time": 0.0,
            "avg_generation_time": 0.0,
        }

        # Threading pour optimisations
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_retrievals)

        logger.info("EnhancedRAGPipeline v2.9 initialisé")

    async def query(
        self, question: str, repo_context: str, user_context: dict | None = None, **_kwargs
    ) -> RAGResponse:
        """
        Traitement d'une requête RAG avec pipeline amélioré
        """
        start_time = time.time()

        try:
            # 1. Préparation et normalisation de la requête
            processed_query = await self._preprocess_query(question, user_context)

            # 2. Récupération progressive des chunks
            chunks = await self._progressive_retrieval(processed_query, repo_context)

            # 3. Reranking sémantique des résultats
            if self.config.enable_semantic_reranking:
                chunks = await self._semantic_reranking(chunks, processed_query)

            # 4. Compression de contexte
            if self.config.enable_context_compression:
                chunks = await self._compress_context(chunks, processed_query)

            # 5. Génération de la réponse
            if self.config.enable_answer_fusion:
                answer = await self._generate_fused_answer(chunks, processed_query)
            else:
                answer = await self._generate_single_answer(chunks, processed_query)

            # 6. Évaluation de la qualité
            quality_scores = await self._evaluate_response_quality(answer, chunks, question)

            # 7. Construction de la réponse finale
            processing_time = time.time() - start_time

            response = RAGResponse(
                answer=answer,
                sources=chunks,
                confidence=self._calculate_confidence(chunks, quality_scores),
                processing_time=processing_time,
                coherence_score=quality_scores.get("coherence", 0.0),
                relevance_score=quality_scores.get("relevance", 0.0),
                completeness_score=quality_scores.get("completeness", 0.0),
                factuality_score=quality_scores.get("factuality", 0.0),
                retrieval_stats=self._get_retrieval_stats(),
                generation_stats=self._get_generation_stats(),
            )

            # Mise à jour des statistiques
            self._update_stats(response)

            return response

        except Exception as e:
            logger.error(f"Erreur pipeline RAG: {e}")
            raise

    async def _preprocess_query(self, question: str, user_context: dict | None) -> str:
        """Prétraitement intelligent de la requête"""

        # Normalisation de base
        processed = question.strip().lower()

        # Expansion basée sur le contexte utilisateur
        if user_context:
            if "preferred_language" in user_context:
                # Adaptation linguistique
                pass

            if "expertise_level" in user_context:
                # Adaptation du niveau de détail
                if user_context["expertise_level"] == "beginner":
                    processed = f"Explain in simple terms: {processed}"
                elif user_context["expertise_level"] == "expert":
                    processed = f"Provide detailed technical information: {processed}"

        # Détection d'intention
        intent = self._detect_query_intent(processed)
        if intent:
            processed = f"[Intent: {intent}] {processed}"

        return processed

    def _detect_query_intent(self, query: str) -> str | None:
        """Détection simple d'intention de requête"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["how to", "how do", "comment"]):
            return "how_to"
        elif any(word in query_lower for word in ["what is", "qu'est-ce que", "define"]):
            return "definition"
        elif any(word in query_lower for word in ["why", "pourquoi"]):
            return "explanation"
        elif any(word in query_lower for word in ["show me", "example", "exemple"]):
            return "example"
        elif any(word in query_lower for word in ["compare", "difference", "vs"]):
            return "comparison"

        return None

    async def _progressive_retrieval(self, query: str, repo_context: str) -> list[RetrievalResult]:
        """Récupération progressive avec raffinement"""

        # Étape 1: Récupération initiale large
        initial_chunks = await self._retrieve_chunks(
            query, repo_context, limit=self.config.max_chunks * 2
        )

        # Étape 2: Filtrage par seuil de similarité
        filtered_chunks = [
            chunk for chunk in initial_chunks if chunk.score >= self.config.min_similarity
        ]

        # Étape 3: Si pas assez de résultats, récupération élargie
        if len(filtered_chunks) < self.config.max_chunks // 2:
            logger.debug("Récupération élargie nécessaire")
            expanded_query = await self._expand_query(query)
            additional_chunks = await self._retrieve_chunks(
                expanded_query, repo_context, limit=self.config.max_chunks
            )

            # Fusion et déduplication
            all_chunk_ids = {chunk.chunk_id for chunk in filtered_chunks}
            for chunk in additional_chunks:
                if (
                    chunk.chunk_id not in all_chunk_ids
                    and chunk.score >= self.config.min_similarity * 0.8
                ):
                    filtered_chunks.append(chunk)

        # Étape 4: Calcul des scores enrichis
        for chunk in filtered_chunks:
            chunk.semantic_score = await self._calculate_semantic_score(chunk, query)
            chunk.relevance_score = await self._calculate_relevance_score(chunk, query)
            chunk.freshness_score = self._calculate_freshness_score(chunk)
            chunk.authority_score = self._calculate_authority_score(chunk)
            chunk.combined_score = self._calculate_combined_score(chunk)

        # Tri par score combiné
        filtered_chunks.sort(key=lambda x: x.combined_score, reverse=True)

        return filtered_chunks[: self.config.max_chunks]

    async def _retrieve_chunks(
        self, query: str, repo_context: str, limit: int
    ) -> list[RetrievalResult]:
        """Récupération de base des chunks (simulation)"""
        # Simulation - à remplacer par vraie récupération Qdrant
        chunks = []

        for i in range(min(limit, 20)):
            chunk = RetrievalResult(
                content=f"Content chunk {i} for query: {query[:50]}...",
                score=0.9 - (i * 0.05),
                source=f"file_{i}.py",
                metadata={"lines": f"{i*10}-{i*10+20}", "repo": repo_context},
                chunk_id=f"chunk_{i}_{hash(query) % 1000}",
            )
            chunks.append(chunk)

        return chunks

    async def _expand_query(self, original_query: str) -> str:
        """Expansion de requête pour récupération élargie"""
        # Ajout de synonymes et termes connexes
        expansions = {
            "function": ["method", "procedure", "routine"],
            "error": ["exception", "bug", "issue", "problem"],
            "class": ["object", "type", "structure"],
            "variable": ["field", "attribute", "property"],
        }

        expanded_terms = []
        words = original_query.lower().split()

        for word in words:
            expanded_terms.append(word)
            if word in expansions:
                expanded_terms.extend(expansions[word][:2])  # Limiter l'expansion

        return " ".join(expanded_terms)

    async def _semantic_reranking(
        self, chunks: list[RetrievalResult], query: str
    ) -> list[RetrievalResult]:
        """Reranking sémantique des résultats"""

        # Calcul de scores sémantiques profonds
        for chunk in chunks:
            # Score de cohérence sémantique
            semantic_coherence = await self._calculate_semantic_coherence(chunk.content, query)

            # Score de spécificité contextuelle
            contextual_specificity = self._calculate_contextual_specificity(chunk.content, query)

            # Score de complétude informationnelle
            information_completeness = self._calculate_information_completeness(
                chunk.content, query
            )

            # Reranking basé sur la combinaison des scores
            chunk.semantic_score = (
                semantic_coherence * 0.4
                + contextual_specificity * 0.3
                + information_completeness * 0.3
            )

        # Tri par score sémantique
        chunks.sort(key=lambda x: x.semantic_score, reverse=True)
        return chunks

    async def _calculate_semantic_coherence(self, content: str, query: str) -> float:
        """Calcul de cohérence sémantique (simulation)"""
        # Simulation - en production utiliser des embeddings plus sophistiqués
        common_words = set(content.lower().split()) & set(query.lower().split())
        return min(len(common_words) / max(len(query.split()), 1), 1.0)

    def _calculate_contextual_specificity(self, content: str, _query: str) -> float:
        """Score de spécificité contextuelle"""
        # Bonus pour les termes techniques spécifiques
        technical_terms = ["class", "function", "method", "variable", "import", "return"]
        tech_score = sum(1 for term in technical_terms if term in content.lower()) / len(
            technical_terms
        )

        # Bonus pour la longueur appropriée
        length_score = 1.0 if 50 <= len(content) <= 500 else 0.5

        return (tech_score + length_score) / 2

    def _calculate_information_completeness(self, content: str, _query: str) -> float:
        """Score de complétude informationnelle"""
        # Analyse simple de complétude
        has_example = any(word in content.lower() for word in ["example", "e.g.", "for instance"])
        has_explanation = any(word in content.lower() for word in ["because", "since", "therefore"])
        has_context = len(content) > 100

        completeness = (
            (0.3 if has_example else 0)
            + (0.3 if has_explanation else 0)
            + (0.4 if has_context else 0)
        )

        return completeness

    async def _compress_context(
        self, chunks: list[RetrievalResult], query: str
    ) -> list[RetrievalResult]:
        """Compression intelligente du contexte"""
        if not self.config.enable_context_compression:
            return chunks

        compressed_chunks = []
        total_tokens = 0
        max_tokens = self.config.max_tokens // 2  # Réserver de l'espace pour la réponse

        for chunk in chunks:
            # Estimation des tokens (approximation)
            chunk_tokens = len(chunk.content.split()) * 1.3

            if total_tokens + chunk_tokens <= max_tokens:
                # Compression du contenu si nécessaire
                if len(chunk.content) > 300:
                    compressed_content = await self._compress_chunk_content(chunk.content, query)
                    chunk.content = compressed_content

                compressed_chunks.append(chunk)
                total_tokens += len(chunk.content.split()) * 1.3
            else:
                break

        logger.debug(f"Contexte compressé: {len(chunks)} -> {len(compressed_chunks)} chunks")
        return compressed_chunks

    async def _compress_chunk_content(self, content: str, query: str) -> str:
        """Compression d'un chunk individuel"""
        # Stratégie simple de compression
        sentences = content.split(".")

        # Garder les phrases les plus pertinentes
        relevant_sentences = []
        query_words = set(query.lower().split())

        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            relevance = len(query_words & sentence_words) / len(query_words) if query_words else 0

            if relevance > 0.2 or len(relevant_sentences) < 3:
                relevant_sentences.append(sentence.strip())

        return (
            ". ".join(relevant_sentences[:5]) + "." if relevant_sentences else content[:200] + "..."
        )

    async def _generate_fused_answer(self, chunks: list[RetrievalResult], query: str) -> str:
        """Génération avec fusion de réponses multiples"""

        # Générer plusieurs réponses candidates
        candidates = []

        # Candidat 1: Réponse basée sur le chunk le plus pertinent
        if chunks:
            primary_answer = await self._generate_answer_from_chunk(chunks[0], query)
            candidates.append(primary_answer)

        # Candidat 2: Réponse basée sur la fusion des top chunks
        if len(chunks) >= 3:
            fused_context = "\n".join([chunk.content for chunk in chunks[:3]])
            fused_answer = await self._generate_answer_from_context(fused_context, query)
            candidates.append(fused_answer)

        # Candidat 3: Réponse spécialisée selon l'intention
        intent_answer = await self._generate_intent_based_answer(chunks, query)
        if intent_answer:
            candidates.append(intent_answer)

        # Fusion des candidats
        if len(candidates) > 1:
            final_answer = await self._fuse_answer_candidates(candidates, query)
        else:
            final_answer = (
                candidates[0] if candidates else "Je n'ai pas pu générer une réponse satisfaisante."
            )

        return final_answer

    async def _generate_single_answer(self, chunks: list[RetrievalResult], query: str) -> str:
        """Génération de réponse simple"""
        if not chunks:
            return "Aucune information pertinente trouvée pour cette requête."

        # Utiliser le meilleur chunk
        primary_chunk = chunks[0]
        return await self._generate_answer_from_chunk(primary_chunk, query)

    async def _generate_answer_from_chunk(self, chunk: RetrievalResult, query: str) -> str:
        """Génération de réponse à partir d'un chunk"""
        # Simulation de génération - à remplacer par vraie LLM
        return f"Basé sur {chunk.source}: {chunk.content[:200]}... [Réponse générée pour: {query}]"

    async def _generate_answer_from_context(self, context: str, query: str) -> str:
        """Génération à partir d'un contexte fusionné"""
        # Simulation
        return f"Synthèse des sources multiples: {context[:150]}... [Réponse pour: {query}]"

    async def _generate_intent_based_answer(
        self, chunks: list[RetrievalResult], query: str
    ) -> str | None:
        """Génération spécialisée selon l'intention"""
        intent = self._detect_query_intent(query)

        if not intent or not chunks:
            return None

        if intent == "how_to":
            return f"Pour {query}: {chunks[0].content[:200]}..."
        elif intent == "definition":
            return f"Définition: {chunks[0].content[:150]}..."
        elif intent == "example":
            return f"Exemple: {chunks[0].content[:200]}..."

        return None

    async def _fuse_answer_candidates(self, candidates: list[str], _query: str) -> str:
        """Fusion intelligente des candidats de réponse"""
        # Stratégie simple de fusion
        if len(candidates) == 1:
            return candidates[0]

        # Prendre les parties les plus informatives de chaque candidat
        fused_parts = []

        for i, candidate in enumerate(candidates):
            # Prendre une partie de chaque candidat
            part_length = len(candidate) // len(candidates)
            start = i * part_length
            end = start + part_length if i < len(candidates) - 1 else len(candidate)

            part = candidate[start:end].strip()
            if part and part not in " ".join(fused_parts):
                fused_parts.append(part)

        return " ".join(fused_parts)

    async def _evaluate_response_quality(
        self, answer: str, chunks: list[RetrievalResult], original_query: str
    ) -> dict[str, float]:
        """Évaluation de la qualité de la réponse"""

        scores = {}

        # Score de cohérence
        scores["coherence"] = self._evaluate_coherence(answer)

        # Score de pertinence
        scores["relevance"] = self._evaluate_relevance(answer, original_query)

        # Score de complétude
        scores["completeness"] = self._evaluate_completeness(answer, original_query)

        # Score de factualité (basé sur les sources)
        scores["factuality"] = self._evaluate_factuality(answer, chunks)

        return scores

    def _evaluate_coherence(self, answer: str) -> float:
        """Évaluation de la cohérence de la réponse"""
        # Métriques simples de cohérence
        sentences = answer.split(".")
        if len(sentences) < 2:
            return 0.8

        # Vérifier la longueur appropriée
        length_score = 1.0 if 50 <= len(answer) <= 1000 else 0.6

        # Vérifier la structure
        structure_score = (
            1.0
            if any(
                word in answer.lower() for word in ["because", "therefore", "however", "moreover"]
            )
            else 0.7
        )

        return (length_score + structure_score) / 2

    def _evaluate_relevance(self, answer: str, query: str) -> float:
        """Évaluation de la pertinence"""
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        overlap = len(query_words & answer_words)
        relevance = overlap / len(query_words) if query_words else 0

        return min(relevance * 1.5, 1.0)  # Boost la pertinence

    def _evaluate_completeness(self, answer: str, query: str) -> float:
        """Évaluation de la complétude"""
        # Heuristiques simples
        has_explanation = len(answer) > 100
        has_details = any(word in answer.lower() for word in ["example", "specifically", "detail"])
        addresses_query = any(word in answer.lower() for word in query.lower().split())

        completeness = (
            (0.4 if has_explanation else 0)
            + (0.3 if has_details else 0)
            + (0.3 if addresses_query else 0)
        )

        return completeness

    def _evaluate_factuality(self, answer: str, chunks: list[RetrievalResult]) -> float:
        """Évaluation de la factualité basée sur les sources"""
        if not chunks:
            return 0.5

        # Score basé sur la qualité des sources
        source_quality = sum(chunk.combined_score for chunk in chunks) / len(chunks)

        # Bonus si la réponse cite ou référence les sources
        citation_bonus = 0.2 if any(chunk.source in answer for chunk in chunks) else 0

        return min(source_quality + citation_bonus, 1.0)

    def _calculate_confidence(
        self, chunks: list[RetrievalResult], quality_scores: dict[str, float]
    ) -> float:
        """Calcul de la confiance globale"""
        if not chunks:
            return 0.0

        # Confiance basée sur les sources
        source_confidence = sum(chunk.combined_score for chunk in chunks) / len(chunks)

        # Confiance basée sur la qualité
        quality_confidence = (
            sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.5
        )

        # Confiance combinée
        return source_confidence * 0.6 + quality_confidence * 0.4

    # Calcul des scores enrichis pour les chunks
    async def _calculate_semantic_score(self, chunk: RetrievalResult, query: str) -> float:
        """Score sémantique enrichi"""
        return await self._calculate_semantic_coherence(chunk.content, query)

    async def _calculate_relevance_score(self, chunk: RetrievalResult, query: str) -> float:
        """Score de pertinence contextuelle"""
        return self._evaluate_relevance(chunk.content, query)

    def _calculate_freshness_score(self, _chunk: RetrievalResult) -> float:
        """Score de fraîcheur (basé sur les métadonnées)"""
        # Simulation - en production utiliser les timestamps réels
        return 0.8  # Score par défaut

    def _calculate_authority_score(self, chunk: RetrievalResult) -> float:
        """Score d'autorité du chunk"""
        # Bonus pour certains types de fichiers
        source = chunk.source.lower()
        if source.endswith(".md"):
            return 0.9  # Documentation
        elif source.endswith(".py"):
            return 0.8  # Code source
        elif source.endswith(".test.py"):
            return 0.7  # Tests
        else:
            return 0.6

    def _calculate_combined_score(self, chunk: RetrievalResult) -> float:
        """Score combiné final"""
        return (
            chunk.score * 0.3  # Score de similarité de base
            + chunk.semantic_score * 0.25  # Score sémantique
            + chunk.relevance_score * 0.2  # Score de pertinence
            + chunk.freshness_score * 0.15  # Score de fraîcheur
            + chunk.authority_score * 0.1  # Score d'autorité
        )

    def _get_retrieval_stats(self) -> dict[str, Any]:
        """Statistiques de récupération"""
        return {
            "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["total_queries"], 1),
            "avg_retrieval_time": self.stats["avg_retrieval_time"],
        }

    def _get_generation_stats(self) -> dict[str, Any]:
        """Statistiques de génération"""
        return {"avg_generation_time": self.stats["avg_generation_time"]}

    def _update_stats(self, response: RAGResponse):
        """Mise à jour des statistiques"""
        self.stats["total_queries"] += 1

        # Mise à jour des moyennes (simple)
        if self.stats["avg_retrieval_time"] == 0:
            self.stats["avg_retrieval_time"] = (
                response.processing_time * 0.6
            )  # Estimation retrieval
        else:
            self.stats["avg_retrieval_time"] = (
                self.stats["avg_retrieval_time"] * 0.9 + response.processing_time * 0.6 * 0.1
            )

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Obtenir les statistiques du pipeline"""
        return dict(self.stats)

    def clear_caches(self):
        """Vider les caches"""
        self.embeddings_cache.clear()
        self.response_cache.clear()
        logger.info("Caches du pipeline RAG vidés")
