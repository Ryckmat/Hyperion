---
title: "Code Understanding Engine"
toc: true
description: "Module : hyperion.modules.understanding"
weight: 2
---

**Module** : `hyperion.modules.understanding`
**Version** : **Component** : Code Understanding Engine

---

## Vue d'ensemble

Le module **Code Understanding Engine** permet de mapper les features business vers le code source, facilitant :
- Localisation rapide du code pour une fonctionnalité
- Onboarding développeurs (comprendre rapidement le code)
- Documentation automatique basée sur le code
- Recherche sémantique dans le codebase

## Architecture

```
understanding/
├── indexer.py        # Indexation code (docstrings, comments, AST)
├── mapper.py         # Mapping feature → code
└── query_engine.py   # Interface requêtes RAG
```

## Composants

### 1. CodeIndexer

**Responsabilité** : Indexation exhaustive du code source.

**Métadonnées extraites** :
- Docstrings (modules, classes, fonctions)
- Commentaires inline
- Signatures de fonctions
- Informations classes (héritage, méthodes)
- Imports

**Exemple d'usage** :
```python
from hyperion.modules.understanding import CodeIndexer

indexer = CodeIndexer("/path/to/repo")
code_index = indexer.index_repository()

# Accès aux métadonnées
file_metadata = code_index["src/api/main.py"]
print(file_metadata["docstrings"])
print(file_metadata["functions"])
```

### 2. FeatureMapper

**Responsabilité** : Mapper features business → code.

**Stratégie** :
1. Recherche par mots-clés dans docstrings/commentaires
2. Recherche sémantique via embeddings (à venir)
3. Scoring de pertinence

**Exemple d'usage** :
```python
from hyperion.modules.understanding import FeatureMapper

mapper = FeatureMapper(code_index)

# Trouver le code pour une feature
results = mapper.map_feature_to_code("calcul de remise client")

for result in results[:5]:
    print(f"{result['file']} (score: {result['score']:.2f})")
```

### 3. UnderstandingQueryEngine

**Responsabilité** : Interface unifiée pour requêtes.

**Capacités** :
- Répondre à des questions sur le code
- Trouver l'implémentation d'une feature
- Localiser les tests associés
- Trouver fichiers similaires

**Exemple d'usage** :
```python
from hyperion.modules.understanding import UnderstandingQueryEngine

engine = UnderstandingQueryEngine("/path/to/repo")

# Question naturelle
response = engine.query("Où est implémenté le calcul de TVA ?")
print(response["answer"])
print(f"Confiance: {response['confidence']:.2f}")

# Trouver implémentation
files = engine.find_implementation("authentification utilisateur")

# Trouver tests
tests = engine.find_tests("src/auth/login.py")
```

## Workflow complet

```python
from pathlib import Path
from hyperion.modules.understanding import (
    CodeIndexer,
    FeatureMapper,
    UnderstandingQueryEngine
)

# 1. Indexation
indexer = CodeIndexer("/path/to/repo")
code_index = indexer.index_repository()
print(f"Indexé {len(code_index)} fichiers")

# 2. Mapping
mapper = FeatureMapper(code_index)
results = mapper.map_feature_to_code("gestion des stocks")

# 3. Query engine
engine = UnderstandingQueryEngine("/path/to/repo")
response = engine.query("Comment fonctionne l'export PDF ?")

print(response["answer"])
for source in response["sources"]:
    print(f"  - {source['file']} (score: {source['score']:.2f})")
```

## Cas d'usage

### 1. Onboarding développeur

```python
# Générer learning path basé sur features principales
features = [
    "authentification",
    "gestion commandes",
    "export données"
]

for feature in features:
    results = mapper.map_feature_to_code(feature)
    print(f"\n📚 {feature}:")
    for r in results[:3]:
        print(f"  - {r['file']}")
```

### 2. Documentation automatique

```python
# Générer docs basées sur l'indexation
for file, metadata in code_index.items():
    if "api" in file:
        print(f"\n## {file}")
        if "module" in metadata["docstrings"]:
            print(metadata["docstrings"]["module"])
```

### 3. Recherche de code similaire

```python
# Trouver fichiers liés sémantiquement
related = engine.get_related_files("src/core/payments.py", max_results=5)
print("Fichiers similaires:")
for r in related:
    print(f"  - {r['file']} (similarité: {r['score']:.2f})")
```

## Intégration RAG

Le Code Understanding Engine s'intègre avec le RAG existant :

```python
from hyperion.modules.rag.query import RAGQueryEngine
from hyperion.modules.understanding import UnderstandingQueryEngine

# RAG pour profils Git
rag_engine = RAGQueryEngine()
git_response = rag_engine.query("Qui a le plus contribué ?")

# Understanding pour code
code_engine = UnderstandingQueryEngine("/path/to/repo")
code_response = code_engine.query("Où est le calcul de prix ?")

# Combinaison
print(f"Contributeur: {git_response['answer']}")
print(f"Localisation code: {code_response['answer']}")
```

## TODO

- [ ] Embeddings sémantiques (sentence-transformers)
- [ ] Support multi-langages
- [ ] Indexation tests unitaires
- [ ] Détection duplications code
- [ ] Interface web interactive

## Références

- AST parsing: `ast` module Python
- Embeddings: `sentence-transformers`
- Recherche: `Qdrant` vector database
