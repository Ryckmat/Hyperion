# Architecture Hyperion

Documentation de l'architecture du projet Hyperion.

## 🎯 Vue d'ensemble

Hyperion est une plateforme d'analyse de dépôts Git avec 4 composants principaux :

1. **Profiler** : Analyse Git complète → `profile.yaml`
2. **Generator** : Documentation Markdown depuis YAML
3. **Exporter** : Historique production (releases)
4. **Ingester** : Graphe Neo4j pour requêtes avancées

## 📦 Structure des packages

```
hyperion/
├── __init__.py              # Point d'entrée package
├── __version__.py           # Version unique
├── config.py                # Configuration centralisée
│
├── cli/                     # Interface ligne de commande
│   ├── main.py             # Entry point CLI (Click)
│   ├── profile.py          # Commande: hyperion profile
│   ├── generate.py         # Commande: hyperion generate
│   ├── export.py           # Commande: hyperion export
│   └── ingest.py           # Commande: hyperion ingest
│
├── core/                    # Logique métier
│   ├── git_analyzer.py     # Analyse Git (commits, contributors, hotspots)
│   ├── prod_exporter.py    # Export releases production
│   ├── contributor_deduplicator.py  # Fusion aliases contributeurs
│   ├── hotspot_calculator.py        # Calcul hotspots avec filtres
│   └── metrics_calculator.py        # KPIs (ratios, densité, etc.)
│
├── integrations/            # Intégrations externes
│   ├── neo4j_ingester.py   # Ingestion graphe Neo4j
│   ├── gitlab_client.py    # Client GitLab API (futur)
│   └── github_client.py    # Client GitHub API (futur)
│
├── generators/              # Générateurs documentation
│   ├── markdown_generator.py  # Génération Markdown (Jinja2)
│   ├── yaml_generator.py      # Génération YAML
│   └── html_generator.py      # Génération HTML (futur)
│
├── models/                  # Modèles de données
│   ├── repository.py        # Modèle Repository
│   ├── commit.py            # Modèle Commit
│   ├── contributor.py       # Modèle Contributor
│   └── hotspot.py           # Modèle Hotspot
│
└── utils/                   # Utilitaires
    ├── git_utils.py         # Wrappers Git (sh, parsing)
    ├── file_utils.py        # Manipulation fichiers
    ├── path_normalizer.py   # Normalisation chemins Git
    └── logger.py            # Logging structuré
```

## 🔄 Flux de données

### 1. Profile → YAML

```
Dépôt Git
    ↓
[GitAnalyzer]
    ↓
Commits + Contributors + Numstat
    ↓
[ContributorDeduplicator] + [HotspotCalculator]
    ↓
[MetricsCalculator]
    ↓
profile.yaml
```

### 2. YAML → Documentation

```
profile.yaml
    ↓
[MarkdownGenerator]
    ↓
Templates Jinja2 (index.md.j2, registre.md.j2)
    ↓
Documentation Markdown (index.md, registre.md)
```

### 3. Export Production

```
Dépôt Git + Tags SemVer
    ↓
[ProdExporter]
    ↓
Releases + Commits par release + Fichiers modifiés
    ↓
prod_deploys.json + prod_commits.jsonl + prod_files.jsonl
```

### 4. Ingestion Neo4j

```
Exports JSONL
    ↓
[Neo4jIngester]
    ↓
Nœuds: Repo, Branch, Tag, Commit, Author, File, Dir
Relations: CONTAINS, COMMITTED_BY, TOUCHED, IN_RELEASE, IN_DIR
    ↓
Graphe Neo4j
```

## 🧠 Core : Logique métier

### GitAnalyzer

**Rôle** : Analyser un dépôt Git local et extraire toutes les métriques.

**Entrée** : Chemin vers repo Git  
**Sortie** : `dict` (futur `profile.yaml`)

**Workflow** :
1. Détection métadonnées (nom, remote, branche principale)
2. Extraction historique Git (`git log --date=iso --pretty=format:...`)
3. Déduplication contributeurs (emails Gmail, noreply GitHub)
4. Calcul hotspots (`git log --numstat` + filtres)
5. Stats par extension / répertoire
6. Détection CI/CD et licence
7. Calcul KPIs (ratios, densité, commits/an)

**Dépendances** :
- `GitRepo` (utils)
- `ContributorDeduplicator` (core)
- `HotspotCalculator` (core)
- `MetricsCalculator` (core)

### ContributorDeduplicator

**Rôle** : Fusionner les alias d'un même contributeur.

**Logique** :
1. Normalisation emails :
   - Gmail : suppression `.` dans local part (`john.smith@gmail.com` → `johnsmith@gmail.com`)
   - GitHub noreply : suppression `+tag` (`user+tag@users.noreply.github.com` → `user@users.noreply.github.com`)
2. Fusion par nom canonique (title case, suppression `[bot]`)
3. Agrégation commits

**Exemple** :
```python
Input:
  - "John Smith <john.smith@gmail.com>" (50 commits)
  - "John Smith <johnsmith@gmail.com>" (30 commits)
  
Output:
  - "John Smith <johnsmith@gmail.com>" (80 commits)
```

### HotspotCalculator

**Rôle** : Identifier les fichiers les plus modifiés (hotspots).

**Logique** :
1. Parsing `git log --numstat` (additions + suppressions par fichier)
2. Filtrage :
   - Extensions binaires (`.png`, `.pdf`, `.exe`, etc.)
   - Vendored (`node_modules/`, `vendor/`, etc.)
   - Docs bruités (`README`, `CHANGELOG`, `HISTORY`)
3. Normalisation chemins (renames Git : `{old => new}`)
4. Tri par nombre de changements
5. Top 10

**Filtres** : Configuration dans `config/filters.yaml`

### MetricsCalculator

**Rôle** : Calculer les KPIs projet.

**Métriques** :
- **Évolution (années)** : `last_commit.year - first_commit.year`
- **Commits/an** : `total_commits / années`
- **Moyenne changements/hotspot** : `sum(hotspots.changes) / len(hotspots)`
- **Ratio code/tests/docs** :
  - Code : fichiers dans `src/`, `lib/`, `{service}/`
  - Tests : fichiers dans `tests/`, `test/`
  - Docs : fichiers `.md`, `.rst`, `docs/`
- **Densité .py** : `changements_py / nb_fichiers_py`

## 🔌 Integrations : Neo4j

### Modèle de graphe

```cypher
// Nœuds
(:Repo {name})
(:Branch {name, is_main})
(:Tag {name, released_at, tag_sha})
(:Commit {sha, subject, date, isMerge})
(:Author {name, email})
(:File {path, ext})
(:Dir {path})

// Relations
(:Repo)-[:HAS_BRANCH]->(:Branch)
(:Repo)-[:HAS_TAG]->(:Tag)
(:Branch)-[:CONTAINS]->(:Commit)
(:Commit)-[:COMMITTED_BY]->(:Author)
(:Commit)-[:IN_RELEASE]->(:Tag)
(:Commit)-[:TOUCHED {add, del, type}]->(:File)
(:File)-[:IN_DIR]->(:Dir)
```

### Contraintes & Index

```cypher
// Contraintes unicité
CREATE CONSTRAINT repo IF NOT EXISTS FOR (r:Repo) REQUIRE r.name IS UNIQUE
CREATE CONSTRAINT commit IF NOT EXISTS FOR (c:Commit) REQUIRE c.sha IS UNIQUE
CREATE CONSTRAINT tag IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE
CREATE CONSTRAINT author IF NOT EXISTS FOR (a:Author) REQUIRE a.email IS UNIQUE

// Index performance
CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path)
CREATE INDEX dir_path IF NOT EXISTS FOR (d:Dir) ON (d.path)
CREATE INDEX branch_name IF NOT EXISTS FOR (b:Branch) ON (b.name)
```

### Ingestion par batch

```python
# Commits : batch de 500
for batch in chunks(commits, 500):
    session.execute_write(upsert_commits_batch, batch)

# Fichiers : batch de 2000
for batch in chunks(files, 2000):
    session.execute_write(upsert_files_batch, batch)
```

## 📝 Generators : Documentation

### MarkdownGenerator

**Rôle** : Générer Markdown depuis `profile.yaml`.

**Templates Jinja2** :
- `templates/markdown/index.md.j2` → Vue d'ensemble
- `templates/markdown/registre.md.j2` → Registre technique

**Variables disponibles** :
```jinja2
{{ service }}
{{ owner.team }}
{{ git_summary.commits }}
{{ metrics.avg_commits_per_year }}
...
```

**Filtres Jinja2** :
- `capitalize` : Première lettre majuscule
- Boucles : `{% for item in list %}`

## ⚙️ Configuration

### config.py

**Rôle** : Configuration centralisée du projet.

**Constantes** :
```python
PROJECT_ROOT: Path              # Racine projet
CONFIG_DIR: Path                # config/
TEMPLATES_DIR: Path             # templates/
DATA_DIR: Path                  # data/
OUTPUT_DIR: Path                # output/

DEFAULT_MAIN_CANDIDATES: list   # ["main", "master", "trunk", "develop"]
DEFAULT_TAGS_REGEX: str         # r"^v?\d+\.\d+\.\d+$"

NEO4J_URI: str                  # bolt://localhost:7687
NEO4J_USER: str                 # neo4j
NEO4J_PASSWORD: str             # (from env)
NEO4J_DATABASE: str             # hyperion

BATCH_SIZE_COMMITS: int         # 500
BATCH_SIZE_FILES: int           # 2000

FILTERS: dict                   # Chargé depuis config/filters.yaml
```

### config/filters.yaml

**Rôle** : Définir les filtres pour hotspots.

**Structure** :
```yaml
ignore_extensions:
  - .png
  - .pdf
  ...

ignore_prefixes:
  - node_modules/
  - vendor/
  ...

ignore_files:
  - README.md
  - CHANGELOG
  ...
```

## 🎮 CLI : Interface utilisateur

### Click framework

**Avantages** :
- Syntaxe déclarative
- Auto-génération `--help`
- Validation arguments
- Gestion erreurs

**Structure** :
```python
@click.group()
def cli():
    """Entry point."""
    pass

@cli.command()
@click.argument("repo_path")
@click.option("--output", "-o")
def profile(repo_path, output):
    """Profiler un repo."""
    pass
```

## 🧪 Tests

### Structure

```
tests/
├── conftest.py                 # Fixtures pytest
├── test_structure.py           # Tests structure projet
├── test_git_analyzer.py        # Tests GitAnalyzer
├── test_contributor_dedup.py   # Tests déduplication
├── test_hotspot_calculator.py  # Tests hotspots
└── fixtures/                   # Données de test
```

### Fixtures

```python
@pytest.fixture
def project_root():
    """Racine projet."""
    return Path(__file__).parent.parent

@pytest.fixture
def sample_profile_yaml():
    """Profile YAML de test."""
    return project_root / "data/repositories/requests/profile.yaml"
```

## 🚀 Évolutions futures

### v1.1.0 - CLI amélioré
- Mode interactif
- Support multi-repos
- Progress bars
- Export HTML

### v1.2.0 - Intégrations avancées
- Client GitLab API
- Client GitHub API
- Webhooks
- Dashboard web

### v2.0.0 - Hyperion Platform
- API REST FastAPI
- RAG documentation
- Graphe dépendances inter-repos
- ML prédictif

## 📚 Références

- [Click documentation](https://click.palletsprojects.com/)
- [Jinja2 templates](https://jinja.palletsprojects.com/)
- [Neo4j Cypher](https://neo4j.com/docs/cypher-manual/)
- [Conventional Commits](https://www.conventionalcommits.org/)
