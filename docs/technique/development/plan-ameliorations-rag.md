---
title: "Hyperion - Améliorations RAG"
toc: true
description: "Actuellement Hyperion utilise uniquement Qdrant (recherche vectorielle). Ajouter BM25 améliore le recall de 15-20% sur les termes techniques exacts."
weight: 4
---

## Vue d'ensemble

**Objectif**: Améliorer la qualité du pipeline RAG existant avec des techniques éprouvées.

**Version cible**: **Base**: Enterprise Ready
**Inspiration sélective**: Techniques RAG de [Docify](https://github.com/keshavashiya/docify)

> **Note**: Docify est un RAG documentaire, pas un générateur de docs. Seules les techniques RAG pertinentes sont retenues.

---

## Ce qui est retenu vs ignoré

| Concept Docify | Retenu ? | Raison |
|----------------|----------|--------|
| Recherche Hybride BM25+Vector | ✅ Oui | Améliore recall significativement |
| Re-ranking multi-facteurs | ✅ Oui | Meilleure précision |
| Query Expansion | ⚠️ Optionnel | Utile mais coût LLM |
| Vérification citations | ✅ Oui | Réduit hallucinations |
| Parsers PDF/URL | ❌ Non | Hors scope Hyperion |
| Architecture 11 étapes | ❌ Non | Over-engineering |

---

## Phase 1: Recherche Hybride (Priorité Haute)

### Pourquoi ?
Actuellement Hyperion utilise uniquement Qdrant (recherche vectorielle). Ajouter BM25 améliore le recall de 15-20% sur les termes techniques exacts.

### Structure

```
src/hyperion/modules/rag/hybrid/
├── __init__.py
├── bm25_index.py        # Index BM25 avec rank-bm25
├── hybrid_search.py     # Fusion RRF
└── config.py
```

### Implémentation

```python
from rank_bm25 import BM25Okapi
from dataclasses import dataclass

@dataclass
class HybridConfig:
    vector_weight: float = 0.6
    bm25_weight: float = 0.4
    rrf_k: int = 60  # Constante RRF


class HybridSearchEngine:
    """Combine recherche vectorielle Qdrant + BM25."""

    def __init__(self, qdrant_client, config: HybridConfig):
        self.qdrant = qdrant_client
        self.bm25: BM25Okapi | None = None
        self.config = config
        self.corpus = []
        self.doc_ids = []

    def build_bm25_index(self, chunks: list[dict]):
        """Construit l'index BM25 à partir des chunks existants."""
        tokenized = [self._tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)
        self.corpus = chunks
        self.doc_ids = [c["id"] for c in chunks]

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Recherche hybride avec fusion RRF."""
        # Recherche vectorielle
        vector_results = self._vector_search(query, top_k * 2)

        # Recherche BM25
        bm25_results = self._bm25_search(query, top_k * 2)

        # Fusion RRF
        return self._rrf_fusion(vector_results, bm25_results, top_k)

    def _rrf_fusion(self, vec_results, bm25_results, top_k) -> list[dict]:
        """Reciprocal Rank Fusion."""
        scores = {}
        k = self.config.rrf_k

        for rank, r in enumerate(vec_results):
            scores[r["id"]] = scores.get(r["id"], 0) + self.config.vector_weight / (k + rank + 1)

        for rank, r in enumerate(bm25_results):
            scores[r["id"]] = scores.get(r["id"], 0) + self.config.bm25_weight / (k + rank + 1)

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [self._get_doc(id) for id in sorted_ids[:top_k]]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenization simple pour code."""
        import re
        # Split sur espaces, underscores, camelCase
        tokens = re.split(r'[\s_]+|(?<=[a-z])(?=[A-Z])', text.lower())
        return [t for t in tokens if len(t) > 2]
```

### Dépendance

```toml
# pyproject.toml
rank-bm25 = "^0.2.2"
```

---

## Phase 2: Re-ranking Simple (Priorité Moyenne)

### Pourquoi ?
Le re-ranking améliore la précision en recalculant la pertinence après la recherche initiale.

### Implémentation légère

```python
@dataclass
class RerankerConfig:
    semantic_weight: float = 0.5
    recency_weight: float = 0.2
    source_weight: float = 0.3


class SimpleReranker:
    """Re-ranking basé sur 3 facteurs."""

    def __init__(self, embedder, config: RerankerConfig):
        self.embedder = embedder
        self.config = config

    def rerank(self, query: str, results: list[dict], top_k: int = 5) -> list[dict]:
        """Re-rank les résultats."""
        query_emb = self.embedder.encode(query)

        scored = []
        for r in results:
            score = self._compute_score(query_emb, r)
            scored.append((r, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in scored[:top_k]]

    def _compute_score(self, query_emb, result: dict) -> float:
        """Score composite."""
        # Similarité sémantique
        if "embedding" in result:
            from numpy import dot
            from numpy.linalg import norm
            sem_score = dot(query_emb, result["embedding"]) / (norm(query_emb) * norm(result["embedding"]))
        else:
            sem_score = result.get("score", 0.5)

        # Fraîcheur (si timestamp disponible)
        recency_score = self._recency_score(result.get("timestamp"))

        # Type de source (code > docs > comments)
        source_score = self._source_score(result.get("section", ""))

        return (
            self.config.semantic_weight * sem_score +
            self.config.recency_weight * recency_score +
            self.config.source_weight * source_score
        )

    def _source_score(self, section: str) -> float:
        """Score par type de source."""
        scores = {
            "functions": 1.0,
            "classes": 0.9,
            "overview": 0.8,
            "metrics": 0.6,
            "contributors": 0.4,
        }
        return scores.get(section, 0.5)
```

---

## Phase 3: Vérification Citations (Priorité Haute)

### Pourquoi ?
Réduit les hallucinations en validant que les réponses sont supportées par les sources.

### Implémentation

```python
@dataclass
class CitationResult:
    claim: str
    source_id: str | None
    confidence: float
    verified: bool


class CitationVerifier:
    """Vérifie les citations contre les sources."""

    def __init__(self, embedder, threshold: float = 0.7):
        self.embedder = embedder
        self.threshold = threshold

    def verify(self, response: str, sources: list[dict]) -> dict:
        """Vérifie que la réponse est supportée par les sources."""
        # Extraction claims simples (phrases)
        claims = [s.strip() for s in response.split('.') if len(s.strip()) > 20]

        results = []
        for claim in claims:
            best_match = self._find_best_source(claim, sources)
            results.append(CitationResult(
                claim=claim,
                source_id=best_match["id"] if best_match else None,
                confidence=best_match["score"] if best_match else 0.0,
                verified=best_match["score"] > self.threshold if best_match else False
            ))

        verified_count = sum(1 for r in results if r.verified)
        return {
            "claims": results,
            "overall_confidence": verified_count / len(results) if results else 1.0,
            "unverified_count": len(results) - verified_count
        }

    def _find_best_source(self, claim: str, sources: list[dict]) -> dict | None:
        """Trouve la source la plus proche."""
        claim_emb = self.embedder.encode(claim)

        best = None
        best_score = 0

        for source in sources:
            source_emb = self.embedder.encode(source["text"][:500])
            score = self._cosine_sim(claim_emb, source_emb)
            if score > best_score:
                best_score = score
                best = {"id": source["id"], "score": score}

        return best
```

---

## Intégration dans le Pipeline Existant

### Modification de `modules/rag/query.py`

```python
class RAGQueryEngine:
    def __init__(self, config: RAGConfig):
        # ... existing code ...

        # additions
        self.hybrid_search = HybridSearchEngine(self.qdrant_client, HybridConfig())
        self.reranker = SimpleReranker(self.embedder, RerankerConfig())
        self.citation_verifier = CitationVerifier(self.embedder)

    def query(self, question: str, repo: str = None) -> dict:
        # 1. Recherche hybride (remplace recherche simple)
        results = self.hybrid_search.search(question, top_k=20)

        # 2. Re-ranking
        results = self.reranker.rerank(question, results, top_k=5)

        # 3. Génération réponse (existant)
        response = self._generate_response(question, results)

        # 4. Vérification citations
        citation_check = self.citation_verifier.verify(response, results)

        return {
            "response": response,
            "sources": results,
            "citation_confidence": citation_check["overall_confidence"],
            "unverified_claims": citation_check["unverified_count"]
        }
```

---

## Métriques de Succès

| Métrique | | Cible |
|----------|------|------------|
| Recall@10 | ~65% | >75% |
| Precision@5 | ~70% | >80% |
| Réponses avec sources | ~60% | >85% |

---

## Ce qui n'est PAS dans

- ❌ Query Expansion LLM (coût trop élevé pour le gain)
- ❌ Pipeline 12 étapes (over-engineering)
- ❌ Parsers PDF/URL (hors scope)
- ❌ Déduplication sémantique (complexité)
- ❌ Conflict Detection (peut-être)

---

## Dépendances Ajoutées

```toml
[project.dependencies]
rank-bm25 = "^0.2.2"
```

C'est tout. Pas de nouvelles dépendances lourdes.

---

## Effort Estimé

| Phase | Composant | Complexité |
|-------|-----------|------------|
| 1 | Hybrid Search | Modérée |
| 2 | Re-ranking | Légère |
| 3 | Citation Verify | Légère |
| **Total** | | **~3 fichiers, ~300 lignes** |
