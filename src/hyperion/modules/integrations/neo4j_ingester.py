"""Ingestion Neo4j - Importe les profils Hyperion dans le graphe."""

import contextlib
from pathlib import Path

import yaml
from neo4j import GraphDatabase

from hyperion.config import (
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
)


class Neo4jIngester:
    """
    Ingère un profil Hyperion dans Neo4j.

    Crée le modèle de graphe :
    - (:Repo)-[:HAS_CONTRIBUTOR]->(:Contributor)
    - (:Repo)-[:HAS_HOTSPOT]->(:Hotspot)
    - (:Repo)-[:HAS_DIRECTORY]->(:Directory)
    - (:Repo)-[:HAS_EXTENSION]->(:Extension)

    Example:
        >>> ingester = Neo4jIngester()
        >>> ingester.ingest_profile("data/repositories/requests/profile.yaml")
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ):
        """
        Initialise la connexion Neo4j.

        Args:
            uri: URI Neo4j (défaut: depuis config)
            user: Username (défaut: depuis config)
            password: Password (défaut: depuis config)
            database: Database name (défaut: depuis config)
        """
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.database = database or NEO4J_DATABASE

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.driver.verify_connectivity()

    def close(self):
        """Ferme la connexion Neo4j."""
        self.driver.close()

    def ingest_profile(self, profile_path: str) -> dict:
        """
        Ingère un profil Hyperion complet dans Neo4j.

        Args:
            profile_path: Chemin vers le fichier profile.yaml

        Returns:
            Statistiques d'ingestion
        """
        # Charger le profil
        profile = self._load_profile(profile_path)

        stats = {
            "repo": 0,
            "contributors": 0,
            "hotspots": 0,
            "directories": 0,
            "extensions": 0,
            "metrics": 0,
        }

        with self.driver.session(database=self.database) as session:
            # 1. Contraintes et index
            session.execute_write(self._setup_constraints)

            # 2. Créer le nœud Repo
            repo_name = profile["service"]
            session.execute_write(self._create_repo, profile)
            stats["repo"] = 1

            # 3. Ingérer contributeurs
            contributors = profile.get("git_summary", {}).get("contributors_top10", [])
            if contributors:
                session.execute_write(self._ingest_contributors, repo_name, contributors)
                stats["contributors"] = len(contributors)

            # 4. Ingérer hotspots
            hotspots = profile.get("git_summary", {}).get("hotspots_top10", [])
            if hotspots:
                session.execute_write(self._ingest_hotspots, repo_name, hotspots)
                stats["hotspots"] = len(hotspots)

            # 5. Ingérer répertoires
            directories = profile.get("git_summary", {}).get("directories_top", [])
            if directories:
                session.execute_write(self._ingest_directories, repo_name, directories)
                stats["directories"] = len(directories)

            # 6. Ingérer extensions
            extensions = profile.get("git_summary", {}).get("by_extension", [])
            if extensions:
                session.execute_write(self._ingest_extensions, repo_name, extensions)
                stats["extensions"] = len(extensions)

            # 7. Ingérer métriques
            metrics = profile.get("metrics", {})
            if metrics:
                session.execute_write(self._ingest_metrics, repo_name, metrics)
                stats["metrics"] = 1

        return stats

    def _load_profile(self, profile_path: str) -> dict:
        """Charge un profil YAML."""
        path = Path(profile_path)
        if not path.exists():
            raise FileNotFoundError(f"Profil introuvable : {profile_path}")

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _setup_constraints(self, tx):
        """Crée les contraintes et index Neo4j."""
        constraints = [
            "CREATE CONSTRAINT repo_name IF NOT EXISTS FOR (r:Repo) REQUIRE r.name IS UNIQUE",
            ("CREATE CONSTRAINT contributor_id IF NOT EXISTS " "FOR (c:Contributor) REQUIRE c.id IS UNIQUE"),
            "CREATE CONSTRAINT hotspot_path IF NOT EXISTS FOR (h:Hotspot) REQUIRE h.path IS UNIQUE",
            "CREATE INDEX hotspot_changes IF NOT EXISTS FOR (h:Hotspot) ON (h.changes)",
            "CREATE INDEX contributor_commits IF NOT EXISTS FOR (c:Contributor) ON (c.commits)",
        ]

        for constraint in constraints:
            with contextlib.suppress(Exception):
                tx.run(constraint)

    def _create_repo(self, tx, profile: dict):
        """Crée le nœud Repository principal."""
        repo_info = profile["repositories"][0]
        git_summary = profile.get("git_summary", {})

        tx.run(
            """
        MERGE (r:Repo {name: $name})
        SET r.url = $url,
            r.language = $language,
            r.license = $license,
            r.ci = $ci,
            r.runtime = $runtime,
            r.default_branch = $default_branch,
            r.commits = $commits,
            r.contributors = $contributors,
            r.first_commit = $first_commit,
            r.last_commit = $last_commit,
            r.recent_commits_90d = $recent_commits
        """,
            name=profile["service"],
            url=repo_info.get("url"),
            language=repo_info.get("main_language"),
            license=repo_info.get("license"),
            ci=profile["tech"].get("ci"),
            runtime=profile["tech"].get("runtime"),
            default_branch=repo_info.get("default_branch"),
            commits=git_summary.get("commits", 0),
            contributors=git_summary.get("contributors", 0),
            first_commit=git_summary.get("first_commit"),
            last_commit=git_summary.get("last_commit"),
            recent_commits=git_summary.get("recent_commits_90d", 0),
        )

    def _ingest_contributors(self, tx, repo_name: str, contributors: list):
        """Ingère les contributeurs."""
        tx.run(
            """
        UNWIND $contributors AS contrib
        MERGE (c:Contributor {id: $repo + '::' + contrib.email})
        SET c.name = contrib.name,
            c.email = contrib.email,
            c.commits = contrib.commits
        WITH c
        MATCH (r:Repo {name: $repo})
        MERGE (r)-[rel:HAS_CONTRIBUTOR]->(c)
        SET rel.commits = c.commits
        """,
            repo=repo_name,
            contributors=contributors,
        )

    def _ingest_hotspots(self, tx, repo_name: str, hotspots: list):
        """Ingère les hotspots."""
        tx.run(
            """
        UNWIND $hotspots AS hot
        MERGE (h:Hotspot {path: hot.path})
        SET h.changes = hot.changes,
            h.repo = $repo
        WITH h
        MATCH (r:Repo {name: $repo})
        MERGE (r)-[rel:HAS_HOTSPOT]->(h)
        SET rel.changes = h.changes
        """,
            repo=repo_name,
            hotspots=hotspots,
        )

    def _ingest_directories(self, tx, repo_name: str, directories: list):
        """Ingère les répertoires."""
        tx.run(
            """
        UNWIND $directories AS dir
        MERGE (d:Directory {name: $repo + '::' + dir.dir})
        SET d.dir = dir.dir,
            d.changes = dir.changes,
            d.repo = $repo
        WITH d
        MATCH (r:Repo {name: $repo})
        MERGE (r)-[rel:HAS_DIRECTORY]->(d)
        SET rel.changes = d.changes
        """,
            repo=repo_name,
            directories=directories,
        )

    def _ingest_extensions(self, tx, repo_name: str, extensions: list):
        """Ingère les extensions."""
        tx.run(
            """
        UNWIND $extensions AS ext
        MERGE (e:Extension {name: $repo + '::' + ext.ext})
        SET e.ext = ext.ext,
            e.files = ext.files,
            e.changes = ext.changes,
            e.repo = $repo
        WITH e
        MATCH (r:Repo {name: $repo})
        MERGE (r)-[rel:HAS_EXTENSION]->(e)
        SET rel.files = e.files,
            rel.changes = e.changes
        """,
            repo=repo_name,
            extensions=extensions,
        )

    def _ingest_metrics(self, tx, repo_name: str, metrics: dict):
        """Ingère les métriques dans le nœud Repo."""
        tx.run(
            """
        MATCH (r:Repo {name: $repo})
        SET r.evolution_years = $evolution_years,
            r.avg_commits_per_year = $avg_commits_per_year,
            r.avg_changes_per_hotspot = $avg_changes_per_hotspot,
            r.ratio_code = $ratio_code,
            r.ratio_tests = $ratio_tests,
            r.ratio_docs = $ratio_docs,
            r.py_changes_per_file = $py_changes_per_file
        """,
            repo=repo_name,
            evolution_years=metrics.get("evolution_years"),
            avg_commits_per_year=metrics.get("avg_commits_per_year"),
            avg_changes_per_hotspot=metrics.get("avg_changes_per_hotspot"),
            ratio_code=metrics.get("changes_ratio", {}).get("code_py"),
            ratio_tests=metrics.get("changes_ratio", {}).get("tests"),
            ratio_docs=metrics.get("changes_ratio", {}).get("docs"),
            py_changes_per_file=metrics.get("py_changes_per_file_avg"),
        )

    def clear_repo(self, repo_name: str):
        """Supprime toutes les données d'un repo."""
        with self.driver.session(database=self.database) as session:
            session.run(
                """
            MATCH (r:Repo {name: $name})
            OPTIONAL MATCH (r)-[rel]->(n)
            DELETE rel, n, r
            """,
                name=repo_name,
            )

    def get_repo_stats(self, repo_name: str) -> dict:
        """Récupère les stats d'un repo depuis Neo4j."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
            MATCH (r:Repo {name: $name})
            OPTIONAL MATCH (r)-[:HAS_CONTRIBUTOR]->(c:Contributor)
            OPTIONAL MATCH (r)-[:HAS_HOTSPOT]->(h:Hotspot)
            OPTIONAL MATCH (r)-[:HAS_DIRECTORY]->(d:Directory)
            OPTIONAL MATCH (r)-[:HAS_EXTENSION]->(e:Extension)
            RETURN r,
                   count(DISTINCT c) as contributors,
                   count(DISTINCT h) as hotspots,
                   count(DISTINCT d) as directories,
                   count(DISTINCT e) as extensions
            """,
                name=repo_name,
            )

            record = result.single()
            if not record:
                return {}

            repo = dict(record["r"])
            return {
                "name": repo.get("name"),
                "commits": repo.get("commits"),
                "contributors_count": record["contributors"],
                "hotspots_count": record["hotspots"],
                "directories_count": record["directories"],
                "extensions_count": record["extensions"],
                "language": repo.get("language"),
                "license": repo.get("license"),
            }
