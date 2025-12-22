"""Query engine pour RAG."""

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama

from hyperion.modules.rag.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TOP_K,
    SYSTEM_PROMPT,
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

        # Modèle embeddings (même que ingestion)
        print(f"📥 Chargement modèle embeddings...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
        print(f"✅ Embeddings prêts ({EMBEDDING_DEVICE})")

        # LLM Ollama
        print(f"🤖 Connexion à Ollama ({ollama_model})...")
        self.llm = Ollama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=LLM_TEMPERATURE,
            num_predict=LLM_MAX_TOKENS,
        )
        print(f"✅ LLM prêt")

    def query(
        self, question: str, repo_filter: Optional[str] = None, top_k: int = LLM_TOP_K
    ) -> Dict:
        """
        Répond à une question via RAG.

        Args:
            question: Question en langage naturel
            repo_filter: Filtrer sur un repo spécifique (optionnel)
            top_k: Nombre de chunks à récupérer

        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "question": str
            }
        """
        # 1. Générer embedding de la question
        question_embedding = self.embedding_model.encode(question, convert_to_numpy=True)

        # 2. Recherche dans Qdrant (API v1.7+)
        search_filter = None
        if repo_filter:
            search_filter = Filter(
                must=[FieldCondition(key="repo", match=MatchValue(value=repo_filter))]
            )

        search_results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=question_embedding.tolist(),
            limit=top_k,
            query_filter=search_filter,
        ).points

        # 3. Assembler contexte
        context_parts = []
        sources = []

        for result in search_results:
            payload = result.payload
            context_parts.append(payload["text"])
            sources.append(
                {
                    "repo": payload["repo"],
                    "section": payload["section"],
                    "score": result.score,
                    "text": payload["text"][:200] + "...",  # Preview
                }
            )

        context = "\n\n---\n\n".join(context_parts)

        # 4. Construire prompt
        full_prompt = QUERY_PROMPT_TEMPLATE.format(context=context, question=question)

        # 5. Appeler LLM
        answer = self.llm.invoke(full_prompt)

        return {
            "answer": answer.strip(),
            "sources": sources,
            "question": question,
            "repo_filter": repo_filter,
        }

    def chat(
        self, question: str, repo: Optional[str] = None, history: Optional[List[Dict]] = None
    ) -> Dict:
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
