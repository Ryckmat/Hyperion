"""Query engine pour RAG avec validation qualité intégrée."""

import os
import time

from langchain_ollama import OllamaLLM
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer

from hyperion.modules.rag.config import (
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    LLM_TOP_K,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    QDRANT_COLLECTION,
    QDRANT_HOST,
    QDRANT_PORT,
    QUERY_PROMPT_TEMPLATE,
)

# Import du système de validation qualité v2.8
try:
    from hyperion.modules.rag.quality.response_validator import ResponseValidator

    VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Validation qualité non disponible: {e}")
    VALIDATION_AVAILABLE = False


class RAGQueryEngine:
    """
    Moteur de requêtes RAG.

    Process :
    1. Question → embedding
    2. Recherche top-k similaires dans Qdrant
    3. Assembly contexte
    4. Prompt au LLM Ollama
    5. Retour réponse formatée
    """

    def __init__(
        self,
        qdrant_host: str = QDRANT_HOST,
        qdrant_port: int = QDRANT_PORT,
        collection_name: str = QDRANT_COLLECTION,
        ollama_base_url: str = OLLAMA_BASE_URL,
        ollama_model: str = OLLAMA_MODEL,
    ):
        """Initialise le query engine avec validation qualité v2.8."""
        # Qdrant client
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name

        # Modèle embeddings avec fallback automatique
        print("📥 Chargement modèle embeddings...")
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
            print(f"✅ Embeddings prêts ({EMBEDDING_DEVICE})")
        except Exception as e:
            if EMBEDDING_DEVICE == "cuda":
                print(f"⚠️ Erreur GPU embeddings: {e}")
                print("🔄 Fallback automatique vers CPU...")
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
                print("✅ Embeddings prêts (cpu - fallback)")
            else:
                raise

        # LLM Ollama (optimisé)
        print(f"🤖 Connexion à Ollama ({ollama_model})...")
        self.llm = OllamaLLM(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=LLM_TEMPERATURE,
            num_predict=LLM_MAX_TOKENS,
            timeout=LLM_TIMEOUT,  # Timeout pour éviter attentes longues
        )
        print("✅ LLM prêt")

        # Système de validation qualité v2.8
        self.enable_validation = os.getenv("ENABLE_RESPONSE_VALIDATION", "true").lower() == "true"
        self.validation_mode = os.getenv("VALIDATION_MODE", "flag")  # "flag" ou "reject"

        if self.enable_validation and VALIDATION_AVAILABLE:
            print("🔍 Initialisation validation qualité v2.8...")
            try:
                self.response_validator = ResponseValidator(self.embedding_model)
                print("✅ Validation qualité prête")
            except Exception as e:
                print(f"⚠️ Erreur init validation: {e}")
                self.enable_validation = False
                self.response_validator = None
        else:
            if not VALIDATION_AVAILABLE:
                print("⚠️ Module validation qualité non disponible")
            else:
                print("ℹ️ Validation qualité désactivée (ENABLE_RESPONSE_VALIDATION=false)")
            self.response_validator = None

    def query(self, question: str, repo_filter: str | None = None, top_k: int = LLM_TOP_K) -> dict:
        """
        Répond à une question via RAG avec validation qualité v2.8.

        Args:
            question: Question en langage naturel
            repo_filter: Filtrer sur un repo spécifique (optionnel)
            top_k: Nombre de chunks à récupérer

        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "question": str,
                "processing_time": float,
                "quality": Dict (si validation activée)
            }
        """
        start_time = time.time()

        try:
            # 1. Générer embedding de la question (optimisé)
            question_embedding = self.embedding_model.encode(
                question,
                convert_to_numpy=True,
                show_progress_bar=False,  # Désactiver pour vitesse
            )

            # 2. Recherche dans Qdrant (ultra-optimisé)
            search_filter = None
            if repo_filter:
                search_filter = Filter(
                    must=[FieldCondition(key="repo", match=MatchValue(value=repo_filter))]
                )

            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=question_embedding.tolist(),
                limit=min(top_k, 1),  # Un seul chunk pour vitesse maximum
                query_filter=search_filter,
                timeout=1,  # Timeout Qdrant strict
            ).points

            # 3. Assembler contexte (optimisé, texte réduit)
            context_parts = []
            full_context_chunks = []  # Chunks complets pour validation qualité
            sources = []
            source_scores = []

            for result in search_results:
                payload = result.payload

                # Texte complet pour validation qualité
                full_text = payload["text"]
                full_context_chunks.append(full_text)
                source_scores.append(result.score)

                # Ultra-limitation pour vitesse maximale (comme avant)
                display_text = full_text
                if len(display_text) > 100:  # Extrême réduction 200→100
                    display_text = display_text[:100] + "..."

                context_parts.append(display_text)
                sources.append(
                    {
                        "repo": payload["repo"],
                        "section": payload["section"],
                        "score": result.score,
                        "text": display_text[:30] + "...",  # Preview ultra réduit 50→30
                    }
                )

            context = "\n\n---\n\n".join(context_parts)

            # 4. Construire prompt (optimisé)
            full_prompt = QUERY_PROMPT_TEMPLATE.format(context=context, question=question)

            # 5. Appeler LLM avec timeout
            answer = self.llm.invoke(full_prompt).strip()

            processing_time = time.time() - start_time

            # 6. NOUVEAU: Validation qualité v2.8
            validation_result = None
            if self.enable_validation and self.response_validator:
                try:
                    validation_result = self.response_validator.validate_response(
                        answer=answer,
                        question=question,
                        context_chunks=full_context_chunks,
                        source_scores=source_scores,
                        processing_time=processing_time,
                    )

                    # Traitement selon mode validation
                    if validation_result["action"] == "reject" and self.validation_mode == "reject":
                        original_answer = answer
                        answer = "Je ne peux pas répondre avec certitude basée sur les sources disponibles. Veuillez reformuler votre question ou être plus spécifique."
                        validation_result["original_answer"] = original_answer
                        validation_result["answer_modified"] = True

                except Exception as validation_error:
                    print(f"⚠️ Erreur validation qualité: {validation_error}")
                    # Continue sans validation en cas d'erreur

            # 7. Construire réponse finale
            response = {
                "answer": answer,
                "sources": sources,
                "question": question,
                "repo_filter": repo_filter,
                "processing_time": round(processing_time, 2),
                "performance": "fast" if processing_time < 3.0 else "slow",
            }

            # Ajouter métadonnées qualité si validation activée
            if validation_result:
                response["quality"] = {
                    "confidence": validation_result["confidence"],
                    "grade": validation_result["quality_grade"],
                    "action": validation_result["action"],
                    "should_flag": validation_result["should_flag"],
                    "hallucination_detected": validation_result["hallucination_analysis"][
                        "is_hallucination"
                    ],
                    "hallucination_severity": validation_result["hallucination_analysis"][
                        "severity"
                    ],
                    "recommendations": validation_result["recommendations"][:3],  # Limiter pour API
                    "validation_time": validation_result["validation_metadata"]["validation_time"],
                    "answer_modified": validation_result.get("answer_modified", False),
                }

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "answer": f"Erreur lors du traitement de la question: {str(e)}",
                "sources": [],
                "question": question,
                "repo_filter": repo_filter,
                "processing_time": round(processing_time, 2),
                "performance": "error",
            }

    def chat(
        self, question: str, repo: str | None = None, history: list[dict] | None = None
    ) -> dict:
        """
        Chat avec historique de conversation.

        Args:
            question: Question actuelle
            repo: Repo à filtrer (optionnel)
            history: Historique [{role: "user/assistant", content: "..."}]

        Returns:
            Même format que query() avec historique mis à jour
        """
        # TODO: Intégrer l'historique dans le prompt
        # Pour l'instant, simple query
        result = self.query(question, repo_filter=repo)

        # Ajouter à l'historique
        if history is None:
            history = []

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": result["answer"]})

        result["history"] = history

        return result
