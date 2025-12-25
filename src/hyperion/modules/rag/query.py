"""Query engine pour RAG."""

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
        """Initialise le query engine."""
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

    def query(self, question: str, repo_filter: str | None = None, top_k: int = LLM_TOP_K) -> dict:
        """
        Répond à une question via RAG (optimisé <3s).

        Args:
            question: Question en langage naturel
            repo_filter: Filtrer sur un repo spécifique (optionnel)
            top_k: Nombre de chunks à récupérer

        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "question": str,
                "processing_time": float
            }
        """
        import time

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
            sources = []

            for result in search_results:
                payload = result.payload
                # Ultra-limitation pour vitesse maximale
                text = payload["text"]
                if len(text) > 100:  # Extrême réduction 200→100
                    text = text[:100] + "..."

                context_parts.append(text)
                sources.append(
                    {
                        "repo": payload["repo"],
                        "section": payload["section"],
                        "score": result.score,
                        "text": text[:30] + "...",  # Preview ultra réduit 50→30
                    }
                )

            context = "\n\n---\n\n".join(context_parts)

            # 4. Construire prompt (optimisé)
            full_prompt = QUERY_PROMPT_TEMPLATE.format(context=context, question=question)

            # 5. Appeler LLM avec timeout
            answer = self.llm.invoke(full_prompt)

            processing_time = time.time() - start_time

            return {
                "answer": answer.strip(),
                "sources": sources,
                "question": question,
                "repo_filter": repo_filter,
                "processing_time": round(processing_time, 2),
                "performance": "fast" if processing_time < 3.0 else "slow",
            }

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
