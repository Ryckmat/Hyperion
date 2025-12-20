# Hyperion Core - Git Analyzer

## 📦 Module `git_analyzer.py`

Analyseur Git complet qui génère des profils Hyperion à partir de dépôts Git.

---

## 🎯 Usage

### Analyse simple

```python
from hyperion.core.git_analyzer import GitAnalyzer

# Analyser un repo
analyzer = GitAnalyzer("/home/kortazo/Documents/requests")
profile = analyzer.analyze()

print(f"Repo: {profile['service']}")
print(f"Commits: {profile['git_summary']['commits']}")
print(f"Contributeurs: {profile['git_summary']['contributors']}")
```

### Sauvegarder le profil

```python
import yaml

# Sauvegarder en YAML
with open("data/repositories/requests/profile.yaml", "w") as f:
    yaml.safe_dump(profile, f, allow_unicode=True, sort_keys=False)
```

---

## 📊 Structure du profil généré

```yaml
service: requests
owner:
  team: À remplir
  contacts:
    - https://github.com/psf/requests.git

repositories:
  - name: requests
    url: https://github.com/psf/requests.git
    main_language: python
    default_branch: main
    stars: null
    license: Apache-2.0

tech:
  runtime: python3
  framework: none
  ci: github-actions

git_summary:
  commits: 6377
  first_commit: '2011-02-13'
  last_commit: '2024-12-18'
  contributors: 805
  recent_commits_90d: 14
  
  hotspots_top10:
    - path: requests/models.py
      changes: 11079
    - path: tests/test_requests.py
      changes: 7652
    # ...
  
  contributors_top10:
    - name: Kenneth Reitz
      email: me@kennethreitz.com
      commits: 3148
    # ...
  
  by_extension:
    - ext: .py
      files: 99
      changes: 63769
    # ...
  
  directories_top:
    - dir: requests
      changes: 38075
    # ...

metrics:
  evolution_years: 14
  avg_commits_per_year: 455.5
  avg_changes_per_hotspot: 4689.2
  changes_ratio:
    code_py: 44.2
    tests: 18.2
    docs: 18.9
  py_changes_per_file_avg: 387.4

notes:
  - Hotspots calculés après filtrage des vendored/artefacts
  - Contributeurs dédupliqués (noreply, variantes Gmail)
  - Licence et CI détectées localement
```

---

## 🔧 Fonctionnalités

### 1. Déduplication contributeurs

Fusionne automatiquement :
- **Gmail** : `john.smith@gmail.com` → `johnsmith@gmail.com`
- **GitHub noreply** : `user+tag@users.noreply.github.com` → `user@users.noreply.github.com`
- **Variantes de noms** : Normalise casse et espaces

### 2. Filtrage hotspots intelligent

Ignore automatiquement :
- **Binaires** : `.png`, `.jpg`, `.exe`, `.pdf`, etc.
- **Vendored** : `node_modules/`, `vendor/`, `requests/packages/`
- **Docs bruitées** : `CHANGELOG`, `README`, `HISTORY`

Configuration dans `config/filters.yaml`.

### 3. Métriques qualité

- **Ratio code/tests/docs** : Analyse la répartition des changements
- **Densité fichiers** : Moyenne changements par fichier Python
- **Évolution** : Années d'activité, commits par an
- **Hotspots** : Moyenne changements dans les 10 fichiers les plus touchés

### 4. Détections automatiques

- **Langage** : Heuristique sur extensions de fichiers
- **CI/CD** : GitHub Actions, GitLab CI, Jenkins, Travis, etc.
- **Licence** : Apache, MIT, BSD, GPL (détection par pattern)

---

## 🧪 Tests

### Script de test standalone

```bash
cd /home/kortazo/Documents/Hyperion
python3 scripts/test_analyzer_requests.py
```

Analyse complète du repo `requests` (~30-60 secondes) et sauvegarde :
- `data/repositories/requests/profile.yaml`
- `data/repositories/requests/profile.json`

### Tests unitaires (à venir)

```bash
pytest tests/test_git_analyzer.py -v
```

---

## 📈 Performance

Sur le repo `requests` (6377 commits, 805 contributeurs) :
- **Analyse complète** : ~30-60 secondes
- **Mémoire** : ~200 MB
- **Sortie** : ~50 KB (YAML)

---

## 🔗 Dépendances

- `hyperion.utils.git_utils.GitRepo` : Wrapper Git
- `hyperion.config.FILTERS` : Configuration filtres
- `yaml` : Sauvegarde profil
- Standard library : `collections`, `pathlib`, `re`

---

## 🎯 Intégration CLI

Ce module sera appelé par la commande :

```bash
hyperion profile /path/to/repo --output data/repositories/
```

Implémentation dans `hyperion/cli/main.py` :

```python
from hyperion.core.git_analyzer import GitAnalyzer

analyzer = GitAnalyzer(repo_path)
profile = analyzer.analyze()

# Sauvegarder
output_path = Path(output) / repo_name / "profile.yaml"
with open(output_path, "w") as f:
    yaml.safe_dump(profile, f, allow_unicode=True, sort_keys=False)
```

---

## 💡 Exemples avancés

### Analyse avec filtres personnalisés

```python
from hyperion.core.git_analyzer import GitAnalyzer

analyzer = GitAnalyzer("/path/to/repo")

# Modifier les filtres temporairement
analyzer.filters["ignore_extensions"].append(".custom")
analyzer.filters["ignore_prefixes"].append("generated/")

profile = analyzer.analyze()
```

### Analyse multi-repos

```python
repos = [
    "/home/kortazo/Documents/requests",
    "/home/kortazo/Documents/flask",
    "/home/kortazo/Documents/django"
]

for repo_path in repos:
    analyzer = GitAnalyzer(repo_path)
    profile = analyzer.analyze()
    
    repo_name = profile["service"]
    output = f"data/repositories/{repo_name}/profile.yaml"
    
    with open(output, "w") as f:
        yaml.safe_dump(profile, f, allow_unicode=True, sort_keys=False)
    
    print(f"✅ {repo_name}: {profile['git_summary']['commits']} commits")
```

---

## 🚀 Prochaines étapes

1. **Connecter au CLI** : Implémenter `hyperion profile`
2. **Tests unitaires** : Coverage > 80%
3. **Optimisations** : Cache numstat, analyse incrémentale
4. **Métriques avancées** : Complexité cyclomatique, code churn
