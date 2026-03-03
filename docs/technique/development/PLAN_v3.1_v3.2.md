# Hyperion v3.1 & v3.2 - Plan d'Implémentation Complet

## Vue d'Ensemble

| Version | Nom | Focus | Effort |
|---------|-----|-------|--------|
| **v3.1** | RAG Enhanced | Amélioration qualité recherche/réponses | ~400 lignes |
| **v3.2** | Documentation Intelligence | Génération docs & diagrammes | ~800 lignes |

**Prérequis**: v3.0 Enterprise Ready (actuel)

---

# PARTIE 1: Hyperion v3.1 - RAG Enhanced

## 1.1 Objectifs

- Améliorer le recall de 15-20% avec recherche hybride
- Améliorer la précision avec re-ranking
- Réduire les hallucinations de 50% avec vérification citations

## 1.2 Structure des Fichiers

```
src/hyperion/modules/rag/
├── hybrid/                          # NOUVEAU - v3.1
│   ├── __init__.py
│   ├── config.py                    # Configuration hybride
│   ├── bm25_index.py               # Index BM25
│   ├── hybrid_search.py            # Moteur hybride
│   └── tokenizer.py                # Tokenizer code-aware
├── reranking/                       # NOUVEAU - v3.1
│   ├── __init__.py
│   ├── config.py
│   ├── simple_reranker.py          # Re-ranker 3 facteurs
│   └── factors.py                  # Fonctions de scoring
├── citations/                       # NOUVEAU - v3.1
│   ├── __init__.py
│   ├── verifier.py                 # Vérificateur citations
│   └── claim_extractor.py          # Extraction claims
├── query.py                         # MODIFIER - intégrer v3.1
├── ingestion.py                     # MODIFIER - construire index BM25
└── config.py                        # MODIFIER - nouvelles configs
```

## 1.3 Dépendances

```toml
# pyproject.toml - ajouter
[project.dependencies]
rank-bm25 = "^0.2.2"
```

---

## 1.4 Implémentation Détaillée

### 1.4.1 Configuration Hybride

**Fichier**: `src/hyperion/modules/rag/hybrid/config.py`

```python
"""Configuration pour la recherche hybride v3.1."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HybridSearchConfig:
    """Configuration du moteur de recherche hybride."""

    # Pondération des sources
    vector_weight: float = 0.6
    bm25_weight: float = 0.4

    # Paramètre RRF (Reciprocal Rank Fusion)
    rrf_k: int = 60

    # Nombre de résultats intermédiaires
    intermediate_top_k: int = 50

    # Chemin de persistence index BM25
    bm25_index_path: Path = field(default_factory=lambda: Path("data/bm25_index"))

    # Tokenization
    min_token_length: int = 2
    max_token_length: int = 50

    def __post_init__(self):
        self.bm25_index_path.mkdir(parents=True, exist_ok=True)
```

---

### 1.4.2 Tokenizer Code-Aware

**Fichier**: `src/hyperion/modules/rag/hybrid/tokenizer.py`

```python
"""Tokenizer adapté au code source."""

import re
from typing import List


class CodeAwareTokenizer:
    """Tokenizer qui comprend les conventions de nommage du code."""

    def __init__(self, min_length: int = 2, max_length: int = 50):
        self.min_length = min_length
        self.max_length = max_length

        # Patterns pour split
        self.split_patterns = [
            r'[\s\n\t]+',           # Espaces
            r'[_\-\.]+',            # Séparateurs
            r'(?<=[a-z])(?=[A-Z])', # camelCase
            r'(?<=[A-Z])(?=[A-Z][a-z])',  # XMLParser -> XML, Parser
            r'[^\w]+',              # Non-alphanumériques
        ]

        # Stopwords code
        self.stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'self', 'cls', 'this', 'that', 'these', 'those',
            'def', 'class', 'import', 'from', 'return', 'if', 'else',
            'elif', 'for', 'while', 'try', 'except', 'finally', 'with',
            'as', 'in', 'not', 'and', 'or', 'none', 'true', 'false',
        }

    def tokenize(self, text: str) -> List[str]:
        """Tokenize le texte en tokens normalisés."""
        if not text:
            return []

        # Lowercase
        text = text.lower()

        # Split progressif
        tokens = [text]
        for pattern in self.split_patterns:
            new_tokens = []
            for token in tokens:
                new_tokens.extend(re.split(pattern, token))
            tokens = new_tokens

        # Filtrage
        filtered = []
        for token in tokens:
            token = token.strip()
            if (
                token
                and self.min_length <= len(token) <= self.max_length
                and token not in self.stopwords
                and not token.isdigit()
            ):
                filtered.append(token)

        return filtered

    def tokenize_query(self, query: str) -> List[str]:
        """Tokenize une requête (moins de filtrage)."""
        tokens = self.tokenize(query)
        # Garde aussi les tokens courts pour les requêtes
        return tokens
```

---

### 1.4.3 Index BM25

**Fichier**: `src/hyperion/modules/rag/hybrid/bm25_index.py`

```python
"""Index BM25 avec persistence."""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from .tokenizer import CodeAwareTokenizer
from .config import HybridSearchConfig


@dataclass
class BM25Result:
    """Résultat de recherche BM25."""
    doc_id: str
    score: float
    rank: int


class BM25Index:
    """Index BM25 avec persistence et mise à jour incrémentale."""

    def __init__(self, config: HybridSearchConfig):
        self.config = config
        self.tokenizer = CodeAwareTokenizer(
            min_length=config.min_token_length,
            max_length=config.max_token_length
        )

        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []
        self.doc_ids: List[str] = []
        self.tokenized_corpus: List[List[str]] = []

        # Charger index existant si disponible
        self._load_if_exists()

    def index_documents(self, documents: List[Dict[str, Any]], force: bool = False):
        """Indexe une liste de documents.

        Args:
            documents: Liste de dicts avec 'id' et 'text'
            force: Si True, réindexe tout même si déjà présent
        """
        if not force and self.bm25 is not None:
            # Index incrémental
            new_docs = [d for d in documents if d["id"] not in self.doc_ids]
            if not new_docs:
                return

            for doc in new_docs:
                tokens = self.tokenizer.tokenize(doc["text"])
                self.tokenized_corpus.append(tokens)
                self.documents.append(doc)
                self.doc_ids.append(doc["id"])

            # Reconstruire BM25 avec nouveau corpus
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            # Index complet
            self.documents = documents
            self.doc_ids = [d["id"] for d in documents]
            self.tokenized_corpus = [
                self.tokenizer.tokenize(d["text"]) for d in documents
            ]
            self.bm25 = BM25Okapi(self.tokenized_corpus)

        self._save()

    def search(self, query: str, top_k: int = 10) -> List[BM25Result]:
        """Recherche dans l'index BM25.

        Args:
            query: Requête textuelle
            top_k: Nombre de résultats

        Returns:
            Liste de BM25Result triés par score décroissant
        """
        if self.bm25 is None:
            return []

        tokens = self.tokenizer.tokenize_query(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)

        # Top-k indices
        import numpy as np
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:  # Ignorer scores nuls
                results.append(BM25Result(
                    doc_id=self.doc_ids[idx],
                    score=float(scores[idx]),
                    rank=rank
                ))

        return results

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un document par ID."""
        try:
            idx = self.doc_ids.index(doc_id)
            return self.documents[idx]
        except ValueError:
            return None

    def _save(self):
        """Sauvegarde l'index sur disque."""
        index_file = self.config.bm25_index_path / "bm25_index.pkl"
        meta_file = self.config.bm25_index_path / "bm25_meta.json"

        # Sauvegarder BM25
        with open(index_file, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'tokenized_corpus': self.tokenized_corpus,
            }, f)

        # Sauvegarder métadonnées
        with open(meta_file, 'w') as f:
            json.dump({
                'doc_ids': self.doc_ids,
                'documents': self.documents,
            }, f)

    def _load_if_exists(self):
        """Charge l'index depuis le disque si disponible."""
        index_file = self.config.bm25_index_path / "bm25_index.pkl"
        meta_file = self.config.bm25_index_path / "bm25_meta.json"

        if index_file.exists() and meta_file.exists():
            try:
                with open(index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.bm25 = data['bm25']
                    self.tokenized_corpus = data['tokenized_corpus']

                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    self.doc_ids = meta['doc_ids']
                    self.documents = meta['documents']
            except Exception:
                # Index corrompu, on repart de zéro
                pass

    def clear(self):
        """Vide l'index."""
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        self.tokenized_corpus = []

        # Supprimer fichiers
        for f in self.config.bm25_index_path.glob("bm25_*"):
            f.unlink()
```

---

### 1.4.4 Moteur de Recherche Hybride

**Fichier**: `src/hyperion/modules/rag/hybrid/hybrid_search.py`

```python
"""Moteur de recherche hybride BM25 + Vector."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient

from .config import HybridSearchConfig
from .bm25_index import BM25Index, BM25Result


@dataclass
class HybridResult:
    """Résultat de recherche hybride."""
    doc_id: str
    text: str
    score: float
    vector_score: Optional[float] = None
    bm25_score: Optional[float] = None
    metadata: Dict[str, Any] = None


class HybridSearchEngine:
    """Combine recherche vectorielle Qdrant + BM25."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        embedder,
        config: Optional[HybridSearchConfig] = None
    ):
        self.qdrant = qdrant_client
        self.collection_name = collection_name
        self.embedder = embedder
        self.config = config or HybridSearchConfig()

        self.bm25_index = BM25Index(self.config)

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Indexe les documents dans BM25 (Qdrant géré séparément)."""
        self.bm25_index.index_documents(documents)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_conditions: Optional[Dict] = None
    ) -> List[HybridResult]:
        """Recherche hybride avec fusion RRF.

        Args:
            query: Requête textuelle
            top_k: Nombre de résultats finaux
            filter_conditions: Filtres Qdrant optionnels

        Returns:
            Liste de HybridResult triés par score fusionné
        """
        intermediate_k = self.config.intermediate_top_k

        # 1. Recherche vectorielle
        vector_results = self._vector_search(query, intermediate_k, filter_conditions)

        # 2. Recherche BM25
        bm25_results = self.bm25_index.search(query, intermediate_k)

        # 3. Fusion RRF
        fused = self._rrf_fusion(vector_results, bm25_results)

        return fused[:top_k]

    def _vector_search(
        self,
        query: str,
        top_k: int,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Recherche vectorielle via Qdrant."""
        try:
            query_vector = self.embedder.encode(query).tolist()

            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filter_conditions
            )

            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "text": r.payload.get("text", ""),
                    "metadata": r.payload
                }
                for r in results
            ]
        except Exception:
            return []

    def _rrf_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[BM25Result]
    ) -> List[HybridResult]:
        """Reciprocal Rank Fusion des deux sources."""
        k = self.config.rrf_k
        scores: Dict[str, Dict] = {}

        # Scores vectoriels
        for rank, r in enumerate(vector_results):
            doc_id = r["id"]
            rrf_score = self.config.vector_weight / (k + rank + 1)
            scores[doc_id] = {
                "rrf_score": rrf_score,
                "vector_score": r["score"],
                "bm25_score": None,
                "text": r["text"],
                "metadata": r.get("metadata", {})
            }

        # Scores BM25
        for r in bm25_results:
            rrf_score = self.config.bm25_weight / (k + r.rank + 1)
            if r.doc_id in scores:
                scores[r.doc_id]["rrf_score"] += rrf_score
                scores[r.doc_id]["bm25_score"] = r.score
            else:
                doc = self.bm25_index.get_document(r.doc_id)
                if doc:
                    scores[r.doc_id] = {
                        "rrf_score": rrf_score,
                        "vector_score": None,
                        "bm25_score": r.score,
                        "text": doc.get("text", ""),
                        "metadata": doc
                    }

        # Tri par score RRF
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x]["rrf_score"], reverse=True)

        return [
            HybridResult(
                doc_id=doc_id,
                text=scores[doc_id]["text"],
                score=scores[doc_id]["rrf_score"],
                vector_score=scores[doc_id]["vector_score"],
                bm25_score=scores[doc_id]["bm25_score"],
                metadata=scores[doc_id]["metadata"]
            )
            for doc_id in sorted_ids
        ]
```

---

### 1.4.5 Re-ranking Simple

**Fichier**: `src/hyperion/modules/rag/reranking/config.py`

```python
"""Configuration du re-ranking."""

from dataclasses import dataclass


@dataclass
class RerankerConfig:
    """Configuration des facteurs de re-ranking."""

    # Poids des facteurs
    semantic_weight: float = 0.5
    recency_weight: float = 0.2
    source_type_weight: float = 0.3

    # Seuil de score minimum
    min_score_threshold: float = 0.1
```

**Fichier**: `src/hyperion/modules/rag/reranking/factors.py`

```python
"""Fonctions de scoring pour le re-ranking."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import numpy as np


def semantic_similarity_score(
    query_embedding: np.ndarray,
    doc_embedding: Optional[np.ndarray]
) -> float:
    """Calcule la similarité cosinus."""
    if doc_embedding is None:
        return 0.5

    dot = np.dot(query_embedding, doc_embedding)
    norm = np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)

    if norm == 0:
        return 0.0

    return float(dot / norm)


def recency_score(timestamp: Optional[str], decay_days: int = 365) -> float:
    """Score basé sur la fraîcheur du contenu.

    Plus récent = score plus élevé.
    Decay exponentiel sur decay_days.
    """
    if not timestamp:
        return 0.5  # Neutre si pas de timestamp

    try:
        doc_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(doc_date.tzinfo)
        days_old = (now - doc_date).days

        # Decay exponentiel
        score = np.exp(-days_old / decay_days)
        return float(max(0.0, min(1.0, score)))
    except Exception:
        return 0.5


def source_type_score(section: str) -> float:
    """Score par type de source.

    Code source > Documentation > Métadonnées
    """
    scores = {
        # Code
        "functions": 1.0,
        "classes": 0.95,
        "methods": 0.9,

        # Documentation
        "overview": 0.85,
        "docstrings": 0.8,
        "comments": 0.7,

        # Métadonnées
        "metrics": 0.6,
        "tech": 0.55,
        "contributors": 0.4,
        "hotspots": 0.5,
        "extensions": 0.3,
    }

    return scores.get(section.lower(), 0.5)
```

**Fichier**: `src/hyperion/modules/rag/reranking/simple_reranker.py`

```python
"""Re-ranker simple basé sur 3 facteurs."""

from typing import List, Optional
from dataclasses import dataclass
import numpy as np

from .config import RerankerConfig
from .factors import semantic_similarity_score, recency_score, source_type_score
from ..hybrid.hybrid_search import HybridResult


@dataclass
class RankedResult:
    """Résultat après re-ranking."""
    result: HybridResult
    final_score: float
    factor_scores: dict


class SimpleReranker:
    """Re-ranker basé sur 3 facteurs: sémantique, fraîcheur, type source."""

    def __init__(self, embedder, config: Optional[RerankerConfig] = None):
        self.embedder = embedder
        self.config = config or RerankerConfig()

    def rerank(
        self,
        query: str,
        results: List[HybridResult],
        top_k: int = 5
    ) -> List[RankedResult]:
        """Re-rank les résultats avec scoring multi-facteurs.

        Args:
            query: Requête originale
            results: Résultats de la recherche hybride
            top_k: Nombre de résultats à retourner

        Returns:
            Liste de RankedResult triés par score final
        """
        if not results:
            return []

        # Encoder la requête
        query_embedding = self.embedder.encode(query)

        ranked = []
        for r in results:
            scores = self._compute_factor_scores(query_embedding, r)
            final_score = self._aggregate_scores(scores)

            if final_score >= self.config.min_score_threshold:
                ranked.append(RankedResult(
                    result=r,
                    final_score=final_score,
                    factor_scores=scores
                ))

        # Tri par score final
        ranked.sort(key=lambda x: x.final_score, reverse=True)

        return ranked[:top_k]

    def _compute_factor_scores(
        self,
        query_embedding: np.ndarray,
        result: HybridResult
    ) -> dict:
        """Calcule les scores pour chaque facteur."""
        # Embedding du document (si disponible dans metadata)
        doc_embedding = None
        if result.metadata and "embedding" in result.metadata:
            doc_embedding = np.array(result.metadata["embedding"])

        # Score sémantique
        if result.vector_score is not None:
            # Utiliser le score vectoriel existant
            sem_score = result.vector_score
        else:
            # Calculer
            sem_score = semantic_similarity_score(query_embedding, doc_embedding)

        # Score fraîcheur
        timestamp = None
        if result.metadata:
            timestamp = result.metadata.get("timestamp") or result.metadata.get("date")
        rec_score = recency_score(timestamp)

        # Score type source
        section = ""
        if result.metadata:
            section = result.metadata.get("section", "")
        src_score = source_type_score(section)

        return {
            "semantic": sem_score,
            "recency": rec_score,
            "source_type": src_score
        }

    def _aggregate_scores(self, scores: dict) -> float:
        """Agrège les scores avec pondération."""
        return (
            self.config.semantic_weight * scores["semantic"] +
            self.config.recency_weight * scores["recency"] +
            self.config.source_type_weight * scores["source_type"]
        )
```

---

### 1.4.6 Vérification Citations

**Fichier**: `src/hyperion/modules/rag/citations/claim_extractor.py`

```python
"""Extraction des claims depuis une réponse."""

import re
from typing import List


class ClaimExtractor:
    """Extrait les affirmations vérifiables d'une réponse."""

    def __init__(self, min_length: int = 20, max_length: int = 500):
        self.min_length = min_length
        self.max_length = max_length

    def extract(self, response: str) -> List[str]:
        """Extrait les claims d'une réponse.

        Une claim est une phrase/segment qui fait une affirmation vérifiable.
        """
        if not response:
            return []

        # Split en phrases
        sentences = re.split(r'[.!?]\s+', response)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()

            # Filtrer par longueur
            if len(sentence) < self.min_length:
                continue
            if len(sentence) > self.max_length:
                # Tronquer
                sentence = sentence[:self.max_length]

            # Ignorer les questions et les phrases trop vagues
            if sentence.endswith('?'):
                continue
            if self._is_too_vague(sentence):
                continue

            claims.append(sentence)

        return claims

    def _is_too_vague(self, sentence: str) -> bool:
        """Détecte les phrases trop vagues pour être vérifiées."""
        vague_patterns = [
            r'^(maybe|perhaps|possibly|probably)\b',
            r'^(i think|i believe|it seems)\b',
            r'^(generally|usually|sometimes)\b',
            r'^(you (can|could|should|might))\b',
        ]

        lower = sentence.lower()
        for pattern in vague_patterns:
            if re.match(pattern, lower):
                return True

        return False
```

**Fichier**: `src/hyperion/modules/rag/citations/verifier.py`

```python
"""Vérification des citations contre les sources."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from .claim_extractor import ClaimExtractor


@dataclass
class VerifiedClaim:
    """Résultat de vérification d'une claim."""
    claim: str
    source_id: Optional[str]
    source_text: Optional[str]
    confidence: float
    verified: bool


@dataclass
class VerificationResult:
    """Résultat global de vérification."""
    claims: List[VerifiedClaim]
    overall_confidence: float
    verified_count: int
    unverified_count: int
    verification_rate: float


class CitationVerifier:
    """Vérifie que les affirmations sont supportées par les sources."""

    def __init__(
        self,
        embedder,
        confidence_threshold: float = 0.7,
        min_claims: int = 1
    ):
        self.embedder = embedder
        self.threshold = confidence_threshold
        self.min_claims = min_claims
        self.claim_extractor = ClaimExtractor()

    def verify(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> VerificationResult:
        """Vérifie que la réponse est supportée par les sources.

        Args:
            response: Réponse générée par le LLM
            sources: Liste des sources utilisées (avec 'id' et 'text')

        Returns:
            VerificationResult avec détails par claim
        """
        # Extraire les claims
        claims = self.claim_extractor.extract(response)

        if not claims:
            # Pas de claims vérifiables
            return VerificationResult(
                claims=[],
                overall_confidence=1.0,
                verified_count=0,
                unverified_count=0,
                verification_rate=1.0
            )

        # Pré-encoder les sources
        source_embeddings = self._encode_sources(sources)

        # Vérifier chaque claim
        verified_claims = []
        for claim in claims:
            result = self._verify_claim(claim, sources, source_embeddings)
            verified_claims.append(result)

        # Statistiques
        verified_count = sum(1 for c in verified_claims if c.verified)
        unverified_count = len(verified_claims) - verified_count
        verification_rate = verified_count / len(verified_claims) if verified_claims else 1.0

        # Confidence globale (moyenne des confidences)
        confidences = [c.confidence for c in verified_claims]
        overall_confidence = np.mean(confidences) if confidences else 1.0

        return VerificationResult(
            claims=verified_claims,
            overall_confidence=float(overall_confidence),
            verified_count=verified_count,
            unverified_count=unverified_count,
            verification_rate=verification_rate
        )

    def _encode_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """Encode les sources en vecteurs."""
        embeddings = {}
        for source in sources:
            source_id = source.get("id", str(hash(source.get("text", ""))))
            text = source.get("text", "")[:1000]  # Limiter la taille
            if text:
                embeddings[source_id] = self.embedder.encode(text)
        return embeddings

    def _verify_claim(
        self,
        claim: str,
        sources: List[Dict[str, Any]],
        source_embeddings: Dict[str, np.ndarray]
    ) -> VerifiedClaim:
        """Vérifie une claim contre les sources."""
        claim_embedding = self.embedder.encode(claim)

        best_source_id = None
        best_source_text = None
        best_score = 0.0

        for source in sources:
            source_id = source.get("id", str(hash(source.get("text", ""))))
            source_text = source.get("text", "")

            if source_id not in source_embeddings:
                continue

            # Similarité cosinus
            source_emb = source_embeddings[source_id]
            score = self._cosine_similarity(claim_embedding, source_emb)

            if score > best_score:
                best_score = score
                best_source_id = source_id
                best_source_text = source_text[:200]  # Extrait

        return VerifiedClaim(
            claim=claim,
            source_id=best_source_id,
            source_text=best_source_text,
            confidence=float(best_score),
            verified=best_score >= self.threshold
        )

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcule la similarité cosinus."""
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(dot / norm)
```

---

### 1.4.7 Intégration dans RAGQueryEngine

**Fichier**: `src/hyperion/modules/rag/query.py` (modifications)

```python
# Ajouter ces imports en haut
from .hybrid.config import HybridSearchConfig
from .hybrid.hybrid_search import HybridSearchEngine
from .reranking.config import RerankerConfig
from .reranking.simple_reranker import SimpleReranker
from .citations.verifier import CitationVerifier


class RAGQueryEngine:
    """Moteur de requête RAG v3.1 avec recherche hybride."""

    def __init__(self, config: RAGConfig = None):
        # ... code existant ...

        # v3.1: Composants hybrides
        self.hybrid_config = HybridSearchConfig()
        self.hybrid_search = HybridSearchEngine(
            qdrant_client=self.qdrant_client,
            collection_name=self.config.qdrant_collection,
            embedder=self.embedder,
            config=self.hybrid_config
        )

        self.reranker_config = RerankerConfig()
        self.reranker = SimpleReranker(
            embedder=self.embedder,
            config=self.reranker_config
        )

        self.citation_verifier = CitationVerifier(
            embedder=self.embedder,
            confidence_threshold=0.7
        )

    def query(
        self,
        question: str,
        repo: str = None,
        use_hybrid: bool = True,  # v3.1
        verify_citations: bool = True  # v3.1
    ) -> dict:
        """Exécute une requête RAG.

        Args:
            question: Question utilisateur
            repo: Filtrer par repository
            use_hybrid: Utiliser recherche hybride (v3.1)
            verify_citations: Vérifier les citations (v3.1)

        Returns:
            Dict avec response, sources, et métriques v3.1
        """
        # 1. Recherche
        if use_hybrid:
            filter_cond = {"repo": repo} if repo else None
            hybrid_results = self.hybrid_search.search(
                query=question,
                top_k=20,
                filter_conditions=filter_cond
            )

            # 2. Re-ranking
            ranked_results = self.reranker.rerank(
                query=question,
                results=hybrid_results,
                top_k=5
            )

            sources = [
                {
                    "id": r.result.doc_id,
                    "text": r.result.text,
                    "score": r.final_score,
                    "metadata": r.result.metadata
                }
                for r in ranked_results
            ]
        else:
            # Fallback recherche simple (code existant)
            sources = self._simple_search(question, repo)

        # 3. Génération réponse (code existant)
        response = self._generate_response(question, sources)

        # 4. Vérification citations (v3.1)
        citation_result = None
        if verify_citations and sources:
            citation_result = self.citation_verifier.verify(response, sources)

        return {
            "response": response,
            "sources": sources,
            # v3.1 métriques
            "citation_confidence": citation_result.overall_confidence if citation_result else None,
            "verified_claims": citation_result.verified_count if citation_result else None,
            "unverified_claims": citation_result.unverified_count if citation_result else None,
            "verification_rate": citation_result.verification_rate if citation_result else None,
        }
```

---

### 1.4.8 Tests v3.1

**Fichier**: `tests/unit/rag/test_hybrid_search.py`

```python
"""Tests pour la recherche hybride."""

import pytest
from unittest.mock import Mock, MagicMock

from hyperion.modules.rag.hybrid.config import HybridSearchConfig
from hyperion.modules.rag.hybrid.tokenizer import CodeAwareTokenizer
from hyperion.modules.rag.hybrid.bm25_index import BM25Index
from hyperion.modules.rag.hybrid.hybrid_search import HybridSearchEngine


class TestCodeAwareTokenizer:
    def test_tokenize_camel_case(self):
        tokenizer = CodeAwareTokenizer()
        tokens = tokenizer.tokenize("getUserById")
        assert "get" in tokens
        assert "user" in tokens
        assert "by" not in tokens  # stopword

    def test_tokenize_snake_case(self):
        tokenizer = CodeAwareTokenizer()
        tokens = tokenizer.tokenize("get_user_by_id")
        assert "get" in tokens
        assert "user" in tokens

    def test_removes_stopwords(self):
        tokenizer = CodeAwareTokenizer()
        tokens = tokenizer.tokenize("def function self return")
        assert "def" not in tokens
        assert "self" not in tokens
        assert "return" not in tokens


class TestBM25Index:
    def test_index_and_search(self, tmp_path):
        config = HybridSearchConfig(bm25_index_path=tmp_path / "bm25")
        index = BM25Index(config)

        docs = [
            {"id": "1", "text": "Python function to calculate sum"},
            {"id": "2", "text": "JavaScript class for user management"},
            {"id": "3", "text": "Python class with async methods"},
        ]

        index.index_documents(docs)
        results = index.search("Python function", top_k=2)

        assert len(results) >= 1
        assert results[0].doc_id == "1"


class TestHybridSearchEngine:
    def test_rrf_fusion(self):
        # Mock Qdrant et embedder
        mock_qdrant = MagicMock()
        mock_embedder = Mock()
        mock_embedder.encode.return_value = [0.1] * 384

        config = HybridSearchConfig()
        engine = HybridSearchEngine(
            qdrant_client=mock_qdrant,
            collection_name="test",
            embedder=mock_embedder,
            config=config
        )

        # Test fusion logic
        vector_results = [
            {"id": "1", "score": 0.9, "text": "doc1", "metadata": {}},
            {"id": "2", "score": 0.8, "text": "doc2", "metadata": {}},
        ]

        from hyperion.modules.rag.hybrid.bm25_index import BM25Result
        bm25_results = [
            BM25Result(doc_id="2", score=5.0, rank=0),
            BM25Result(doc_id="3", score=4.0, rank=1),
        ]

        fused = engine._rrf_fusion(vector_results, bm25_results)

        # Doc 2 devrait être en haut (présent dans les deux)
        assert fused[0].doc_id == "2"
```

---

## 1.5 Résumé v3.1

| Composant | Fichiers | Lignes |
|-----------|----------|--------|
| Config | 2 | ~50 |
| Tokenizer | 1 | ~70 |
| BM25 Index | 1 | ~150 |
| Hybrid Search | 1 | ~120 |
| Reranker | 3 | ~100 |
| Citations | 2 | ~150 |
| Tests | 1 | ~80 |
| **Total** | **11** | **~720** |

---

# PARTIE 2: Hyperion v3.2 - Documentation Intelligence

## 2.1 Objectifs

- Générer des docstrings automatiquement via LLM
- Générer des README complets
- Créer des diagrammes Mermaid depuis le code
- Produire une documentation API

## 2.2 Structure des Fichiers

```
src/hyperion/modules/documentation/
├── __init__.py
├── v3_2/                            # NOUVEAU
│   ├── __init__.py
│   ├── config.py                    # Configuration docs
│   ├── doc_generator.py             # Orchestrateur principal
│   ├── docstring/
│   │   ├── __init__.py
│   │   ├── generator.py             # Génération docstrings
│   │   ├── styles.py                # Google, NumPy, Sphinx
│   │   └── prompts.py               # Prompts LLM
│   ├── readme/
│   │   ├── __init__.py
│   │   ├── generator.py             # Génération README
│   │   └── templates.py             # Templates sections
│   ├── diagrams/
│   │   ├── __init__.py
│   │   ├── mermaid_base.py          # Base Mermaid
│   │   ├── class_diagram.py         # Diagrammes de classes
│   │   ├── flowchart.py             # Flowcharts
│   │   ├── dependency_graph.py      # Graphe dépendances
│   │   └── sequence_diagram.py      # Diagrammes séquence
│   └── api_docs/
│       ├── __init__.py
│       ├── generator.py             # Génération API docs
│       └── templates.py             # Templates API
└── generator.py                      # MODIFIER - utiliser v3_2
```

## 2.3 Dépendances

Aucune nouvelle dépendance requise ! Utilise :
- `langchain-ollama` (existant)
- `jinja2` (existant)
- Modules `understanding` (existant)

---

## 2.4 Implémentation Détaillée

### 2.4.1 Configuration Documentation

**Fichier**: `src/hyperion/modules/documentation/v3_2/config.py`

```python
"""Configuration pour la génération de documentation v3.2."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class DocstringStyle(Enum):
    """Styles de docstrings supportés."""
    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"


class DiagramType(Enum):
    """Types de diagrammes supportés."""
    CLASS = "class"
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"


@dataclass
class DocumentationConfig:
    """Configuration principale de la documentation."""

    # Style docstrings
    docstring_style: DocstringStyle = DocstringStyle.GOOGLE

    # LLM
    llm_model: str = "llama3.2:1b"
    llm_temperature: float = 0.2
    llm_timeout: int = 30

    # Output
    output_dir: Path = field(default_factory=lambda: Path("docs/generated"))
    output_format: str = "markdown"

    # Filtrage
    include_private: bool = False
    include_tests: bool = False
    min_complexity: int = 0  # Documenter seulement si complexité >= min

    # Diagrammes
    diagram_format: str = "mermaid"
    max_nodes_per_diagram: int = 50

    # Langues
    language: str = "fr"  # Docs en français

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class DiagramConfig:
    """Configuration spécifique aux diagrammes."""

    # Apparence
    direction: str = "TB"  # TB, BT, LR, RL
    theme: str = "default"  # default, dark, forest, neutral

    # Filtrage
    show_private: bool = False
    show_methods: bool = True
    show_attributes: bool = True
    max_depth: int = 3

    # Grouping
    group_by_module: bool = True
```

---

### 2.4.2 Styles de Docstrings

**Fichier**: `src/hyperion/modules/documentation/v3_2/docstring/styles.py`

```python
"""Définition des styles de docstrings."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class DocstringTemplate:
    """Template pour un style de docstring."""

    function_template: str
    class_template: str
    module_template: str


GOOGLE_STYLE = DocstringTemplate(
    function_template='''"""
{summary}

{description}

Args:
{args}

Returns:
{returns}

Raises:
{raises}

Example:
{example}
"""''',

    class_template='''"""
{summary}

{description}

Attributes:
{attributes}

Example:
{example}
"""''',

    module_template='''"""
{summary}

{description}

Modules:
{modules}

Classes:
{classes}

Functions:
{functions}
"""'''
)


NUMPY_STYLE = DocstringTemplate(
    function_template='''"""
{summary}

{description}

Parameters
----------
{args}

Returns
-------
{returns}

Raises
------
{raises}

Examples
--------
{example}
"""''',

    class_template='''"""
{summary}

{description}

Attributes
----------
{attributes}

Examples
--------
{example}
"""''',

    module_template='''"""
{summary}

{description}
"""'''
)


SPHINX_STYLE = DocstringTemplate(
    function_template='''"""
{summary}

{description}

:param {args}
:returns: {returns}
:raises {raises}:

.. code-block:: python

{example}
"""''',

    class_template='''"""
{summary}

{description}

:ivar {attributes}

.. code-block:: python

{example}
"""''',

    module_template='''"""
{summary}

{description}
"""'''
)


STYLES: Dict[str, DocstringTemplate] = {
    "google": GOOGLE_STYLE,
    "numpy": NUMPY_STYLE,
    "sphinx": SPHINX_STYLE,
}
```

---

### 2.4.3 Prompts LLM pour Docstrings

**Fichier**: `src/hyperion/modules/documentation/v3_2/docstring/prompts.py`

```python
"""Prompts LLM pour la génération de docstrings."""


FUNCTION_DOCSTRING_PROMPT = """Tu es un expert Python. Génère une docstring {style}-style pour cette fonction.

Fonction: {name}
Signature: {signature}
Complexité cyclomatique: {complexity}
Appels: {calls}
Fichier: {file_path}

Code source:
```python
{source_code}
```

Contexte du module:
{module_context}

Génère UNIQUEMENT la docstring (sans les triples guillemets), en français, avec:
1. Résumé court (1 ligne)
2. Description détaillée si la fonction est complexe
3. Args: chaque paramètre avec type et description
4. Returns: type et description du retour
5. Raises: exceptions possibles (si applicable)
6. Example: un exemple d'utilisation simple

Docstring:"""


CLASS_DOCSTRING_PROMPT = """Tu es un expert Python. Génère une docstring {style}-style pour cette classe.

Classe: {name}
Hérite de: {bases}
Méthodes: {methods}
Attributs: {attributes}
Fichier: {file_path}

Code source:
```python
{source_code}
```

Génère UNIQUEMENT la docstring (sans les triples guillemets), en français, avec:
1. Résumé court (1 ligne)
2. Description du rôle de la classe
3. Attributes: attributs principaux avec types
4. Example: exemple d'instanciation et utilisation

Docstring:"""


MODULE_DOCSTRING_PROMPT = """Tu es un expert Python. Génère une docstring de module pour ce fichier.

Fichier: {file_path}
Classes: {classes}
Fonctions: {functions}
Imports: {imports}

Aperçu du code:
```python
{code_preview}
```

Génère UNIQUEMENT la docstring (sans les triples guillemets), en français, avec:
1. Résumé du module (1-2 lignes)
2. Description de son rôle dans le projet
3. Liste des classes principales
4. Liste des fonctions principales

Docstring:"""


README_SECTION_PROMPT = """Tu es un expert en documentation technique. Génère la section "{section}" d'un README.

Projet: {project_name}
Description: {description}
Technologies: {technologies}
Structure:
{structure}

Métriques:
- Lignes de code: {loc}
- Nombre de fichiers: {files}
- Complexité moyenne: {avg_complexity}

Génère cette section en markdown, en français, de manière concise mais informative:"""
```

---

### 2.4.4 Générateur de Docstrings

**Fichier**: `src/hyperion/modules/documentation/v3_2/docstring/generator.py`

```python
"""Générateur de docstrings via LLM."""

from typing import Optional, List
from pathlib import Path

from langchain_ollama import OllamaLLM

from ..config import DocumentationConfig, DocstringStyle
from .prompts import FUNCTION_DOCSTRING_PROMPT, CLASS_DOCSTRING_PROMPT
from .styles import STYLES
from ....understanding.ast_parser import ASTParser, FunctionInfo, ClassInfo, FileAnalysis


class DocstringGenerator:
    """Génère des docstrings intelligentes via LLM."""

    def __init__(self, config: Optional[DocumentationConfig] = None):
        self.config = config or DocumentationConfig()
        self.parser = ASTParser()

        self.llm = OllamaLLM(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            timeout=self.config.llm_timeout
        )

        self.style = STYLES.get(
            self.config.docstring_style.value,
            STYLES["google"]
        )

    def generate_for_file(
        self,
        file_path: Path,
        inplace: bool = False
    ) -> dict:
        """Génère les docstrings pour un fichier.

        Args:
            file_path: Chemin du fichier Python
            inplace: Si True, modifie le fichier directement

        Returns:
            Dict avec les docstrings générées
        """
        analysis = self.parser.analyze_file(file_path)

        results = {
            "file": str(file_path),
            "functions": [],
            "classes": [],
        }

        # Générer pour chaque fonction
        for func in analysis.functions:
            if self._should_document(func):
                docstring = self._generate_function_docstring(func, analysis)
                results["functions"].append({
                    "name": func.name,
                    "lineno": func.lineno,
                    "docstring": docstring,
                    "existing": func.docstring
                })

        # Générer pour chaque classe
        for cls in analysis.classes:
            if self._should_document_class(cls):
                docstring = self._generate_class_docstring(cls, analysis)
                results["classes"].append({
                    "name": cls.name,
                    "lineno": cls.lineno,
                    "docstring": docstring,
                    "existing": cls.docstring
                })

        if inplace:
            self._apply_docstrings(file_path, results)

        return results

    def _generate_function_docstring(
        self,
        func: FunctionInfo,
        context: FileAnalysis
    ) -> str:
        """Génère une docstring pour une fonction."""
        prompt = FUNCTION_DOCSTRING_PROMPT.format(
            style=self.config.docstring_style.value,
            name=func.name,
            signature=self._format_signature(func),
            complexity=func.complexity,
            calls=", ".join(func.calls[:10]) if func.calls else "aucun",
            file_path=context.file_path,
            source_code=self._get_source_code(func, context),
            module_context=self._get_module_context(context)
        )

        try:
            response = self.llm.invoke(prompt)
            return self._clean_docstring(response)
        except Exception as e:
            return f"Documentation non générée: {e}"

    def _generate_class_docstring(
        self,
        cls: ClassInfo,
        context: FileAnalysis
    ) -> str:
        """Génère une docstring pour une classe."""
        prompt = CLASS_DOCSTRING_PROMPT.format(
            style=self.config.docstring_style.value,
            name=cls.name,
            bases=", ".join(cls.bases) if cls.bases else "object",
            methods=", ".join(m.name for m in cls.methods[:10]),
            attributes=", ".join(cls.attributes[:10]) if cls.attributes else "aucun",
            file_path=context.file_path,
            source_code=self._get_class_source(cls, context)
        )

        try:
            response = self.llm.invoke(prompt)
            return self._clean_docstring(response)
        except Exception as e:
            return f"Documentation non générée: {e}"

    def _should_document(self, func: FunctionInfo) -> bool:
        """Détermine si une fonction doit être documentée."""
        # Ignorer les fonctions privées si configuré
        if not self.config.include_private and func.name.startswith('_'):
            if not func.name.startswith('__'):  # Garder __init__, etc.
                return False

        # Ignorer si complexité trop faible
        if func.complexity < self.config.min_complexity:
            return False

        # Ignorer si déjà documentée (sauf si vide)
        if func.docstring and len(func.docstring) > 10:
            return False

        return True

    def _should_document_class(self, cls: ClassInfo) -> bool:
        """Détermine si une classe doit être documentée."""
        if not self.config.include_private and cls.name.startswith('_'):
            return False

        if cls.docstring and len(cls.docstring) > 10:
            return False

        return True

    def _format_signature(self, func: FunctionInfo) -> str:
        """Formate la signature d'une fonction."""
        args = []
        for arg in func.args:
            if isinstance(arg, dict):
                arg_str = arg.get('name', str(arg))
                if arg.get('annotation'):
                    arg_str += f": {arg['annotation']}"
                if arg.get('default'):
                    arg_str += f" = {arg['default']}"
                args.append(arg_str)
            else:
                args.append(str(arg))

        return f"{func.name}({', '.join(args)})"

    def _get_source_code(self, func: FunctionInfo, context: FileAnalysis) -> str:
        """Récupère le code source d'une fonction."""
        # Lire le fichier et extraire les lignes
        try:
            with open(context.file_path, 'r') as f:
                lines = f.readlines()

            # Estimer la fin de la fonction (simplifié)
            start = func.lineno - 1
            end = min(start + 50, len(lines))  # Max 50 lignes

            return "".join(lines[start:end])
        except Exception:
            return "# Code source non disponible"

    def _get_class_source(self, cls: ClassInfo, context: FileAnalysis) -> str:
        """Récupère le code source d'une classe."""
        try:
            with open(context.file_path, 'r') as f:
                lines = f.readlines()

            start = cls.lineno - 1
            end = min(start + 100, len(lines))

            return "".join(lines[start:end])
        except Exception:
            return "# Code source non disponible"

    def _get_module_context(self, context: FileAnalysis) -> str:
        """Construit le contexte du module."""
        parts = []

        if context.imports:
            imports = [i.module for i in context.imports[:10]]
            parts.append(f"Imports: {', '.join(imports)}")

        if context.classes:
            classes = [c.name for c in context.classes]
            parts.append(f"Classes: {', '.join(classes)}")

        if context.functions:
            funcs = [f.name for f in context.functions[:10]]
            parts.append(f"Fonctions: {', '.join(funcs)}")

        return "\n".join(parts) if parts else "Module simple"

    def _clean_docstring(self, docstring: str) -> str:
        """Nettoie la docstring générée."""
        # Supprimer les guillemets si présents
        docstring = docstring.strip()
        if docstring.startswith('"""') or docstring.startswith("'''"):
            docstring = docstring[3:]
        if docstring.endswith('"""') or docstring.endswith("'''"):
            docstring = docstring[:-3]

        return docstring.strip()

    def _apply_docstrings(self, file_path: Path, results: dict):
        """Applique les docstrings au fichier (inplace)."""
        # TODO: Implémenter modification in-place avec AST
        # Pour l'instant, générer un fichier .documented.py
        pass
```

---

### 2.4.5 Diagrammes Mermaid - Base

**Fichier**: `src/hyperion/modules/documentation/v3_2/diagrams/mermaid_base.py`

```python
"""Base pour la génération de diagrammes Mermaid."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

from ..config import DiagramConfig


@dataclass
class MermaidNode:
    """Noeud dans un diagramme Mermaid."""
    id: str
    label: str
    type: str = "default"
    style: Optional[str] = None


@dataclass
class MermaidEdge:
    """Arête dans un diagramme Mermaid."""
    source: str
    target: str
    label: Optional[str] = None
    style: str = "-->"  # -->, -.->,-., ==>, etc.


class MermaidGenerator(ABC):
    """Classe de base pour les générateurs Mermaid."""

    def __init__(self, config: Optional[DiagramConfig] = None):
        self.config = config or DiagramConfig()
        self.nodes: List[MermaidNode] = []
        self.edges: List[MermaidEdge] = []

    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """Génère le diagramme Mermaid."""
        pass

    def _escape_label(self, label: str) -> str:
        """Échappe les caractères spéciaux dans les labels."""
        # Mermaid nécessite l'échappement de certains caractères
        label = label.replace('"', "'")
        label = label.replace('<', "&lt;")
        label = label.replace('>', "&gt;")
        label = label.replace('{', "&#123;")
        label = label.replace('}', "&#125;")
        return label

    def _sanitize_id(self, id: str) -> str:
        """Crée un ID valide pour Mermaid."""
        # Remplacer les caractères non-alphanumériques
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', id)

    def to_markdown(self, title: Optional[str] = None) -> str:
        """Génère le bloc Markdown avec le diagramme."""
        diagram = self.generate()
        parts = []

        if title:
            parts.append(f"## {title}\n")

        parts.append("```mermaid")
        parts.append(diagram)
        parts.append("```")

        return "\n".join(parts)
```

---

### 2.4.6 Diagramme de Classes

**Fichier**: `src/hyperion/modules/documentation/v3_2/diagrams/class_diagram.py`

```python
"""Génération de diagrammes de classes Mermaid."""

from typing import List, Optional
from pathlib import Path

from .mermaid_base import MermaidGenerator, MermaidNode, MermaidEdge
from ..config import DiagramConfig
from ....understanding.ast_parser import ASTParser, ClassInfo, FileAnalysis
from ....understanding.code_graph import CodeGraph


class ClassDiagramGenerator(MermaidGenerator):
    """Génère des diagrammes de classes depuis le code."""

    def __init__(self, config: Optional[DiagramConfig] = None):
        super().__init__(config)
        self.parser = ASTParser()

    def generate_from_file(self, file_path: Path) -> str:
        """Génère un diagramme de classes depuis un fichier."""
        analysis = self.parser.analyze_file(file_path)
        return self._generate_from_analysis(analysis)

    def generate_from_graph(self, graph: CodeGraph) -> str:
        """Génère un diagramme depuis un CodeGraph existant."""
        lines = ["classDiagram"]

        # Extraire les classes du graphe
        for node in graph.nodes:
            if node.type == "class":
                class_def = self._format_class_from_node(node)
                lines.extend(class_def)

        # Ajouter les relations
        for edge in graph.edges:
            if edge.type == "inherits":
                lines.append(f"    {edge.target} <|-- {edge.source}")
            elif edge.type == "contains":
                lines.append(f"    {edge.source} *-- {edge.target}")
            elif edge.type == "uses":
                lines.append(f"    {edge.source} ..> {edge.target}")

        return "\n".join(lines)

    def generate(self, classes: List[ClassInfo]) -> str:
        """Génère un diagramme depuis une liste de ClassInfo."""
        lines = ["classDiagram"]

        for cls in classes:
            if not self.config.show_private and cls.name.startswith('_'):
                continue

            lines.extend(self._format_class(cls))

        # Ajouter les relations d'héritage
        for cls in classes:
            for base in cls.bases:
                if base not in ('object', 'ABC'):
                    lines.append(f"    {base} <|-- {cls.name}")

        return "\n".join(lines)

    def _generate_from_analysis(self, analysis: FileAnalysis) -> str:
        """Génère depuis une FileAnalysis."""
        return self.generate(analysis.classes)

    def _format_class(self, cls: ClassInfo) -> List[str]:
        """Formate une classe pour Mermaid."""
        lines = []
        class_id = self._sanitize_id(cls.name)

        lines.append(f"    class {class_id} {{")

        # Attributs
        if self.config.show_attributes and cls.attributes:
            for attr in cls.attributes[:10]:  # Limiter
                visibility = "-" if attr.startswith('_') else "+"
                lines.append(f"        {visibility}{attr}")

        # Méthodes
        if self.config.show_methods and cls.methods:
            for method in cls.methods[:15]:  # Limiter
                visibility = "-" if method.name.startswith('_') else "+"
                args = self._format_method_args(method.args)
                lines.append(f"        {visibility}{method.name}({args})")

        lines.append("    }")

        # Ajouter annotation si abstraite
        if cls.is_abstract:
            lines.append(f"    <<abstract>> {class_id}")

        return lines

    def _format_class_from_node(self, node) -> List[str]:
        """Formate une classe depuis un CodeNode."""
        lines = []
        class_id = self._sanitize_id(node.name)

        lines.append(f"    class {class_id} {{")

        attrs = node.attributes.get("attributes", [])
        methods = node.attributes.get("methods", [])

        if self.config.show_attributes:
            for attr in attrs[:10]:
                lines.append(f"        +{attr}")

        if self.config.show_methods:
            for method in methods[:15]:
                lines.append(f"        +{method}()")

        lines.append("    }")

        return lines

    def _format_method_args(self, args: list) -> str:
        """Formate les arguments d'une méthode."""
        if not args:
            return ""

        formatted = []
        for arg in args[:3]:  # Max 3 args affichés
            if isinstance(arg, dict):
                formatted.append(arg.get('name', ''))
            else:
                formatted.append(str(arg))

        result = ", ".join(formatted)
        if len(args) > 3:
            result += ", ..."

        return result
```

---

### 2.4.7 Graphe de Dépendances

**Fichier**: `src/hyperion/modules/documentation/v3_2/diagrams/dependency_graph.py`

```python
"""Génération de graphes de dépendances Mermaid."""

from typing import List, Optional, Set
from pathlib import Path

from .mermaid_base import MermaidGenerator
from ..config import DiagramConfig
from ....understanding.ast_parser import ASTParser, FileAnalysis
from ....understanding.code_graph import CodeGraph


class DependencyGraphGenerator(MermaidGenerator):
    """Génère des graphes de dépendances depuis le code."""

    def __init__(self, config: Optional[DiagramConfig] = None):
        super().__init__(config)
        self.parser = ASTParser()

    def generate_from_directory(self, directory: Path) -> str:
        """Génère un graphe de dépendances pour un répertoire."""
        files = list(directory.rglob("*.py"))
        return self.generate_from_files(files)

    def generate_from_files(self, files: List[Path]) -> str:
        """Génère un graphe depuis une liste de fichiers."""
        lines = [f"flowchart {self.config.direction}"]

        # Analyser chaque fichier
        modules: Set[str] = set()
        dependencies: List[tuple] = []

        for file_path in files:
            try:
                analysis = self.parser.analyze_file(file_path)
                module_name = self._path_to_module(file_path)
                modules.add(module_name)

                for imp in analysis.imports:
                    if imp.module:
                        dep = self._normalize_import(imp.module)
                        dependencies.append((module_name, dep))
            except Exception:
                continue

        # Filtrer les dépendances internes
        internal_deps = [
            (src, dst) for src, dst in dependencies
            if dst in modules or self._is_internal(dst, modules)
        ]

        # Ajouter les noeuds
        for module in sorted(modules)[:self.config.max_nodes_per_diagram]:
            node_id = self._sanitize_id(module)
            label = module.split('.')[-1]  # Nom court
            lines.append(f"    {node_id}[{label}]")

        # Ajouter les arêtes
        added_edges: Set[tuple] = set()
        for src, dst in internal_deps:
            src_id = self._sanitize_id(src)
            dst_id = self._sanitize_id(dst)

            if (src_id, dst_id) not in added_edges and src_id != dst_id:
                lines.append(f"    {src_id} --> {dst_id}")
                added_edges.add((src_id, dst_id))

        return "\n".join(lines)

    def generate_from_graph(self, graph: CodeGraph) -> str:
        """Génère depuis un CodeGraph existant."""
        lines = [f"flowchart {self.config.direction}"]

        # Grouper par module si configuré
        if self.config.group_by_module:
            modules = self._group_by_module(graph)
            for module_name, nodes in modules.items():
                lines.append(f"    subgraph {self._sanitize_id(module_name)}[{module_name}]")
                for node in nodes[:10]:
                    node_id = self._sanitize_id(node.id)
                    lines.append(f"        {node_id}[{node.name}]")
                lines.append("    end")
        else:
            for node in graph.nodes[:self.config.max_nodes_per_diagram]:
                if node.type == "file":
                    node_id = self._sanitize_id(node.id)
                    label = Path(node.name).stem
                    lines.append(f"    {node_id}[{label}]")

        # Ajouter les arêtes d'import
        for edge in graph.edges:
            if edge.type == "imports":
                src_id = self._sanitize_id(edge.source)
                dst_id = self._sanitize_id(edge.target)
                lines.append(f"    {src_id} --> {dst_id}")

        return "\n".join(lines)

    def generate(self, analysis: FileAnalysis) -> str:
        """Génère pour un seul fichier."""
        lines = [f"flowchart {self.config.direction}"]

        module_name = Path(analysis.file_path).stem
        module_id = self._sanitize_id(module_name)

        lines.append(f"    {module_id}[{module_name}]")

        for imp in analysis.imports[:20]:
            if imp.module:
                dep_id = self._sanitize_id(imp.module)
                dep_label = imp.module.split('.')[-1]
                lines.append(f"    {dep_id}[{dep_label}]")
                lines.append(f"    {module_id} --> {dep_id}")

        return "\n".join(lines)

    def _path_to_module(self, file_path: Path) -> str:
        """Convertit un chemin en nom de module."""
        parts = file_path.with_suffix('').parts
        # Trouver le début du package
        try:
            src_idx = parts.index('src')
            return '.'.join(parts[src_idx + 1:])
        except ValueError:
            return '.'.join(parts[-3:])

    def _normalize_import(self, module: str) -> str:
        """Normalise un nom d'import."""
        return module.split('.')[0] if '.' in module else module

    def _is_internal(self, module: str, known_modules: Set[str]) -> bool:
        """Vérifie si un module est interne au projet."""
        for known in known_modules:
            if module.startswith(known.split('.')[0]):
                return True
        return False

    def _group_by_module(self, graph: CodeGraph) -> dict:
        """Groupe les noeuds par module parent."""
        groups = {}
        for node in graph.nodes:
            if node.file_path:
                module = Path(node.file_path).parent.name
                if module not in groups:
                    groups[module] = []
                groups[module].append(node)
        return groups
```

---

### 2.4.8 Générateur de README

**Fichier**: `src/hyperion/modules/documentation/v3_2/readme/generator.py`

```python
"""Générateur de README automatique."""

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from langchain_ollama import OllamaLLM

from ..config import DocumentationConfig
from ..docstring.prompts import README_SECTION_PROMPT
from ..diagrams.class_diagram import ClassDiagramGenerator
from ..diagrams.dependency_graph import DependencyGraphGenerator
from ....understanding.ast_parser import ASTParser
from ....understanding.code_graph import CodeGraph


class ReadmeGenerator:
    """Génère un README.md complet depuis l'analyse du code."""

    def __init__(self, config: Optional[DocumentationConfig] = None):
        self.config = config or DocumentationConfig()
        self.parser = ASTParser()

        self.llm = OllamaLLM(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            timeout=60  # Plus long pour README
        )

        self.class_diagram_gen = ClassDiagramGenerator()
        self.dep_graph_gen = DependencyGraphGenerator()

    def generate(
        self,
        project_path: Path,
        profile: Optional[Dict[str, Any]] = None,
        graph: Optional[CodeGraph] = None
    ) -> str:
        """Génère un README complet.

        Args:
            project_path: Racine du projet
            profile: Profil Hyperion du projet (optionnel)
            graph: CodeGraph du projet (optionnel)

        Returns:
            Contenu Markdown du README
        """
        # Collecter les informations
        info = self._collect_project_info(project_path, profile)

        sections = []

        # 1. Header
        sections.append(self._generate_header(info))

        # 2. Badges (si disponibles)
        sections.append(self._generate_badges(info))

        # 3. Description
        sections.append(self._generate_description(info))

        # 4. Architecture (avec diagramme)
        sections.append(self._generate_architecture(project_path, graph))

        # 5. Installation
        sections.append(self._generate_installation(info))

        # 6. Utilisation
        sections.append(self._generate_usage(info))

        # 7. Structure du projet
        sections.append(self._generate_structure(project_path))

        # 8. API (si applicable)
        if info.get("has_api"):
            sections.append(self._generate_api_section(info))

        # 9. Tests
        sections.append(self._generate_tests_section(info))

        # 10. Contributing
        sections.append(self._generate_contributing())

        # 11. License
        sections.append(self._generate_license(info))

        # Footer
        sections.append(self._generate_footer())

        return "\n\n".join(filter(None, sections))

    def _collect_project_info(
        self,
        project_path: Path,
        profile: Optional[Dict]
    ) -> Dict[str, Any]:
        """Collecte les informations du projet."""
        info = {
            "name": project_path.name,
            "path": project_path,
            "generated_at": datetime.now().isoformat(),
        }

        # Depuis le profil Hyperion
        if profile:
            info.update({
                "description": profile.get("description", ""),
                "technologies": profile.get("tech", {}),
                "metrics": profile.get("metrics", {}),
                "contributors": profile.get("git_summary", {}).get("contributors_top10", []),
            })

        # Détecter les fichiers de config
        info["has_api"] = (project_path / "src" / "hyperion" / "api").exists()
        info["has_tests"] = (project_path / "tests").exists()
        info["has_docker"] = (project_path / "Dockerfile").exists() or (project_path / "docker-compose.yml").exists()

        # pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            info["has_pyproject"] = True
            # TODO: Parser pyproject.toml pour plus d'infos

        # Compter les fichiers
        py_files = list(project_path.rglob("*.py"))
        info["file_count"] = len(py_files)
        info["loc"] = sum(self._count_lines(f) for f in py_files[:100])

        return info

    def _generate_header(self, info: Dict) -> str:
        """Génère le header du README."""
        name = info["name"]
        return f"# {name}\n"

    def _generate_badges(self, info: Dict) -> str:
        """Génère les badges."""
        badges = []

        if info.get("has_pyproject"):
            badges.append("![Python](https://img.shields.io/badge/python-3.10+-blue.svg)")

        if info.get("has_tests"):
            badges.append("![Tests](https://img.shields.io/badge/tests-passing-green.svg)")

        if info.get("has_docker"):
            badges.append("![Docker](https://img.shields.io/badge/docker-ready-blue.svg)")

        return " ".join(badges) if badges else ""

    def _generate_description(self, info: Dict) -> str:
        """Génère la description via LLM."""
        if info.get("description"):
            return f"## Description\n\n{info['description']}"

        # Générer via LLM
        prompt = f"""Génère une description courte (2-3 phrases) pour ce projet Python:

Nom: {info['name']}
Fichiers: {info.get('file_count', 'inconnu')}
Technologies: {info.get('technologies', {})}

Description:"""

        try:
            description = self.llm.invoke(prompt)
            return f"## Description\n\n{description.strip()}"
        except Exception:
            return "## Description\n\n*Description à ajouter*"

    def _generate_architecture(
        self,
        project_path: Path,
        graph: Optional[CodeGraph]
    ) -> str:
        """Génère la section architecture avec diagramme."""
        lines = ["## Architecture"]

        # Générer le diagramme de dépendances
        try:
            src_path = project_path / "src"
            if src_path.exists():
                diagram = self.dep_graph_gen.generate_from_directory(src_path)
                lines.append("\n```mermaid")
                lines.append(diagram)
                lines.append("```")
        except Exception:
            lines.append("\n*Diagramme non disponible*")

        return "\n".join(lines)

    def _generate_structure(self, project_path: Path) -> str:
        """Génère l'arborescence du projet."""
        lines = ["## Structure du Projet", "", "```"]

        # Générer l'arbre (simplifié)
        for item in sorted(project_path.iterdir()):
            if item.name.startswith('.'):
                continue
            if item.is_dir():
                lines.append(f"├── {item.name}/")
                # Premier niveau seulement
                for subitem in sorted(item.iterdir())[:5]:
                    if not subitem.name.startswith('.'):
                        lines.append(f"│   ├── {subitem.name}")
            else:
                lines.append(f"├── {item.name}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_installation(self, info: Dict) -> str:
        """Génère les instructions d'installation."""
        lines = ["## Installation", ""]

        if info.get("has_pyproject"):
            lines.extend([
                "```bash",
                f"git clone <repository-url>",
                f"cd {info['name']}",
                "pip install -e .",
                "```"
            ])
        else:
            lines.extend([
                "```bash",
                f"git clone <repository-url>",
                f"cd {info['name']}",
                "pip install -r requirements.txt",
                "```"
            ])

        return "\n".join(lines)

    def _generate_usage(self, info: Dict) -> str:
        """Génère les exemples d'utilisation."""
        lines = ["## Utilisation", ""]

        if info.get("has_api"):
            lines.extend([
                "### API",
                "",
                "```bash",
                "# Lancer le serveur",
                "uvicorn hyperion.api.main:app --reload",
                "```",
                "",
                "L'API sera disponible sur `http://localhost:8000`"
            ])

        return "\n".join(lines)

    def _generate_api_section(self, info: Dict) -> str:
        """Génère la section API."""
        return """## API

Documentation API disponible sur `/docs` (Swagger UI).

### Endpoints principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/chat` | POST | Chat RAG |
| `/api/health` | GET | Health check |
"""

    def _generate_tests_section(self, info: Dict) -> str:
        """Génère la section tests."""
        if not info.get("has_tests"):
            return ""

        return """## Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=src/hyperion
```
"""

    def _generate_contributing(self) -> str:
        """Génère la section contributing."""
        return """## Contribuer

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -m 'Ajoute nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request
"""

    def _generate_license(self, info: Dict) -> str:
        """Génère la section license."""
        return "## License\n\nApache-2.0"

    def _generate_footer(self) -> str:
        """Génère le footer."""
        return f"""---

*Documentation générée automatiquement par Hyperion v3.2*
"""

    def _count_lines(self, file_path: Path) -> int:
        """Compte les lignes d'un fichier."""
        try:
            with open(file_path, 'r', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
```

---

### 2.4.9 Orchestrateur Principal

**Fichier**: `src/hyperion/modules/documentation/v3_2/doc_generator.py`

```python
"""Orchestrateur principal de génération de documentation v3.2."""

from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from .config import DocumentationConfig, DiagramType
from .docstring.generator import DocstringGenerator
from .readme.generator import ReadmeGenerator
from .diagrams.class_diagram import ClassDiagramGenerator
from .diagrams.dependency_graph import DependencyGraphGenerator
from ...understanding.ast_parser import ASTParser
from ...understanding.code_graph import CodeGraph


@dataclass
class GenerationResult:
    """Résultat de génération de documentation."""
    success: bool
    output_path: Optional[Path]
    content: Optional[str]
    errors: List[str]
    stats: Dict[str, int]


class DocumentationOrchestrator:
    """Orchestre la génération de documentation complète."""

    def __init__(self, config: Optional[DocumentationConfig] = None):
        self.config = config or DocumentationConfig()

        # Générateurs
        self.docstring_gen = DocstringGenerator(self.config)
        self.readme_gen = ReadmeGenerator(self.config)
        self.class_diagram_gen = ClassDiagramGenerator()
        self.dep_graph_gen = DependencyGraphGenerator()

        # Parser
        self.parser = ASTParser()

    def generate_all(
        self,
        project_path: Path,
        profile: Optional[Dict[str, Any]] = None,
        graph: Optional[CodeGraph] = None
    ) -> Dict[str, GenerationResult]:
        """Génère toute la documentation du projet.

        Args:
            project_path: Racine du projet
            profile: Profil Hyperion (optionnel)
            graph: CodeGraph du projet (optionnel)

        Returns:
            Dict avec résultats par type de doc
        """
        results = {}

        # 1. README
        results["readme"] = self.generate_readme(project_path, profile, graph)

        # 2. Diagrammes
        results["diagrams"] = self.generate_diagrams(project_path, graph)

        # 3. Docstrings (rapport seulement, pas inplace par défaut)
        results["docstrings"] = self.generate_docstrings_report(project_path)

        return results

    def generate_readme(
        self,
        project_path: Path,
        profile: Optional[Dict] = None,
        graph: Optional[CodeGraph] = None
    ) -> GenerationResult:
        """Génère le README."""
        try:
            content = self.readme_gen.generate(project_path, profile, graph)
            output_path = self.config.output_dir / "README.md"

            with open(output_path, 'w') as f:
                f.write(content)

            return GenerationResult(
                success=True,
                output_path=output_path,
                content=content,
                errors=[],
                stats={"sections": content.count("## ")}
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                output_path=None,
                content=None,
                errors=[str(e)],
                stats={}
            )

    def generate_diagrams(
        self,
        project_path: Path,
        graph: Optional[CodeGraph] = None
    ) -> GenerationResult:
        """Génère tous les diagrammes."""
        errors = []
        diagrams_generated = 0
        output_dir = self.config.output_dir / "diagrams"
        output_dir.mkdir(exist_ok=True)

        # Diagramme de dépendances
        try:
            src_path = project_path / "src"
            if src_path.exists():
                deps = self.dep_graph_gen.generate_from_directory(src_path)
                deps_file = output_dir / "dependencies.md"
                with open(deps_file, 'w') as f:
                    f.write("# Graphe de Dépendances\n\n```mermaid\n")
                    f.write(deps)
                    f.write("\n```\n")
                diagrams_generated += 1
        except Exception as e:
            errors.append(f"Dépendances: {e}")

        # Diagramme de classes (par module)
        try:
            src_path = project_path / "src"
            if src_path.exists():
                for py_file in list(src_path.rglob("*.py"))[:20]:
                    try:
                        analysis = self.parser.analyze_file(py_file)
                        if analysis.classes:
                            diagram = self.class_diagram_gen.generate(analysis.classes)
                            module_name = py_file.stem
                            class_file = output_dir / f"classes_{module_name}.md"
                            with open(class_file, 'w') as f:
                                f.write(f"# Classes - {module_name}\n\n```mermaid\n")
                                f.write(diagram)
                                f.write("\n```\n")
                            diagrams_generated += 1
                    except Exception:
                        continue
        except Exception as e:
            errors.append(f"Classes: {e}")

        return GenerationResult(
            success=len(errors) == 0,
            output_path=output_dir,
            content=None,
            errors=errors,
            stats={"diagrams": diagrams_generated}
        )

    def generate_docstrings_report(
        self,
        project_path: Path
    ) -> GenerationResult:
        """Génère un rapport des docstrings manquantes/générées."""
        src_path = project_path / "src"
        if not src_path.exists():
            src_path = project_path

        stats = {
            "files_analyzed": 0,
            "functions_missing_docs": 0,
            "classes_missing_docs": 0,
            "docstrings_generated": 0,
        }
        errors = []

        report_lines = ["# Rapport Docstrings\n"]

        for py_file in list(src_path.rglob("*.py"))[:50]:
            try:
                result = self.docstring_gen.generate_for_file(py_file, inplace=False)
                stats["files_analyzed"] += 1

                if result["functions"] or result["classes"]:
                    report_lines.append(f"\n## {py_file.name}\n")

                    for func in result["functions"]:
                        stats["functions_missing_docs"] += 1
                        report_lines.append(f"\n### `{func['name']}` (ligne {func['lineno']})\n")
                        report_lines.append(f"```\n{func['docstring']}\n```\n")
                        stats["docstrings_generated"] += 1

                    for cls in result["classes"]:
                        stats["classes_missing_docs"] += 1
                        report_lines.append(f"\n### Class `{cls['name']}` (ligne {cls['lineno']})\n")
                        report_lines.append(f"```\n{cls['docstring']}\n```\n")
                        stats["docstrings_generated"] += 1

            except Exception as e:
                errors.append(f"{py_file.name}: {e}")

        # Sauvegarder le rapport
        report_content = "\n".join(report_lines)
        report_path = self.config.output_dir / "docstrings_report.md"

        with open(report_path, 'w') as f:
            f.write(report_content)

        return GenerationResult(
            success=True,
            output_path=report_path,
            content=report_content,
            errors=errors,
            stats=stats
        )

    def generate_docstrings_inplace(
        self,
        file_path: Path
    ) -> GenerationResult:
        """Génère et applique les docstrings à un fichier."""
        try:
            result = self.docstring_gen.generate_for_file(file_path, inplace=True)
            return GenerationResult(
                success=True,
                output_path=file_path,
                content=None,
                errors=[],
                stats={
                    "functions": len(result["functions"]),
                    "classes": len(result["classes"])
                }
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                output_path=None,
                content=None,
                errors=[str(e)],
                stats={}
            )
```

---

### 2.4.10 CLI v3.2

**Fichier**: `src/hyperion/cli/main.py` (ajouts)

```python
# Ajouter ces commandes au CLI existant

@cli.group()
def docs():
    """Commandes de génération de documentation v3.2."""
    pass


@docs.command("generate")
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", default="docs/generated", help="Répertoire de sortie")
@click.option("--profile", "-p", help="Chemin vers le profil Hyperion YAML")
def docs_generate(path: str, output: str, profile: str):
    """Génère la documentation complète du projet."""
    from pathlib import Path
    from hyperion.modules.documentation.v3_2.config import DocumentationConfig
    from hyperion.modules.documentation.v3_2.doc_generator import DocumentationOrchestrator

    config = DocumentationConfig(output_dir=Path(output))
    orchestrator = DocumentationOrchestrator(config)

    # Charger le profil si fourni
    profile_data = None
    if profile:
        import yaml
        with open(profile) as f:
            profile_data = yaml.safe_load(f)

    results = orchestrator.generate_all(Path(path), profile=profile_data)

    # Afficher les résultats
    for doc_type, result in results.items():
        status = "✓" if result.success else "✗"
        click.echo(f"{status} {doc_type}: {result.stats}")
        if result.errors:
            for err in result.errors:
                click.echo(f"  ⚠ {err}")


@docs.command("docstrings")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--style", type=click.Choice(["google", "numpy", "sphinx"]), default="google")
@click.option("--inplace", is_flag=True, help="Modifier le fichier directement")
def docs_docstrings(file_path: str, style: str, inplace: bool):
    """Génère les docstrings pour un fichier Python."""
    from pathlib import Path
    from hyperion.modules.documentation.v3_2.config import DocumentationConfig, DocstringStyle
    from hyperion.modules.documentation.v3_2.docstring.generator import DocstringGenerator

    config = DocumentationConfig(docstring_style=DocstringStyle(style))
    generator = DocstringGenerator(config)

    result = generator.generate_for_file(Path(file_path), inplace=inplace)

    click.echo(f"Fichier: {result['file']}")
    click.echo(f"Fonctions traitées: {len(result['functions'])}")
    click.echo(f"Classes traitées: {len(result['classes'])}")

    if not inplace:
        for func in result["functions"]:
            click.echo(f"\n--- {func['name']} (ligne {func['lineno']}) ---")
            click.echo(func["docstring"])


@docs.command("diagram")
@click.argument("path", type=click.Path(exists=True))
@click.option("--type", "diagram_type", type=click.Choice(["class", "deps"]), default="deps")
@click.option("--output", "-o", help="Fichier de sortie")
def docs_diagram(path: str, diagram_type: str, output: str):
    """Génère un diagramme Mermaid."""
    from pathlib import Path

    if diagram_type == "deps":
        from hyperion.modules.documentation.v3_2.diagrams.dependency_graph import DependencyGraphGenerator
        gen = DependencyGraphGenerator()
        diagram = gen.generate_from_directory(Path(path))
    else:
        from hyperion.modules.documentation.v3_2.diagrams.class_diagram import ClassDiagramGenerator
        from hyperion.modules.understanding.ast_parser import ASTParser
        gen = ClassDiagramGenerator()
        parser = ASTParser()
        analysis = parser.analyze_file(Path(path))
        diagram = gen.generate(analysis.classes)

    if output:
        with open(output, 'w') as f:
            f.write(f"```mermaid\n{diagram}\n```\n")
        click.echo(f"Diagramme sauvegardé: {output}")
    else:
        click.echo(diagram)


@docs.command("readme")
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", default="README.md")
@click.option("--profile", "-p", help="Profil Hyperion YAML")
def docs_readme(path: str, output: str, profile: str):
    """Génère un README.md automatiquement."""
    from pathlib import Path
    from hyperion.modules.documentation.v3_2.readme.generator import ReadmeGenerator

    generator = ReadmeGenerator()

    profile_data = None
    if profile:
        import yaml
        with open(profile) as f:
            profile_data = yaml.safe_load(f)

    readme = generator.generate(Path(path), profile=profile_data)

    with open(output, 'w') as f:
        f.write(readme)

    click.echo(f"README généré: {output}")
```

---

## 2.5 Tests v3.2

**Fichier**: `tests/unit/documentation/test_docstring_generator.py`

```python
"""Tests pour le générateur de docstrings."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from hyperion.modules.documentation.v3_2.config import DocumentationConfig, DocstringStyle
from hyperion.modules.documentation.v3_2.docstring.generator import DocstringGenerator


class TestDocstringGenerator:
    @pytest.fixture
    def generator(self):
        config = DocumentationConfig(docstring_style=DocstringStyle.GOOGLE)
        with patch.object(DocstringGenerator, '__init__', lambda x, y: None):
            gen = DocstringGenerator.__new__(DocstringGenerator)
            gen.config = config
            gen.llm = Mock()
            gen.parser = Mock()
            return gen

    def test_should_document_public_function(self, generator):
        func = Mock()
        func.name = "public_function"
        func.complexity = 5
        func.docstring = None

        assert generator._should_document(func) is True

    def test_should_not_document_private_function(self, generator):
        generator.config.include_private = False

        func = Mock()
        func.name = "_private_function"

        assert generator._should_document(func) is False

    def test_should_document_dunder_methods(self, generator):
        func = Mock()
        func.name = "__init__"
        func.complexity = 2
        func.docstring = None

        assert generator._should_document(func) is True


class TestClassDiagram:
    def test_generates_valid_mermaid(self):
        from hyperion.modules.documentation.v3_2.diagrams.class_diagram import ClassDiagramGenerator

        gen = ClassDiagramGenerator()

        # Mock classes
        class MockClass:
            name = "TestClass"
            bases = ["BaseClass"]
            methods = [Mock(name="method1", args=[]), Mock(name="method2", args=[])]
            attributes = ["attr1", "attr2"]
            is_abstract = False
            lineno = 1

        diagram = gen.generate([MockClass()])

        assert "classDiagram" in diagram
        assert "TestClass" in diagram
```

---

## 2.6 Résumé v3.2

| Composant | Fichiers | Lignes |
|-----------|----------|--------|
| Config | 1 | ~80 |
| Docstrings | 3 | ~300 |
| README | 2 | ~250 |
| Diagrams | 4 | ~350 |
| Orchestrator | 1 | ~200 |
| CLI | 1 | ~100 |
| Tests | 1 | ~50 |
| **Total** | **13** | **~1330** |

---

# PARTIE 3: Résumé Global

## 3.1 Vue d'Ensemble

| Version | Focus | Fichiers | Lignes | Dépendances |
|---------|-------|----------|--------|-------------|
| v3.1 | RAG Enhanced | 11 | ~720 | rank-bm25 |
| v3.2 | Documentation | 13 | ~1330 | aucune |
| **Total** | | **24** | **~2050** | **1** |

## 3.2 Ordre d'Implémentation Recommandé

### Phase 1: v3.1 Core (Priorité Haute)
1. `hybrid/tokenizer.py`
2. `hybrid/config.py`
3. `hybrid/bm25_index.py`
4. `hybrid/hybrid_search.py`
5. Tests hybrid

### Phase 2: v3.1 Re-ranking
6. `reranking/config.py`
7. `reranking/factors.py`
8. `reranking/simple_reranker.py`

### Phase 3: v3.1 Citations
9. `citations/claim_extractor.py`
10. `citations/verifier.py`

### Phase 4: v3.1 Intégration
11. Modifier `query.py`
12. Modifier `ingestion.py`
13. Tests intégration

### Phase 5: v3.2 Base
14. `v3_2/config.py`
15. `v3_2/docstring/styles.py`
16. `v3_2/docstring/prompts.py`

### Phase 6: v3.2 Docstrings
17. `v3_2/docstring/generator.py`

### Phase 7: v3.2 Diagrammes
18. `v3_2/diagrams/mermaid_base.py`
19. `v3_2/diagrams/class_diagram.py`
20. `v3_2/diagrams/dependency_graph.py`

### Phase 8: v3.2 README
21. `v3_2/readme/generator.py`

### Phase 9: v3.2 Orchestration
22. `v3_2/doc_generator.py`
23. CLI commands
24. Tests

## 3.3 Commandes CLI Finales

```bash
# v3.1 - RAG
hyperion chat "question" --hybrid          # Recherche hybride
hyperion chat "question" --verify-citations # Vérification citations

# v3.2 - Documentation
hyperion docs generate ./project           # Tout générer
hyperion docs docstrings file.py --inplace # Docstrings
hyperion docs diagram ./src --type deps    # Diagramme deps
hyperion docs diagram file.py --type class # Diagramme classes
hyperion docs readme ./project             # README auto
```

## 3.4 Métriques de Succès

| Métrique | Baseline | v3.1 | v3.2 |
|----------|----------|------|------|
| RAG Recall@10 | 65% | >75% | - |
| RAG Precision@5 | 70% | >80% | - |
| Citation Accuracy | 60% | >85% | - |
| Doc Coverage | 0% | - | >80% |
| Diagram Generation | 0% | - | 100% |
