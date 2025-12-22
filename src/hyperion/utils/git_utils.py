"""Utilitaires Git - Wrappers subprocess pour interactions Git."""

import re
import subprocess
from pathlib import Path


class GitCommandError(Exception):
    """Exception levée lors d'une erreur de commande Git."""

    pass


class GitRepo:
    """
    Wrapper pour interactions avec un dépôt Git local.

    Fournit des méthodes pour extraire commits, contributeurs, numstat,
    et détecter métadonnées (branche principale, langage, CI, licence).

    Example:
        >>> repo = GitRepo("/path/to/repo")
        >>> commits = repo.get_commits()
        >>> print(f"Total commits: {len(commits)}")
    """

    def __init__(self, repo_path: str):
        """
        Initialise le wrapper Git.

        Args:
            repo_path: Chemin vers le dépôt Git local

        Raises:
            GitCommandError: Si le chemin n'est pas un dépôt Git valide
        """
        self.repo_path = Path(repo_path).resolve()

        if not self.repo_path.exists():
            raise GitCommandError(f"Le chemin n'existe pas : {repo_path}")

        if not (self.repo_path / ".git").exists():
            raise GitCommandError(f"Pas un dépôt Git valide : {repo_path}")

    def _run_git(self, *args: str, check: bool = True) -> list[str]:
        """
        Exécute une commande Git et retourne les lignes de sortie.

        Args:
            *args: Arguments de la commande Git
            check: Si True, lève GitCommandError en cas d'erreur

        Returns:
            Liste des lignes de sortie (stdout)

        Raises:
            GitCommandError: Si la commande échoue et check=True
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path)] + list(args),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                check=check,
            )
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            if check:
                raise GitCommandError(f"Erreur Git: {e.stderr}") from e
            return []

    def get_name(self) -> str:
        """
        Retourne le nom du dépôt (depuis remote ou nom du dossier).

        Returns:
            Nom du dépôt
        """
        remote_url = self.get_remote_url()
        if remote_url:
            match = re.search(r"/([^/]+?)(?:\.git)?$", remote_url)
            if match:
                return match.group(1)

        return self.repo_path.name

    def get_remote_url(self) -> str | None:
        """
        Retourne l'URL du remote origin.

        Returns:
            URL du remote ou None si pas de remote
        """
        try:
            lines = self._run_git("config", "--get", "remote.origin.url", check=False)
            return lines[0].strip() if lines else None
        except Exception:
            return None

    def detect_main_branch(self, candidates: list[str] | None = None) -> str:
        """
        Détecte la branche principale du dépôt.

        Essaie d'abord origin/HEAD, puis teste les candidats.

        Args:
            candidates: Liste des branches candidates (défaut: main, master, trunk, develop)

        Returns:
            Nom de la branche principale
        """
        if candidates is None:
            candidates = ["main", "master", "trunk", "develop"]

        # Essayer origin/HEAD
        try:
            lines = self._run_git("symbolic-ref", "refs/remotes/origin/HEAD", check=False)
            if lines:
                return lines[0].rsplit("/", 1)[-1].strip()
        except Exception:
            pass

        # Tester les candidats
        for branch in candidates:
            try:
                self._run_git("rev-parse", "--verify", f"origin/{branch}", check=False)
                return branch
            except Exception:
                continue

        return "main"  # Défaut

    def get_commits(self, since: str | None = None) -> list[dict]:
        """
        Retourne la liste des commits avec métadonnées.

        Args:
            since: Filtre temporel optionnel (ex: "90.days", "2024-01-01")

        Returns:
            Liste de dicts avec : sha, author_name, author_email, author_date,
            committer_name, committer_email, committer_date, subject, is_merge
        """
        args = ["log", "--date=iso", "--pretty=format:%H|%an|%ae|%aI|%cn|%ce|%cI|%s|%P"]
        if since:
            args.append(f"--since={since}")

        lines = self._run_git(*args)
        commits = []

        for line in lines:
            parts = line.split("|", 8)
            if len(parts) < 8:
                continue

            sha, an, ae, ai, cn, ce, ci, subject, parents = parts
            parent_list = [p for p in parents.split() if p]

            commits.append(
                {
                    "sha": sha,
                    "author_name": an,
                    "author_email": ae,
                    "author_date": ai,
                    "committer_name": cn,
                    "committer_email": ce,
                    "committer_date": ci,
                    "subject": subject,
                    "is_merge": len(parent_list) > 1,
                    "parents": parent_list,
                }
            )

        return commits

    def get_contributors(self) -> list[dict]:
        """
        Retourne la liste des contributeurs avec nombre de commits.

        Returns:
            Liste de dicts avec : name, email, commits
        """
        lines = self._run_git("shortlog", "-sne", "--all")
        contributors = []

        for line in lines:
            line = line.strip()
            match = re.match(r"(\d+)\s+(.+)\s+<(.+)>$", line)
            if match:
                commits, name, email = match.groups()
                contributors.append({"name": name, "email": email, "commits": int(commits)})

        return contributors

    def get_numstat(self) -> list[tuple[int, int, str]]:
        """
        Retourne les statistiques numériques de tous les commits.

        Returns:
            Liste de tuples (additions, deletions, path)
        """
        lines = self._run_git("log", "--numstat", "--pretty=format:")
        numstat = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 3:
                continue

            add, delete, path = parts
            try:
                additions = 0 if add == "-" else int(add)
                deletions = 0 if delete == "-" else int(delete)
            except ValueError:
                additions, deletions = 0, 0

            numstat.append((additions, deletions, path))

        return numstat

    def count_recent_commits(self, days: int = 90) -> int:
        """
        Compte les commits des N derniers jours.

        Args:
            days: Nombre de jours (défaut: 90)

        Returns:
            Nombre de commits récents
        """
        lines = self._run_git("log", f"--since={days}.days", "--pretty=format:%H")
        return len(lines)

    def detect_language(self) -> str:
        """
        Détecte le langage principal du dépôt (heuristique basique).

        Analyse les extensions de fichiers présents.

        Returns:
            Nom du langage détecté ou "unknown"
        """
        # Compter les fichiers par extension
        extensions = {}

        try:
            lines = self._run_git("ls-files")
            for line in lines:
                path = Path(line)
                ext = path.suffix.lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
        except Exception:
            return "unknown"

        if not extensions:
            return "unknown"

        # Mapper extensions → langages
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".kt": "kotlin",
            ".swift": "swift",
        }

        # Trouver l'extension la plus fréquente
        most_common = max(extensions.items(), key=lambda x: x[1])
        return lang_map.get(most_common[0], "unknown")

    def detect_ci(self) -> str:
        """
        Détecte le système CI/CD utilisé.

        Returns:
            Nom du CI détecté ou "unknown"
        """
        ci_patterns = {
            "github-actions": [".github/workflows/"],
            "gitlab-ci": [".gitlab-ci.yml"],
            "jenkins": ["Jenkinsfile"],
            "travis": [".travis.yml"],
            "circle-ci": [".circleci/"],
            "azure-pipelines": ["azure-pipelines.yml"],
            "drone": [".drone.yml"],
        }

        for ci_name, patterns in ci_patterns.items():
            for pattern in patterns:
                check_path = self.repo_path / pattern
                if check_path.exists():
                    return ci_name

        return "unknown"

    def detect_license(self) -> str | None:
        """
        Détecte la licence du projet (heuristique basique).

        Returns:
            Nom de la licence détectée ou None
        """
        license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "COPYING.txt"]

        for filename in license_files:
            license_path = self.repo_path / filename
            if not license_path.exists():
                continue

            try:
                content = license_path.read_text(encoding="utf-8", errors="ignore")[:2000].lower()

                # Patterns de détection
                if "apache license" in content or "apache-2.0" in content:
                    return "Apache-2.0"
                elif "mit license" in content:
                    return "MIT"
                elif "bsd license" in content or "redistribution and use" in content:
                    return "BSD-3-Clause"
                elif "gnu general public license" in content:
                    if "version 3" in content:
                        return "GPL-3.0"
                    elif "version 2" in content:
                        return "GPL-2.0"
                    return "GPL"
                elif "mozilla public license" in content:
                    return "MPL-2.0"
                else:
                    return "UNKNOWN"
            except Exception:
                continue

        return None

    def get_date_range(self) -> tuple[str | None, str | None]:
        """
        Retourne la date du premier et dernier commit.

        Returns:
            Tuple (first_commit_date, last_commit_date) en ISO format
        """
        commits = self.get_commits()
        if not commits:
            return None, None

        dates = [c["committer_date"] for c in commits if c.get("committer_date")]
        if not dates:
            return None, None

        return min(dates), max(dates)
