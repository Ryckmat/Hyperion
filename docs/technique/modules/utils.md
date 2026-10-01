---
title: "Hyperion Utils - Git Utils"
toc: true
description: "Wrapper Python pour interactions avec Git via subprocess."
weight: 6
---

## 📦 Module `git_utils.py`

Wrapper Python pour interactions avec Git via subprocess.

---

## 🎯 Usage

### Initialisation

```python
from hyperion.utils.git_utils import GitRepo

# Créer un wrapper sur un repo existant
repo = GitRepo("/path/to/repo")
```

### Métadonnées du repo

```python
# Nom du repo
name = repo.get_name()  # "Hyperion"

# URL remote
url = repo.get_remote_url()  # "https://github.com/Ryckmat/Hyperion.git"

# Branche principale
branch = repo.detect_main_branch()  # "main"
```

### Commits

```python
# Tous les commits
commits = repo.get_commits()
# [{"sha": "abc123", "author_name": "Ryckman", "subject": "feat: ...", ...}, ...]

# Commits récents (90 jours)
recent = repo.get_commits(since="90.days")

# Commits depuis une date
from_date = repo.get_commits(since="2024-01-01")
```

### Contributeurs

```python
contributors = repo.get_contributors()
# [{"name": "Ryckman", "email": "...", "commits": 42}, ...]
```

### Statistiques

```python
# Numstat (additions/deletions par fichier)
numstat = repo.get_numstat()
# [(10, 5, "hyperion/core.py"), (3, 1, "README.md"), ...]

# Compter commits récents
count = repo.count_recent_commits(days=90)  # 15
```

### Détections automatiques

```python
# Langage principal (heuristique extensions)
language = repo.detect_language()  # "python"

# CI/CD
ci = repo.detect_ci()  # "github-actions"

# Licence
license_name = repo.detect_license()  # "Apache-2.0"

# Plage de dates
first, last = repo.get_date_range()
# ("2024-01-15T10:30:00+00:00", "2024-12-18T22:45:00+00:00")
```

---

## 🧪 Tests

```bash
# Lancer les tests
pytest tests/test_git_utils.py -v

# Avec coverage
pytest tests/test_git_utils.py --cov=hyperion.utils.git_utils --cov-report=term-missing
```

---

## 🔧 Gestion erreurs

```python
from hyperion.utils.git_utils import GitRepo, GitCommandError

try:
    repo = GitRepo("/invalid/path")
except GitCommandError as e:
    print(f"Erreur: {e}")
```

---

## 📊 Exemple complet

```python
from hyperion.utils.git_utils import GitRepo

# Analyser le repo Hyperion lui-même
repo = GitRepo("/home/kortazo/Documents/Hyperion")

# Métadonnées
print(f"Repo: {repo.get_name()}")
print(f"Branche: {repo.detect_main_branch()}")
print(f"Langage: {repo.detect_language()}")
print(f"CI: {repo.detect_ci()}")
print(f"Licence: {repo.detect_license()}")

# Stats
commits = repo.get_commits()
contributors = repo.get_contributors()
recent = repo.count_recent_commits(90)

print(f"\nStats:")
print(f"  Commits totaux: {len(commits)}")
print(f"  Contributeurs: {len(contributors)}")
print(f"  Commits (90j): {recent}")

# Top contributeurs
top_5 = sorted(contributors, key=lambda x: x["commits"], reverse=True)[:5]
print(f"\nTop 5 contributeurs:")
for c in top_5:
    print(f"  {c['name']}: {c['commits']} commits")
```

---

## 🎯 Prochaines étapes

Ce module est la **base** pour implémenter :
- `hyperion.core.git_analyzer` (utilise `GitRepo`)
- `hyperion.core.prod_exporter` (utilise `GitRepo`)
- CLI `hyperion profile` (via `GitAnalyzer` → `GitRepo`)

---

## 📝 Notes techniques

### Performance
- Chaque méthode exécute une commande Git via subprocess
- Pas de cache (appels répétés = commandes répétées)
- Pour analyse complète, préférer appeler une seule fois et stocker résultats

### Encodage
- UTF-8 par défaut, erreurs ignorées (`errors="ignore"`)
- Compatible repos avec noms de fichiers non-ASCII

### Compatibilité
- Python 3.10+
- Git 2.x
- Testé sur Linux/Unix (compatible Windows via WSL)
