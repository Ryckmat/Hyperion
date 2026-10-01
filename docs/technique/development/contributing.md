---
title: "Guide de contribution"
toc: true
description: "Merci de votre intérêt pour contribuer à Hyperion !"
weight: 3
---

Merci de votre intérêt pour contribuer à Hyperion ! 🎉

## 🚀 Démarrage rapide

### 1. Fork & Clone

```bash
git clone https://github.com/Ryckmat/Hyperion.git
cd Hyperion
```

### 2. Installation dev

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer en mode dev
pip install -e ".[dev]"
```

### 3. Configuration

```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

---

## 📋 Workflow de contribution

### 1. Créer une branche

```bash
git checkout -b feature/ma-super-feature
# ou
git checkout -b fix/correction-bug
```

### 2. Développer

```bash
# Faire vos modifications
# Ajouter des tests si nécessaire
```

### 3. Tests & Qualité

```bash
# Tests unitaires
pytest tests/

# Coverage
pytest --cov=hyperion tests/

# Linting
ruff check hyperion/
black hyperion/ --check

# Type checking
mypy hyperion/
```

### 4. Commit

Convention : [Conventional Commits](https://www.conventionalcommits.org/fr/)

```bash
git add .
git commit -m "feat: ajout génération HTML"
# ou
git commit -m "fix: correction normalisation chemins Git"
# ou
git commit -m "docs: mise à jour README"
```

Types de commits :
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `style:` Formatage (pas de changement code)
- `refactor:` Refactoring
- `test:` Ajout tests
- `chore:` Tâches maintenance

### 5. Push & Pull Request

```bash
git push origin feature/ma-super-feature
```

Puis créer une Pull Request sur GitHub avec :
- Description claire de la fonctionnalité/correction
- Tests ajoutés/modifiés
- Screenshots si UI
- Référence issue (`Fixes #42`)

---

## 🎯 Domaines de contribution

### 🐛 Bugs
- Rechercher dans les [Issues](https://github.com/Ryckmat/Hyperion/issues)
- Reproduire le bug
- Proposer un fix avec tests

### ✨ Nouvelles fonctionnalités
- Discuter d'abord dans une issue
- Implémenter avec tests
- Mettre à jour la documentation

### 📝 Documentation
- README, CHANGELOG, docs/
- Docstrings Python
- Exemples d'usage

### 🧪 Tests
- Améliorer coverage
- Ajouter tests edge cases
- Tests d'intégration

### 🎨 Templates
- Améliorer templates Jinja2
- Nouveaux formats (HTML, etc.)

---

## 📐 Standards de code

### Python Style
- **PEP 8** : respecté via `black` et `ruff`
- **Type hints** : obligatoires (Python 3.10+)
- **Docstrings** : format Google

Exemple :
```python
def analyze_repository(repo_path: str, filters: dict) -> dict:
    """
    Analyse un dépôt Git et retourne le profil complet.
    
    Args:
        repo_path: Chemin vers le dépôt Git
        filters: Dictionnaire des filtres (extensions, préfixes)
    
    Returns:
        Profil Hyperion au format dict
    
    Raises:
        ValueError: Si le chemin n'est pas un dépôt Git valide
    """
    pass
```

### Structure modules
```python
# Imports standard library
import os
from pathlib import Path

# Imports third-party
import click
import yaml

# Imports locaux
from hyperion.config import FILTERS
from hyperion.utils.git_utils import GitRepo
```

### Tests
- Fichier `test_{module}.py` pour chaque module
- Classes `Test{Feature}`
- Méthodes `test_{behaviour}_should_{expected}`

```python
class TestGitAnalyzer:
    def test_analyze_should_return_valid_profile(self):
        analyzer = GitAnalyzer("/path/to/repo")
        profile = analyzer.analyze()
        assert "service" in profile
        assert "git_summary" in profile
```

---

## 🏗️ Architecture

```
hyperion/
├── cli/              # Interface ligne de commande (Click)
├── core/             # Logique métier
│   ├── git_analyzer.py          # Analyseur Git principal
│   ├── prod_exporter.py         # Export releases
│   ├── contributor_deduplicator.py
│   ├── hotspot_calculator.py
│   └── metrics_calculator.py
├── generators/       # Générateurs documentation
│   ├── markdown_generator.py
│   └── html_generator.py
├── integrations/     # Intégrations externes
│   ├── neo4j_ingester.py
│   ├── gitlab_client.py
│   └── github_client.py
├── models/           # Modèles de données
│   ├── repository.py
│   ├── commit.py
│   └── contributor.py
└── utils/            # Utilitaires
    ├── git_utils.py
    ├── path_normalizer.py
    └── logger.py
```

---

## ❓ Questions

- 💬 Discussions : [GitHub Discussions](https://github.com/Ryckmat/Hyperion/discussions)
- 🐛 Bugs : [GitHub Issues](https://github.com/Ryckmat/Hyperion/issues)
- 📧 Email : contact@ryckmat.dev

---

## 📜 Licence

En contribuant, vous acceptez que vos contributions soient sous licence **Apache-2.0**.

---

Merci de contribuer à Hyperion ! 🚀
