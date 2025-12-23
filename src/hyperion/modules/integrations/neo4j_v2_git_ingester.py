"""Ingestion Neo4j v2 - Git History avec tracking Commit->Contributor->File."""

import subprocess
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase


class Neo4jV2GitIngester:
    """
    Ingère l'historique Git dans Neo4j v2 avec tracking complet.

    Crée le modèle de graphe manquant :
    - (:Commit)-[:AUTHORED_BY]->(:Contributor)
    - (:Commit)-[:MODIFIES]->(:File) avec action: CREATE|UPDATE|DELETE
    - (:Directory)-[:CONTAINS]->(:File)

    Example:
        >>> ingester = Neo4jV2GitIngester()
        >>> ingester.ingest_git_history("/path/to/repo")
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "hyperion123",
        database: str = "neo4j",
    ):
        """
        Initialise la connexion Neo4j.

        Args:
            uri: URI Neo4j
            user: Username
            password: Password
            database: Database name
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.driver.verify_connectivity()

    def close(self):
        """Ferme la connexion Neo4j."""
        self.driver.close()

    def ingest_git_history(self, repo_path: str | Path) -> dict[str, int]:
        """
        Ingère tout l'historique Git dans Neo4j v2.

        Args:
            repo_path: Chemin vers le repository Git

        Returns:
            Statistiques d'ingestion
        """
        repo_path = Path(repo_path)
        repo_name = repo_path.name

        if not (repo_path / ".git").exists():
            raise ValueError(f"Repository Git non trouvé : {repo_path}")

        stats = {
            "commits": 0,
            "contributors": 0,
            "files_modified": 0,
            "directories": 0,
            "commit_relations": 0,
            "file_relations": 0,
            "directory_relations": 0,
        }

        with self.driver.session(database=self.database) as session:
            # 1. Setup contraintes et index
            session.execute_write(self._setup_v2_constraints)

            # 2. Ingérer contributeurs
            contributors = self._extract_contributors(repo_path)
            session.execute_write(self._ingest_contributors, repo_name, contributors)
            stats["contributors"] = len(contributors)

            # 3. Ingérer commits avec relations
            commits_data = self._extract_commits_with_files(repo_path)
            for commit_data in commits_data:
                session.execute_write(self._ingest_commit, repo_name, commit_data)
                stats["commits"] += 1
                stats["commit_relations"] += 1
                stats["file_relations"] += len(commit_data["files"])

            # 4. Créer relations Directory->File
            directory_files = self._extract_directory_structure(repo_path)
            session.execute_write(
                self._ingest_directory_relations, repo_name, directory_files
            )
            stats["directories"] = len(directory_files)
            stats["directory_relations"] = sum(
                len(files) for files in directory_files.values()
            )

        return stats

    def _setup_v2_constraints(self, tx):
        """Crée les contraintes et index Neo4j v2 pour Git."""
        constraints = [
            "CREATE CONSTRAINT commit_hash IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE",
            (
                "CREATE CONSTRAINT contributor_v2_id IF NOT EXISTS "
                "FOR (cont:Contributor) REQUIRE cont.id IS UNIQUE"
            ),
            "CREATE CONSTRAINT file_v2_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            (
                "CREATE CONSTRAINT directory_v2_path IF NOT EXISTS "
                "FOR (d:Directory) REQUIRE d.path IS UNIQUE"
            ),
            "CREATE INDEX commit_date IF NOT EXISTS FOR (c:Commit) ON (c.date)",
            "CREATE INDEX contributor_email IF NOT EXISTS FOR (cont:Contributor) ON (cont.email)",
        ]

        for constraint in constraints:
            try:
                tx.run(constraint)
            except Exception:
                pass  # Contrainte existe déjà

    def _extract_contributors(self, repo_path: Path) -> list[dict[str, Any]]:
        """Extrait la liste des contributeurs."""
        cmd = [
            "git",
            "-C",
            str(repo_path),
            "log",
            "--format=%ae|%an",
            "--all",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        contributors = {}
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                email, name = line.split("|", 1)
                if email not in contributors:
                    contributors[email] = {"email": email, "name": name, "commits": 0}
                contributors[email]["commits"] += 1

        return list(contributors.values())

    def _extract_commits_with_files(self, repo_path: Path) -> list[dict[str, Any]]:
        """
        Extrait commits avec fichiers modifiés et actions (CREATE/UPDATE/DELETE).
        """
        # Format: hash|author_email|date|subject
        cmd = [
            "git",
            "-C",
            str(repo_path),
            "log",
            "--format=%H|%ae|%ai|%s",
            "--all",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        commits_data = []
        for line in result.stdout.strip().split("\n"):
            if "|" not in line:
                continue

            parts = line.split("|", 3)
            if len(parts) != 4:
                continue

            hash_val, author_email, date, subject = parts

            # Récupérer fichiers modifiés pour ce commit
            files_modified = self._get_commit_files(repo_path, hash_val)

            commit_data = {
                "hash": hash_val,
                "author_email": author_email,
                "date": date,
                "subject": subject,
                "files": files_modified,
            }
            commits_data.append(commit_data)

        return commits_data

    def _get_commit_files(self, repo_path: Path, commit_hash: str) -> list[dict[str, str]]:
        """Récupère les fichiers modifiés par un commit avec l'action (A/M/D)."""
        cmd = [
            "git",
            "-C",
            str(repo_path),
            "show",
            "--name-status",
            "--format=",
            commit_hash,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            return []

        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue

            status, file_path = parts

            # Mapper les statuts Git vers nos actions
            action_map = {
                "A": "CREATE",
                "M": "UPDATE",
                "D": "DELETE",
                "C": "CREATE",  # Copy
                "R": "UPDATE",  # Rename
            }

            action = action_map.get(status[0], "UPDATE")

            files.append({"path": file_path, "action": action})

        return files

    def _extract_directory_structure(self, repo_path: Path) -> dict[str, list[str]]:
        """Extrait la structure des répertoires avec leurs fichiers."""
        # Récupérer tous les fichiers trackés par Git
        cmd = ["git", "-C", str(repo_path), "ls-tree", "-r", "--name-only", "HEAD"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            return {}

        directory_files = {}
        for file_path in result.stdout.strip().split("\n"):
            if not file_path:
                continue

            # Extraire le directory parent
            path_obj = Path(file_path)
            if path_obj.parent == Path("."):
                directory = "."  # Root directory
            else:
                directory = str(path_obj.parent)

            if directory not in directory_files:
                directory_files[directory] = []

            directory_files[directory].append(file_path)

        return directory_files

    def _ingest_contributors(self, tx, repo_name: str, contributors: list[dict[str, Any]]):
        """Ingère les contributeurs avec leurs stats."""
        tx.run(
            """
            UNWIND $contributors AS contrib
            MERGE (c:Contributor {id: $repo + '::' + contrib.email})
            SET c.email = contrib.email,
                c.name = contrib.name,
                c.commits_count = contrib.commits,
                c.repo = $repo
            """,
            repo=repo_name,
            contributors=contributors,
        )

    def _ingest_commit(self, tx, repo_name: str, commit_data: dict[str, Any]):
        """Ingère un commit avec ses relations vers Contributor et Files."""
        # Créer le commit
        # Convertir date ISO format pour Neo4j
        import datetime as dt

        try:
            # Parse git date format: "2024-12-01 18:13:38 +0000"
            dt_obj = dt.datetime.fromisoformat(commit_data["date"].replace(" +", "+"))
            date_iso = dt_obj.isoformat()
        except (ValueError, AttributeError):
            # Fallback si parsing échoue
            date_iso = "2024-01-01T00:00:00"

        tx.run(
            """
            MERGE (c:Commit {hash: $hash})
            SET c.date = datetime($date),
                c.subject = $subject,
                c.repo = $repo
            """,
            hash=commit_data["hash"],
            date=date_iso,
            subject=commit_data["subject"],
            repo=repo_name,
        )

        # Relation Commit -> Contributor
        tx.run(
            """
            MATCH (c:Commit {hash: $hash})
            MATCH (contrib:Contributor {id: $contrib_id})
            MERGE (c)-[:AUTHORED_BY]->(contrib)
            """,
            hash=commit_data["hash"],
            contrib_id=f"{repo_name}::{commit_data['author_email']}",
        )

        # Relations Commit -> File avec action
        for file_info in commit_data["files"]:
            # Créer le fichier s'il n'existe pas
            tx.run(
                """
                MERGE (f:File {path: $path})
                SET f.repo = $repo
                """,
                path=file_info["path"],
                repo=repo_name,
            )

            # Relation Commit -> File avec action
            tx.run(
                """
                MATCH (c:Commit {hash: $hash})
                MATCH (f:File {path: $path})
                MERGE (c)-[:MODIFIES {action: $action}]->(f)
                """,
                hash=commit_data["hash"],
                path=file_info["path"],
                action=file_info["action"],
            )

    def _ingest_directory_relations(
        self, tx, repo_name: str, directory_files: dict[str, list[str]]
    ):
        """Ingère les relations Directory -> File."""
        for directory, files in directory_files.items():
            # Créer le directory
            tx.run(
                """
                MERGE (d:Directory {path: $path})
                SET d.repo = $repo
                """,
                path=directory,
                repo=repo_name,
            )

            # Relations Directory -> File
            tx.run(
                """
                MATCH (d:Directory {path: $dir_path})
                UNWIND $files AS file_path
                MATCH (f:File {path: file_path})
                MERGE (d)-[:CONTAINS]->(f)
                """,
                dir_path=directory,
                files=files,
            )

    def get_commit_stats(self, repo_name: str) -> dict[str, Any]:
        """Récupère les statistiques Git depuis Neo4j."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (c:Commit {repo: $repo})
                OPTIONAL MATCH (c)-[:AUTHORED_BY]->(contrib:Contributor)
                OPTIONAL MATCH (c)-[:MODIFIES]->(f:File)
                RETURN count(DISTINCT c) as commits,
                       count(DISTINCT contrib) as contributors,
                       count(DISTINCT f) as files_touched,
                       min(c.date) as first_commit,
                       max(c.date) as last_commit
                """,
                repo=repo_name,
            )

            record = result.single()
            if not record:
                return {}

            return dict(record)

    def clear_git_data(self, repo_name: str):
        """Supprime toutes les données Git d'un repo."""
        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MATCH (c:Commit {repo: $repo})
                OPTIONAL MATCH (c)-[r1]-()
                OPTIONAL MATCH (contrib:Contributor {repo: $repo})
                OPTIONAL MATCH (contrib)-[r2]-()
                OPTIONAL MATCH (d:Directory {repo: $repo})
                OPTIONAL MATCH (d)-[r3]-()
                DELETE r1, r2, r3, c, contrib, d
                """,
                repo=repo_name,
            )
