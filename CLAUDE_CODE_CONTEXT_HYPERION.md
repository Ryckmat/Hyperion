# 🧠 HYPERION v3.0 — Contexte Claude Code

> **Document de référence pour Claude Code**
> Version: 3.0.0-dev | Dernière mise à jour: 2025-01-01

---

## 📋 TABLE DES MATIÈRES

1. [Présentation du Projet](#1-présentation-du-projet)
2. [Architecture Actuelle](#2-architecture-actuelle)
3. [Problèmes à Corriger (P0/P1/P2)](#3-problèmes-à-corriger)
4. [Améliorations à Implémenter](#4-améliorations-à-implémenter)
5. [Fichiers Clés et Leur Rôle](#5-fichiers-clés-et-leur-rôle)
6. [Conventions et Règles de Code](#6-conventions-et-règles-de-code)
7. [Stack Technique](#7-stack-technique)
8. [Commandes Essentielles](#8-commandes-essentielles)

---

## 1. PRÉSENTATION DU PROJET

### 1.1 Vision

**Hyperion** est une plateforme d'intelligence locale pour repositories Git, combinant :

- **Analyse Git** : commits, contributeurs, hotspots, métriques
- **RAG Pipeline** : recherche sémantique avec validation qualité
- **Knowledge Graph** : Neo4j pour les relations de code
- **LLM Local** : Ollama pour l'inférence (Qwen 2.5 32B)
- **Architecture Enterprise** : 8 microservices, API Gateway, monitoring

### 1.2 Objectifs Stratégiques

| Objectif | Description | Statut |
|----------|-------------|--------|
| Code Intelligence | Compréhension sémantique du code via AST | 🔴 À implémenter |
| Impact Analysis | Prédiction des effets de changements | 🟡 Partiel |
| RAG Accuracy | 80%+ de précision sur les réponses | 🟡 21.8% actuel |
| Zero Cloud | 100% local, 0€/mois | ✅ Atteint |
| Enterprise Ready | Auth, audit, RBAC, monitoring | 🟡 Partiel |

### 1.3 Contraintes Techniques

```yaml
hardware:
  gpu: RTX 4090
  cpu_cores: 32
  ram: 30GB
  os: Manjaro Linux

performance_slos:
  rag_query_response: < 5s
  api_latency_p95: < 1s
  cold_start: < 30s
```

---

## 2. ARCHITECTURE ACTUELLE

### 2.1 Structure du Repository

```
Hyperion/
├── src/hyperion/                    # Code source principal
│   ├── __init__.py
│   ├── __version__.py               # ⚠️ Version 3.0.0-dev
│   ├── config.py                    # Configuration centralisée
│   ├── api/                         # API FastAPI
│   │   ├── main.py                  # Endpoints principaux
│   │   ├── openai_compat.py         # Compatibilité OpenAI
│   │   └── v2_endpoints.py          # Endpoints v2
│   ├── cli/
│   │   └── main.py                  # CLI Click
│   ├── core/
│   │   └── git_analyzer.py          # Analyseur Git principal
│   ├── modules/
│   │   ├── analytics/v2_9/          # Analytics Engine
│   │   ├── anomaly/                 # Détection d'anomalies
│   │   ├── cache/v3_0/              # Cache distribué L1/L2
│   │   ├── capacity/                # Estimation de capacité
│   │   ├── documentation/           # Génération de docs
│   │   ├── gateway/v3_0/            # API Gateway
│   │   ├── generators/              # Générateurs Markdown
│   │   ├── impact/                  # Analyse d'impact
│   │   ├── integrations/            # Neo4j ingesters
│   │   ├── ml/                      # Infrastructure ML
│   │   │   ├── infrastructure/      # Feature store, registry
│   │   │   ├── training/            # Pipelines d'entraînement
│   │   │   └── v2_9/                # Modèles v2.9
│   │   ├── monitoring/              # Prometheus, logs
│   │   ├── onboarding/              # Recommandations
│   │   ├── rag/                     # Pipeline RAG
│   │   │   ├── quality/             # Validation qualité
│   │   │   ├── monitoring/          # Métriques qualité
│   │   │   └── v2_9/                # Enhanced RAG
│   │   ├── refactoring/             # Suggestions refactoring
│   │   ├── security/v3_0/           # Auth JWT/TOTP/RBAC
│   │   └── understanding/           # Code understanding
│   └── utils/
│       └── git_utils.py             # Utilitaires Git
├── tests/                           # Tests (189 tests)
├── docs/                            # Documentation
├── scripts/                         # Scripts d'orchestration
├── config/                          # Configuration YAML
├── data/                            # Données et profils
├── mlruns/                          # MLflow runs
└── modeles/                         # Modèles ML entraînés
```

### 2.2 Services Docker (8 microservices)

```yaml
services:
  core:
    - qdrant         # Vector DB (port 6333)
    - ollama         # LLM Server (port 11434)
    - hyperion-api   # API principale (port 8000)

  optional:
    - neo4j          # Graph DB (ports 7474, 7687)
    - hyperion-dashboard  # React (port 3000)
    - open-webui     # Chat UI (port 3001)
    - prometheus     # Monitoring (port 9090)
    - mlflow         # ML Platform (port 5000)
```

### 2.3 Flux de Données

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Git Repo  │────▶│  Analyzer   │────▶│   Profile   │
└─────────────┘     └─────────────┘     │   (YAML)    │
                                        └──────┬──────┘
                                               │
        ┌──────────────────────────────────────┼──────────────────────────────────────┐
        │                                      │                                      │
        ▼                                      ▼                                      ▼
┌───────────────┐                    ┌─────────────────┐                    ┌─────────────────┐
│    Qdrant     │                    │     Neo4j       │                    │     MLflow      │
│   (Vectors)   │                    │    (Graph)      │                    │    (Models)     │
└───────┬───────┘                    └────────┬────────┘                    └────────┬────────┘
        │                                     │                                      │
        └─────────────────────────────────────┼──────────────────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   API Gateway   │
                                    │   (FastAPI)     │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
            ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
            │     CLI     │          │  Dashboard  │          │   WebUI     │
            └─────────────┘          └─────────────┘          └─────────────┘
```

---

## 3. PROBLÈMES À CORRIGER

### 🔴 P0 — Corrections Indispensables

#### 3.1 Incohérence des Versions

**Constat** : Désalignement entre les fichiers de version

| Fichier | Version Actuelle | Version Cible |
|---------|-----------------|---------------|
| `pyproject.toml` | `2.7.0` | `3.0.0` |
| `src/hyperion/__version__.py` | `3.0.0-dev` | `3.0.0` |
| `docker-compose.yml` (commentaire) | `v2.7` | `v3.0` |

**Correction** :

```python
# Option 1 : Source unique dans pyproject.toml (RECOMMANDÉ)
# pyproject.toml
[project]
version = "3.0.0"

# src/hyperion/__version__.py
from importlib.metadata import version
__version__ = version("hyperion")

# Option 2 : Garder __version__.py comme source
# Mettre à jour pyproject.toml avec dynamic = ["version"]
```

**Fichiers à modifier** :
- `pyproject.toml` : ligne 7
- `src/hyperion/__version__.py` : ligne 1
- `docker-compose.yml` : ligne 4 (commentaire)

---

#### 3.2 Point d'Entrée Unique Non Défini

**Constat** : Multiples façons de lancer (CLI, scripts, docker-compose)

**Correction** :
1. Définir UN seul point d'entrée officiel
2. Documenter clairement dans README

```bash
# Point d'entrée recommandé
hyperion server    # Lance l'API Gateway
hyperion api       # Lance le service API local
hyperion services  # Lance tous les services Docker
```

**Fichiers à modifier** :
- `src/hyperion/cli/main.py` : ajouter commandes `server`, `services`
- `README.md` : clarifier la section démarrage

---

#### 3.3 Gestion des Secrets

**Constat** : `.env.example` correct mais pas de scan CI pour secrets

**Correction** :

```yaml
# .github/workflows/ci.yml - Ajouter
- name: Scan for secrets
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Fichiers à créer/modifier** :
- `.github/workflows/ci.yml` : ajouter job gitleaks
- `.gitleaks.toml` : configuration du scan

---

### 🟠 P1 — Corrections Qualité Code

#### 3.4 Configuration Centralisée Typée

**Constat** : `config.py` utilise `os.getenv()` sans validation de type

**Correction** : Migrer vers `pydantic-settings`

```python
# src/hyperion/settings.py (NOUVEAU)
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="")
    neo4j_database: str = Field(default="neo4j")

    # RAG
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection: str = Field(default="hyperion_repos")

    # Embeddings
    embedding_model: str = Field(default="BAAI/bge-large-en-v1.5")
    embedding_device: str = Field(default="cuda")
    embedding_dim: int = Field(default=1024)

    # LLM
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen2.5:32b")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens: int = Field(default=2048)

    # Performance
    batch_size_commits: int = Field(default=500)
    batch_size_files: int = Field(default=2000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

**Fichiers à créer/modifier** :
- `src/hyperion/settings.py` : nouveau fichier
- `src/hyperion/config.py` : adapter pour importer settings
- `pyproject.toml` : ajouter `pydantic-settings` aux dépendances

---

#### 3.5 Logging Structuré + Request ID

**Constat** : Logs non structurés, pas de correlation ID

**Correction** :

```python
# src/hyperion/modules/monitoring/logging/json_logger.py (MODIFIER)
import structlog
from uuid import uuid4

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# Middleware pour request_id
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    with structlog.contextvars.bind_contextvars(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
    return response
```

**Fichiers à modifier** :
- `src/hyperion/modules/monitoring/logging/structured_logger.py`
- `src/hyperion/api/main.py` : ajouter middleware

---

#### 3.6 Délimitation Enterprise/Legacy

**Constat** : Dossiers `v2_9/`, `v3_0/` mélangés sans clarté

**Correction** : Réorganiser en modules clairs

```
src/hyperion/modules/
├── enterprise/           # v3.0 production-ready
│   ├── gateway/
│   ├── cache/
│   ├── security/
│   └── monitoring/
├── core/                 # Fonctionnalités stables
│   ├── rag/
│   ├── analytics/
│   └── ml/
└── experimental/         # Fonctionnalités en développement
    └── ...
```

**Alternative (moins invasive)** : Ajouter un `STATUS.md` par module

```markdown
# src/hyperion/modules/gateway/v3_0/STATUS.md
status: production
version: 3.0.0
tests: 95%
dependencies:
  - security/v3_0
  - cache/v3_0
```

---

### 🟢 P2 — Améliorations Fonctionnelles

#### 3.7 Harnais d'Évaluation RAG

**Constat** : Pas de framework d'évaluation systématique

**Correction** : Créer `eval/`

```
eval/
├── suites/
│   ├── core.yaml           # Suite de base
│   ├── rag_accuracy.yaml   # Tests RAG
│   └── hallucination.yaml  # Tests hallucinations
├── datasets/
│   ├── questions.json      # Questions de référence
│   └── expected.json       # Réponses attendues
├── metrics/
│   └── reporter.py         # Génération rapports
└── run.py                  # Point d'entrée
```

**Fichier exemple** `eval/suites/core.yaml` :

```yaml
name: core-evaluation
version: "1.0.0"
description: Suite d'évaluation de base pour Hyperion RAG

metrics:
  - latency_ms
  - confidence_score
  - source_coverage
  - hallucination_rate

tests:
  - id: basic_commit_count
    question: "Combien de commits dans le repository?"
    expected_type: numeric
    min_confidence: 0.8
    max_latency_ms: 3000

  - id: contributor_list
    question: "Qui sont les contributeurs principaux?"
    expected_type: list
    min_confidence: 0.7
    source_required: true

  - id: architecture_overview
    question: "Décris l'architecture du projet"
    expected_type: text
    min_length: 100
    hallucination_check: true
```

**Commande CLI** :

```bash
hyperion eval run --suite core --output json
hyperion eval report --format html
```

**Fichiers à créer** :
- `eval/` : nouveau dossier complet
- `src/hyperion/cli/main.py` : ajouter commande `eval`

---

#### 3.8 Labs Reproductibles

**Correction** : Créer 5 labs de démonstration

```
labs/
├── 01_repo_profile/
│   ├── README.md
│   ├── .env.example
│   └── run.sh
├── 02_rag_basics/
│   ├── README.md
│   ├── .env.example
│   └── run.sh
├── 03_gateway_security/
│   ├── README.md
│   ├── .env.example
│   └── run.sh
├── 04_quality_gates/
│   ├── README.md
│   ├── .env.example
│   └── run.sh
└── 05_enterprise_stack/
    ├── README.md
    ├── .env.example
    └── docker-compose.lab.yml
```

**Fichiers à créer** : Dossier `labs/` complet

---

#### 3.9 Contrat API OpenAI-Compatible

**Correction** : Documenter et stabiliser l'API

```yaml
# docs/api/openai-compat-spec.yaml
openapi: 3.0.0
info:
  title: Hyperion OpenAI Compatible API
  version: 1.0.0

paths:
  /v1/models:
    get:
      summary: Liste des modèles disponibles
      responses:
        200:
          description: Liste des modèles

  /v1/chat/completions:
    post:
      summary: Génération de réponse chat
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                  enum: [hyperion-rag, hyperion-code]
                messages:
                  type: array
                stream:
                  type: boolean
                  default: false
      responses:
        200:
          description: Réponse générée

limitations:
  streaming: true  # Supporté
  tools: false     # Non supporté actuellement
  vision: false    # Non supporté
```

**Fichiers à créer** :
- `docs/api/openai-compat-spec.yaml`
- `src/hyperion/api/openai_compat.py` : enrichir

---

## 4. AMÉLIORATIONS À IMPLÉMENTER

### 4.1 Parsing AST pour Code Intelligence

**Objectif** : Analyse réelle du code source (pas seulement métadonnées)

```python
# src/hyperion/modules/understanding/ast_parser.py (NOUVEAU)
import ast
from typing import Dict, List, Any

class PythonASTParser:
    """Parser AST pour Python."""

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse un fichier Python et extrait les éléments."""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())

        return {
            "functions": self._extract_functions(tree),
            "classes": self._extract_classes(tree),
            "imports": self._extract_imports(tree),
            "dependencies": self._extract_dependencies(tree),
            "complexity": self._calculate_complexity(tree)
        }

    def _extract_functions(self, tree: ast.AST) -> List[Dict]:
        """Extrait les définitions de fonctions."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "calls": self._extract_calls(node)
                })
        return functions
```

**Fichiers à créer** :
- `src/hyperion/modules/understanding/ast_parser.py`
- `src/hyperion/modules/understanding/code_graph.py`

---

### 4.2 Intégration Métriques Code Quality

**Objectif** : Intégrer radon, pylint pour métriques

```python
# src/hyperion/modules/quality/code_metrics.py (NOUVEAU)
from radon.complexity import cc_visit
from radon.metrics import mi_visit
import subprocess
import json

class CodeMetricsAnalyzer:
    """Analyse de la qualité du code."""

    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """Analyse la complexité cyclomatique."""
        blocks = cc_visit(code)
        return {
            "blocks": [
                {
                    "name": block.name,
                    "complexity": block.complexity,
                    "rank": block.rank
                }
                for block in blocks
            ],
            "total_complexity": sum(b.complexity for b in blocks),
            "average_complexity": sum(b.complexity for b in blocks) / len(blocks) if blocks else 0
        }

    def analyze_maintainability(self, code: str) -> float:
        """Calcule l'index de maintenabilité."""
        return mi_visit(code, True)

    def run_pylint(self, file_path: str) -> Dict[str, Any]:
        """Exécute pylint et retourne les résultats."""
        result = subprocess.run(
            ["pylint", "--output-format=json", file_path],
            capture_output=True, text=True
        )
        return json.loads(result.stdout) if result.stdout else []
```

**Dépendances à ajouter** :
```toml
# pyproject.toml
[project.optional-dependencies]
quality = [
    "radon>=5.1.0",
    "pylint>=3.0.0",
]
```

---

### 4.3 Graphe de Dépendances Neo4j

**Objectif** : Construire un vrai graphe de dépendances

```cypher
// Schéma Neo4j pour dépendances
CREATE CONSTRAINT unique_file IF NOT EXISTS
FOR (f:File) REQUIRE f.path IS UNIQUE;

CREATE CONSTRAINT unique_function IF NOT EXISTS
FOR (fn:Function) REQUIRE fn.qualified_name IS UNIQUE;

// Relations
(:File)-[:CONTAINS]->(:Function)
(:Function)-[:CALLS]->(:Function)
(:File)-[:IMPORTS]->(:File)
(:Class)-[:INHERITS]->(:Class)
```

```python
# src/hyperion/modules/integrations/neo4j_dependency_graph.py (NOUVEAU)
class DependencyGraphBuilder:
    """Construit le graphe de dépendances dans Neo4j."""

    def build_file_dependencies(self, repo_path: str):
        """Analyse et ingère les dépendances de fichiers."""
        for file_path in self._find_python_files(repo_path):
            ast_data = self.parser.parse_file(file_path)

            # Créer le nœud File
            self._create_file_node(file_path)

            # Créer les relations IMPORTS
            for imp in ast_data["imports"]:
                self._create_import_relation(file_path, imp)

            # Créer les nœuds Function et relations
            for func in ast_data["functions"]:
                self._create_function_node(file_path, func)
                for call in func["calls"]:
                    self._create_call_relation(func, call)
```

---

### 4.4 Détection d'Hallucinations Améliorée

**Objectif** : Améliorer la détection actuelle

```python
# src/hyperion/modules/rag/quality/hallucination_detector.py (AMÉLIORER)
class EnhancedHallucinationDetector:
    """Détecteur d'hallucinations amélioré."""

    def __init__(self):
        self.patterns = self._load_hallucination_patterns()
        self.semantic_checker = SemanticCoherenceChecker()
        self.fact_verifier = FactVerifier()

    def detect(self, response: str, sources: List[str], question: str) -> Dict:
        """Détection multi-niveaux."""
        return {
            "pattern_matches": self._check_patterns(response),
            "semantic_coherence": self.semantic_checker.check(response, sources),
            "fact_verification": self.fact_verifier.verify(response, sources),
            "confidence_score": self._calculate_confidence(response, sources),
            "suspicious_claims": self._extract_suspicious_claims(response, sources)
        }

    def _extract_suspicious_claims(self, response: str, sources: List[str]) -> List[Dict]:
        """Extrait les affirmations non vérifiables."""
        claims = self._extract_claims(response)
        suspicious = []
        for claim in claims:
            if not self._verify_in_sources(claim, sources):
                suspicious.append({
                    "claim": claim,
                    "reason": "Not found in sources",
                    "severity": self._assess_severity(claim)
                })
        return suspicious
```

---

## 5. FICHIERS CLÉS ET LEUR RÔLE

### 5.1 Configuration

| Fichier | Rôle | À modifier |
|---------|------|------------|
| `pyproject.toml` | Config projet, dépendances, version | ✅ Version |
| `src/hyperion/config.py` | Config runtime | ✅ Migrer vers pydantic |
| `.env.example` | Template variables env | ✅ Ajouter secrets v3.0 |
| `docker-compose.yml` | Orchestration Docker | ✅ Commentaire version |

### 5.2 Code Source Principal

| Fichier | Rôle | À modifier |
|---------|------|------------|
| `src/hyperion/__version__.py` | Version du package | ✅ Aligner |
| `src/hyperion/api/main.py` | Endpoints API | 🟡 Ajouter middleware |
| `src/hyperion/cli/main.py` | Commandes CLI | 🟡 Ajouter commandes |
| `src/hyperion/core/git_analyzer.py` | Analyse Git | 🟢 Stable |

### 5.3 Modules v3.0

| Module | Rôle | Statut |
|--------|------|--------|
| `modules/gateway/v3_0/` | API Gateway, routing, auth | ✅ Production |
| `modules/security/v3_0/` | JWT, TOTP, RBAC | ✅ Production |
| `modules/cache/v3_0/` | Cache distribué L1/L2 | ✅ Production |
| `modules/rag/quality/` | Validation qualité | 🟡 À améliorer |
| `modules/monitoring/` | Prometheus, logs | 🟡 Enrichir |

### 5.4 Tests

| Dossier | Contenu | Couverture |
|---------|---------|------------|
| `tests/unit/` | Tests unitaires | Bonne |
| `tests/integration/` | Tests d'intégration | Moyenne |
| `tests/e2e/bash/` | Tests end-to-end Bash | Bonne |
| `tests/deployment/` | Tests de déploiement | Bonne |

---

## 6. CONVENTIONS ET RÈGLES DE CODE

### 6.1 Style Python

```toml
# Configuration dans pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]
```

### 6.2 Structure des Modules

```python
# Template module Hyperion
"""
Module description.

Ce module implémente [fonctionnalité].
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from hyperion.core import GitAnalyzer

logger = logging.getLogger(__name__)


class ModuleName:
    """Description de la classe."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialise le module."""
        self.config = config or {}
        self._validate_config()

    def _validate_config(self) -> None:
        """Valide la configuration."""
        pass

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données."""
        logger.info("Processing data", extra={"module": self.__class__.__name__})
        return self._do_process(data)

    def _do_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Implémentation du traitement."""
        raise NotImplementedError
```

### 6.3 Documentation

```python
def function_name(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Description courte de la fonction.

    Description plus détaillée si nécessaire.

    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2. Par défaut 10.

    Returns:
        Description du retour avec structure

    Raises:
        ValueError: Si param1 est vide

    Example:
        >>> result = function_name("test", 20)
        >>> print(result)
        {'status': 'ok'}
    """
    pass
```

### 6.4 Commits

```bash
# Format des commits
<type>(<scope>): <description>

# Types
feat:     Nouvelle fonctionnalité
fix:      Correction de bug
docs:     Documentation
style:    Formatage
refactor: Refactoring
test:     Tests
chore:    Maintenance

# Exemples
feat(rag): add hallucination detection v2
fix(api): correct OpenAI compat streaming
docs(readme): update quickstart guide
refactor(config): migrate to pydantic-settings
```

---

## 7. STACK TECHNIQUE

### 7.1 Dépendances Principales

```toml
[project.dependencies]
# Core
pyyaml = ">=6.0"
jinja2 = ">=3.1.0"
click = ">=8.1.0"
python-dotenv = ">=1.0.0"

# API
fastapi = ">=0.104.0"
uvicorn = ">=0.24.0"
pydantic = ">=2.0.0"

# RAG
qdrant-client = ">=1.7.0"
sentence-transformers = ">=2.2.0"
langchain = ">=0.1.0"
langchain-community = ">=0.0.20"
torch = ">=2.0.0"

# Graph
neo4j = ">=5.28.0"
```

### 7.2 Dépendances à Ajouter

```toml
# Pour P1 - Configuration typée
pydantic-settings = ">=2.0.0"

# Pour P1 - Logging structuré
structlog = ">=24.0.0"

# Pour P2 - Code quality
radon = ">=5.1.0"
pylint = ">=3.0.0"

# Pour P2 - Évaluation
rouge-score = ">=0.1.0"  # Pour métriques de similarité
```

### 7.3 Services Externes

| Service | Version | Port | Usage |
|---------|---------|------|-------|
| Qdrant | latest | 6333/6334 | Vector DB |
| Ollama | latest | 11434 | LLM inference |
| Neo4j | 5 | 7474/7687 | Graph DB |
| Prometheus | latest | 9090 | Monitoring |
| MLflow | 2.8+ | 5000 | ML Platform |

---

## 8. COMMANDES ESSENTIELLES

### 8.1 Développement

```bash
# Installation développement
pip install -e ".[dev,ml,security]"

# Lancer les tests
pytest tests/ -v
pytest tests/unit/ -v --cov=hyperion

# Formatage
black src/ tests/
ruff check src/ tests/ --fix

# Type checking
mypy src/hyperion/
```

### 8.2 Docker

```bash
# Démarrage minimal
docker compose up -d qdrant ollama

# Démarrage complet
docker compose --profile full up -d

# Logs
docker compose logs -f hyperion-api

# Rebuild
docker compose build --no-cache hyperion-api
```

### 8.3 CLI Hyperion

```bash
# Info système
hyperion info
hyperion --version

# Analyse repository
hyperion profile /path/to/repo
hyperion profile /path/to/repo --output data/repos/myrepo/

# Génération docs
hyperion generate data/repos/myrepo/profile.yaml

# Ingestion Neo4j
hyperion ingest data/repos/myrepo/profile.yaml

# RAG
hyperion query "Combien de commits?" --repo myrepo
```

### 8.4 API

```bash
# Health check
curl http://localhost:8000/api/health

# Liste repos
curl http://localhost:8000/api/repos

# Chat RAG
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Décris l'architecture", "repo": "hyperion"}'

# OpenAI compatible
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hyperion-rag",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## 📋 CHECKLIST DE CORRECTIONS

### Phase 1 — P0 (Immédiat)

- [ ] Aligner versions (`pyproject.toml` → `3.0.0`)
- [ ] Mettre à jour `__version__.py` pour utiliser `importlib.metadata`
- [ ] Corriger commentaire `docker-compose.yml`
- [ ] Ajouter scan secrets dans CI (gitleaks)
- [ ] Documenter point d'entrée unique dans README

### Phase 2 — P1 (Court terme)

- [ ] Créer `src/hyperion/settings.py` avec pydantic-settings
- [ ] Migrer `config.py` vers le nouveau settings
- [ ] Ajouter middleware `X-Request-ID` dans API
- [ ] Configurer structlog pour logs JSON
- [ ] Ajouter `STATUS.md` dans chaque module v3.0

### Phase 3 — P2 (Moyen terme)

- [ ] Créer dossier `eval/` avec suites de tests
- [ ] Implémenter commande `hyperion eval`
- [ ] Créer `labs/` avec 5 exemples reproductibles
- [ ] Documenter API OpenAI-compat dans spec YAML
- [ ] Améliorer détection d'hallucinations

### Phase 4 — Améliorations (Long terme)

- [ ] Parser AST Python pour code intelligence
- [ ] Intégration radon/pylint pour métriques
- [ ] Graphe de dépendances Neo4j complet
- [ ] Dashboard métriques qualité temps réel

---

## 📚 RESSOURCES

- **Repository** : https://github.com/Ryckmat/Hyperion
- **Documentation** : `docs/` (Formation 10 chapitres)
- **API Reference** : `docs/technique/reference/api-reference.md`
- **Architecture v3.0** : `docs/technique/architecture/v3-enterprise-architecture.md`

---

> **Note pour Claude Code** : Ce document est la source de vérité pour comprendre le projet Hyperion. Utiliser ce contexte pour toute modification ou amélioration du code. En cas de doute, se référer aux fichiers source directement et demander des clarifications.
