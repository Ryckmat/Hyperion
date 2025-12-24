"""Analyseur Git principal - Génère un profil Hyperion complet."""

import re
from collections import Counter
from pathlib import Path

from hyperion.config import FILTERS
from hyperion.utils.git_utils import GitRepo


class GitAnalyzer:
    """
    Analyse complète d'un dépôt Git et génération du profil Hyperion.

    Combine les données brutes de GitRepo avec :
    - Déduplication des contributeurs
    - Calcul des hotspots filtrés
    - Métriques qualité (ratio code/tests/docs)
    - Stats par extension et répertoire

    Example:
        >>> analyzer = GitAnalyzer("/home/kortazo/Documents/requests")
        >>> profile = analyzer.analyze()
        >>> print(profile["service"])
        'requests'
    """

    def __init__(self, repo_path: str):
        """
        Initialise l'analyseur Git.

        Args:
            repo_path: Chemin vers le dépôt Git local
        """
        self.repo = GitRepo(repo_path)
        self.filters = FILTERS
        self.repo_name = self.repo.get_name().lower()

    def analyze(self) -> dict:
        """
        Analyse complète du dépôt et génération du profil Hyperion.

        Returns:
            Dictionnaire contenant le profil complet au format YAML Hyperion
        """
        # 1. Métadonnées repo
        repo_name = self.repo.get_name()
        remote_url = self.repo.get_remote_url()
        main_branch = self.repo.detect_main_branch()
        language = self.repo.detect_language()
        ci = self.repo.detect_ci()
        license_name = self.repo.detect_license()

        # 2. Historique commits
        commits = self.repo.get_commits()
        first_date, last_date = self.repo.get_date_range()
        recent_commits = self.repo.count_recent_commits(90)

        # 3. Contributeurs (dédupliqués)
        contributors_raw = self.repo.get_contributors()
        contributors = self._deduplicate_contributors(contributors_raw)
        contributors_top10 = contributors[:10]

        # 4. Numstat → Hotspots filtrés
        numstat = self.repo.get_numstat()
        hotspots = self._calculate_hotspots(numstat)
        hotspots_top10 = hotspots[:10]

        # 5. Stats par extension et répertoire
        by_extension = self._stats_by_extension(numstat)
        directories_top = self._stats_by_directory(numstat)

        # 6. Métriques qualité
        metrics = self._calculate_metrics(
            commits=commits,
            hotspots=hotspots,
            by_extension=by_extension,
            numstat=numstat,
            first_date=first_date,
            last_date=last_date,
        )

        # 7. Construction du profil YAML
        return {
            "service": repo_name,
            "owner": {
                "team": "À remplir",
                "contacts": [remote_url] if remote_url else [],
            },
            "repositories": [
                {
                    "name": repo_name,
                    "url": remote_url,
                    "main_language": language,
                    "default_branch": main_branch,
                    "stars": None,
                    "license": license_name,
                }
            ],
            "tech": {
                "runtime": self._guess_runtime(language),
                "framework": "none",
                "ci": ci,
            },
            "git_summary": {
                "commits": len(commits),
                "first_commit": first_date[:10] if first_date else None,
                "last_commit": last_date[:10] if last_date else None,
                "contributors": len(contributors),
                "recent_commits_90d": recent_commits,
                "hotspots_top10": [{"path": path, "changes": changes} for path, changes in hotspots_top10],
                "contributors_top10": contributors_top10,
                "by_extension": by_extension[:10],
                "directories_top": directories_top[:10],
            },
            "metrics": metrics,
            "notes": [
                "Hotspots calculés après filtrage des vendored/artefacts (prefixes & extensions).",
                "Contributeurs dédupliqués (noreply, variantes Gmail).",
                "Licence et CI détectées localement sans API distante.",
            ],
        }

    def _deduplicate_contributors(self, contributors: list[dict]) -> list[dict]:
        """
        Déduplique les contributeurs en normalisant emails et noms.

        Fusionne :
        - Variantes Gmail (john.smith@gmail.com → johnsmith@gmail.com)
        - Emails noreply GitHub (user+tag@users.noreply.github.com)
        - Variantes de noms (majuscules, espaces)

        Args:
            contributors: Liste brute des contributeurs

        Returns:
            Liste dédupliquée et triée par nombre de commits
        """
        # Agrégation par nom canonique
        aggregated = {}

        for c in contributors:
            name = self._normalize_name(c["name"])
            email = self._normalize_email(c["email"])

            # Clé unique : nom normalisé
            key = name.lower()

            if key in aggregated:
                # Fusionner
                aggregated[key]["commits"] += c["commits"]
                if email and email not in aggregated[key]["emails"]:
                    aggregated[key]["emails"].append(email)
            else:
                # Nouveau
                aggregated[key] = {
                    "name": name,
                    "emails": [email] if email else [],
                    "commits": c["commits"],
                }

        # Convertir en liste et trier
        result = [
            {
                "name": data["name"],
                "email": data["emails"][0] if data["emails"] else "",
                "commits": data["commits"],
            }
            for data in aggregated.values()
        ]

        return sorted(result, key=lambda x: x["commits"], reverse=True)

    def _normalize_name(self, name: str) -> str:
        """Normalise un nom de contributeur."""
        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r"\s*\[bot\]\s*$", "", name, flags=re.I)
        return name.title()

    def _normalize_email(self, email: str) -> str:
        """
        Normalise un email de contributeur.

        - Gmail : supprime les points dans la partie locale
        - GitHub noreply : supprime les tags (+xxx)
        """
        if not email:
            return ""

        email = email.strip().lower()

        # GitHub noreply : user+tag@users.noreply.github.com → user@users.noreply.github.com
        email = re.sub(r"\+.*(?=@users\.noreply\.github\.com)", "", email)

        # Gmail : john.smith@gmail.com → johnsmith@gmail.com
        if email.endswith("@gmail.com"):
            local, domain = email.split("@", 1)
            local = local.replace(".", "")
            email = f"{local}@{domain}"

        return email

    def _calculate_hotspots(self, numstat: list[tuple[int, int, str]]) -> list[tuple[str, int]]:
        """
        Calcule les hotspots (fichiers les plus modifiés) après filtrage.

        Filtre :
        - Extensions binaires (.png, .exe, .pdf, etc.)
        - Préfixes vendored (node_modules/, vendor/, etc.)
        - Fichiers bruits (CHANGELOG, README, etc.)

        Args:
            numstat: Liste (additions, deletions, path)

        Returns:
            Liste triée (path, total_changes) des hotspots
        """
        changes = Counter()

        for add, delete, path in numstat:
            # Normaliser le chemin
            path = self._normalize_path(path)

            # Filtrer
            if self._should_ignore(path):
                continue

            changes[path] += add + delete

        return changes.most_common()

    def _normalize_path(self, path: str) -> str:
        """
        Normalise un chemin Git (gère les renames).

        Exemples :
        - "a/{old => new}/b.py" → "a/new/b.py"
        - "old => new" → "new"
        """
        path = path.replace("\\", "/").strip()

        # Gérer les renames : {old => new}
        if " => " in path:
            path = re.sub(r"\{([^{}]*?)\s*=>\s*([^{}]*?)\}", r"\2", path)
            path = path.split(" => ")[-1]

        return path.lstrip("./")

    def _should_ignore(self, path: str) -> bool:
        """Vérifie si un fichier doit être ignoré selon les filtres."""
        path_lower = path.lower()

        # Extensions à ignorer
        for ext in self.filters.get("ignore_extensions", []):
            if path_lower.endswith(ext):
                return True

        # Préfixes à ignorer
        for prefix in self.filters.get("ignore_prefixes", []):
            if path_lower.startswith(prefix.lower()):
                return True

        # Fichiers à ignorer (nom exact)
        filename = path.split("/")[-1]
        return filename in self.filters.get("ignore_files", [])

    def _stats_by_extension(self, numstat: list[tuple[int, int, str]]) -> list[dict]:
        """
        Calcule les stats par extension de fichier.

        Returns:
            Liste de {"ext": ".py", "files": 99, "changes": 63769}
        """
        ext_files = {}  # {".py": {"fichiers_set", total_changes}}
        ext_changes = Counter()

        for add, delete, path in numstat:
            path = self._normalize_path(path)

            if self._should_ignore(path):
                continue

            # Extension
            ext = Path(path).suffix.lower() or "<noext>"

            # Initialiser si nécessaire
            if ext not in ext_files:
                ext_files[ext] = set()

            ext_files[ext].add(path)
            ext_changes[ext] += add + delete

        # Convertir en liste
        result = [{"ext": ext, "files": len(files), "changes": ext_changes[ext]} for ext, files in ext_files.items()]

        return sorted(result, key=lambda x: x["changes"], reverse=True)

    def _stats_by_directory(self, numstat: list[tuple[int, int, str]]) -> list[dict]:
        """
        Calcule les stats par répertoire de premier niveau.

        Returns:
            Liste de {"dir": "requests", "changes": 38075}
        """
        dir_changes = Counter()

        for add, delete, path in numstat:
            path = self._normalize_path(path)

            if self._should_ignore(path):
                continue

            # Répertoire de premier niveau
            top_dir = path.split("/", 1)[0] if "/" in path else "<root>"
            dir_changes[top_dir] += add + delete

        return [{"dir": d, "changes": ch} for d, ch in dir_changes.most_common(10)]

    def _calculate_metrics(
        self,
        commits: list[dict],
        hotspots: list[tuple[str, int]],
        by_extension: list[dict],
        numstat: list[tuple[int, int, str]],
        first_date: str | None,
        last_date: str | None,
    ) -> dict:
        """
        Calcule les métriques qualité du projet.

        Returns:
            Dictionnaire de métriques (années évolution, commits/an, ratios, etc.)
        """
        # Années d'évolution
        if first_date and last_date:
            from datetime import datetime

            first = datetime.fromisoformat(first_date)
            last = datetime.fromisoformat(last_date)
            years = max(1, (last.year - first.year))
        else:
            years = 1

        # Commits par an
        avg_commits_per_year = round(len(commits) / years, 1)

        # Moyenne changements par hotspot
        avg_changes_per_hotspot = round(sum(ch for _, ch in hotspots[:10]) / len(hotspots[:10]), 1) if hotspots else 0

        # Ratios code/tests/docs
        code_changes = 0
        tests_changes = 0
        docs_changes = 0
        total_changes = 0

        for add, delete, path in numstat:
            path = self._normalize_path(path)
            if self._should_ignore(path):
                continue

            changes = add + delete
            total_changes += changes

            path_lower = path.lower()

            # Code (heuristique : dossiers src/, lib/, module principal)
            # Détection automatique du package principal par nom du repo
            if path_lower.startswith(("src/", "lib/", f"{self.repo_name}/")) and Path(path).suffix == ".py":
                code_changes += changes

            # Tests
            elif path_lower.startswith(("tests/", "test/")):
                tests_changes += changes

            # Docs
            elif path_lower.startswith("docs/") or Path(path).suffix in [
                ".md",
                ".rst",
                ".adoc",
            ]:
                docs_changes += changes

        total_changes = max(1, total_changes)

        # Densité changements par fichier .py
        py_entry = next((e for e in by_extension if e["ext"] == ".py"), None)
        py_changes_per_file = (
            round(py_entry["changes"] / py_entry["files"], 1) if py_entry and py_entry["files"] > 0 else 0
        )

        return {
            "evolution_years": years,
            "avg_commits_per_year": avg_commits_per_year,
            "avg_changes_per_hotspot": avg_changes_per_hotspot,
            "changes_ratio": {
                "code_py": round(100 * code_changes / total_changes, 1),
                "tests": round(100 * tests_changes / total_changes, 1),
                "docs": round(100 * docs_changes / total_changes, 1),
            },
            "py_changes_per_file_avg": py_changes_per_file,
        }

    def _guess_runtime(self, language: str) -> str:
        """Devine le runtime depuis le langage détecté."""
        mapping = {
            "python": "python3",
            "javascript": "nodejs",
            "typescript": "nodejs",
            "java": "jvm",
            "go": "go",
            "ruby": "ruby",
            "php": "php",
            "rust": "cargo",
        }
        return mapping.get(language, "unknown")
