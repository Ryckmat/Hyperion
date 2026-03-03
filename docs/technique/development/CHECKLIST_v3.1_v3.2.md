# Checklist Implémentation v3.1 & v3.2

## v3.1 - RAG Enhanced

### Phase 1: Hybrid Search Core
- [ ] `src/hyperion/modules/rag/hybrid/__init__.py`
- [ ] `src/hyperion/modules/rag/hybrid/config.py`
- [ ] `src/hyperion/modules/rag/hybrid/tokenizer.py`
- [ ] `src/hyperion/modules/rag/hybrid/bm25_index.py`
- [ ] `src/hyperion/modules/rag/hybrid/hybrid_search.py`
- [ ] Ajouter `rank-bm25` dans `pyproject.toml`

### Phase 2: Re-ranking
- [ ] `src/hyperion/modules/rag/reranking/__init__.py`
- [ ] `src/hyperion/modules/rag/reranking/config.py`
- [ ] `src/hyperion/modules/rag/reranking/factors.py`
- [ ] `src/hyperion/modules/rag/reranking/simple_reranker.py`

### Phase 3: Citations
- [ ] `src/hyperion/modules/rag/citations/__init__.py`
- [ ] `src/hyperion/modules/rag/citations/claim_extractor.py`
- [ ] `src/hyperion/modules/rag/citations/verifier.py`

### Phase 4: Intégration
- [ ] Modifier `src/hyperion/modules/rag/query.py`
- [ ] Modifier `src/hyperion/modules/rag/ingestion.py`
- [ ] `tests/unit/rag/test_hybrid_search.py`
- [ ] `tests/unit/rag/test_reranker.py`
- [ ] `tests/unit/rag/test_citations.py`

### Phase 5: Validation v3.1
- [ ] Tests unitaires passent
- [ ] Tests intégration passent
- [ ] Benchmark recall/precision
- [ ] Documentation mise à jour

---

## v3.2 - Documentation Intelligence

### Phase 6: Configuration
- [ ] `src/hyperion/modules/documentation/v3_2/__init__.py`
- [ ] `src/hyperion/modules/documentation/v3_2/config.py`

### Phase 7: Docstrings
- [ ] `src/hyperion/modules/documentation/v3_2/docstring/__init__.py`
- [ ] `src/hyperion/modules/documentation/v3_2/docstring/styles.py`
- [ ] `src/hyperion/modules/documentation/v3_2/docstring/prompts.py`
- [ ] `src/hyperion/modules/documentation/v3_2/docstring/generator.py`

### Phase 8: Diagrammes
- [ ] `src/hyperion/modules/documentation/v3_2/diagrams/__init__.py`
- [ ] `src/hyperion/modules/documentation/v3_2/diagrams/mermaid_base.py`
- [ ] `src/hyperion/modules/documentation/v3_2/diagrams/class_diagram.py`
- [ ] `src/hyperion/modules/documentation/v3_2/diagrams/dependency_graph.py`
- [ ] `src/hyperion/modules/documentation/v3_2/diagrams/sequence_diagram.py` (optionnel)

### Phase 9: README Generator
- [ ] `src/hyperion/modules/documentation/v3_2/readme/__init__.py`
- [ ] `src/hyperion/modules/documentation/v3_2/readme/generator.py`
- [ ] `src/hyperion/modules/documentation/v3_2/readme/templates.py` (optionnel)

### Phase 10: Orchestration
- [ ] `src/hyperion/modules/documentation/v3_2/doc_generator.py`

### Phase 11: CLI
- [ ] Ajouter groupe `docs` dans `src/hyperion/cli/main.py`
- [ ] Commande `docs generate`
- [ ] Commande `docs docstrings`
- [ ] Commande `docs diagram`
- [ ] Commande `docs readme`

### Phase 12: Tests v3.2
- [ ] `tests/unit/documentation/test_docstring_generator.py`
- [ ] `tests/unit/documentation/test_diagrams.py`
- [ ] `tests/unit/documentation/test_readme.py`

### Phase 13: Validation v3.2
- [ ] Tests unitaires passent
- [ ] Génération README fonctionne
- [ ] Diagrammes Mermaid valides
- [ ] Documentation mise à jour

---

## Résumé Fichiers à Créer

### v3.1 (11 fichiers)
```
src/hyperion/modules/rag/
├── hybrid/
│   ├── __init__.py
│   ├── config.py
│   ├── tokenizer.py
│   ├── bm25_index.py
│   └── hybrid_search.py
├── reranking/
│   ├── __init__.py
│   ├── config.py
│   ├── factors.py
│   └── simple_reranker.py
└── citations/
    ├── __init__.py
    ├── claim_extractor.py
    └── verifier.py
```

### v3.2 (13 fichiers)
```
src/hyperion/modules/documentation/v3_2/
├── __init__.py
├── config.py
├── doc_generator.py
├── docstring/
│   ├── __init__.py
│   ├── styles.py
│   ├── prompts.py
│   └── generator.py
├── diagrams/
│   ├── __init__.py
│   ├── mermaid_base.py
│   ├── class_diagram.py
│   └── dependency_graph.py
└── readme/
    ├── __init__.py
    └── generator.py
```

---

## Commandes de Test

```bash
# v3.1
pytest tests/unit/rag/test_hybrid_search.py -v
pytest tests/unit/rag/test_reranker.py -v
pytest tests/unit/rag/test_citations.py -v

# v3.2
pytest tests/unit/documentation/ -v

# Tout
pytest tests/unit/ -v --cov=src/hyperion
```

---

## Notes

- v3.1 dépend de `rank-bm25` (seule nouvelle dépendance)
- v3.2 utilise les modules existants (understanding, langchain-ollama)
- Les deux versions sont indépendantes et peuvent être implémentées en parallèle
- Priorité: v3.1 d'abord (améliore le core RAG)
