# 🚀 Hyperion - Git Repository Profiler & Knowledge Graph

Hyperion analyse vos dépôts Git et génère automatiquement :
- 📊 Documentation technique structurée
- 🔥 Identification des hotspots de code
- 👥 Déduplication intelligente des contributeurs
- 📈 Métriques de qualité (code/tests/docs)
- 🗄️ Ingestion dans Neo4j pour graphe de connaissances

## 🎯 Installation rapide

```bash
cd Hyperion
pip install -e .
```

## 🎮 Usage

### Profiler un dépôt
```bash
hyperion profile /path/to/repo --output data/repositories/
```

### Générer documentation
```bash
hyperion generate data/repositories/mon-repo/profile.yaml --format markdown
```

### Export historique production
```bash
hyperion export /path/to/repo --tags-pattern "^v\d+\.\d+\.\d+$"
```

### Ingestion Neo4j
```bash
hyperion ingest data/repositories/mon-repo/ --uri bolt://localhost:7687
```

## 📁 Structure du projet

```
Hyperion/
├── hyperion/           # Package Python principal
│   ├── cli/           # Interface ligne de commande
│   ├── core/          # Logique métier (analyseurs)
│   ├── integrations/  # Neo4j, GitLab, GitHub
│   ├── generators/    # Générateurs de documentation
│   ├── models/        # Modèles de données
│   └── utils/         # Utilitaires
├── config/            # Configuration (filtres, patterns)
├── templates/         # Templates Jinja2
├── data/              # Données générées (gitignore)
├── output/            # Documentation générée (gitignore)
├── tests/             # Tests unitaires
└── docs/              # Documentation projet
```

## 📚 Documentation complète

- [Getting Started](docs/getting_started.md)
- [Architecture](docs/architecture.md)
- [CLI Reference](docs/cli_reference.md)
- [YAML Schema](docs/yaml_schema.md)
- [Neo4j Model](docs/neo4j_model.md)

## 🛠️ Développement

```bash
# Installation en mode dev
pip install -e ".[dev]"

# Tests
pytest tests/

# Linting
ruff check hyperion/
black hyperion/

# Type checking
mypy hyperion/
```

## 📋 Roadmap

- [x] Profiling Git avancé
- [x] Génération documentation Markdown
- [x] Export historique production
- [x] Ingestion Neo4j
- [ ] API REST FastAPI
- [ ] Dashboard Streamlit
- [ ] Support multi-repos
- [ ] Intégration GitLab CI

## 🤝 Contribution

Contributions bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Licence

Apache-2.0 - Voir [LICENSE](LICENSE)

## 👤 Auteur

**Matthieu Ryckman**
- GitHub: [@Ryckmat](https://github.com/Ryckmat)
