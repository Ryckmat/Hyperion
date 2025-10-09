#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingestion Neo4j des exports 'export_prod_history.py':
  - prod_deploys.json   (index releases + alignement)
  - prod_commits.jsonl  (1 commit/ligne)
  - prod_files.jsonl    (1 fichier touché/ligne)

Crée les nœuds & relations:
  (:Repo)-[:HAS_BRANCH]->(:Branch)
  (:Branch)-[:CONTAINS]->(:Commit)
  (:Commit)-[:COMMITTED_BY]->(:Author)
  (:Commit)-[:TOUCHED {add,del,type}]->(:File)-[:IN_DIR]->(:Dir)
  (:Commit)-[:IN_RELEASE]->(:Tag)
  (optionnel) (:Repo)-[:HAS_TAG]->(:Tag)

Usage:
  pip install neo4j~=5.28.0
  python ingest_prod_history_to_neo4j.py
"""

from neo4j import GraphDatabase
from pathlib import Path
import json
import os
import re
from typing import Iterable

# ========= CONFIG =========
URI  = os.environ.get("NEO_URI",  "")
AUTH = (os.environ.get("NEO_USER", ""), os.environ.get("NEO_PASS", ""))
DB   = os.environ.get("NEO_DB", "s")

DATA_DIR = Path(os.environ.get("DATA_DIR", "../data/"))  # dossier où se trouvent les JSON/JSONL
REPO_NAME = os.environ.get("REPO_NAME", Path(".").resolve().name)  # ou fixe "requests"

BATCH_SIZE_COMMITS = int(os.environ.get("BATCH_COMMITS", "500"))
BATCH_SIZE_FILES   = int(os.environ.get("BATCH_FILES",   "2000"))

# ========= HELPERS =========
def chunks(it: Iterable, size: int):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf

def normalize_email(email: str) -> str:
    if not email:
        return ""
    e = email.strip().lower()
    e = re.sub(r"\+.*(?=@users\.noreply\.github\.com)", "", e)
    if e.endswith("@gmail.com"):
        local, domain = e.split("@", 1)
        local = local.replace(".", "")
        e = f"{local}@{domain}"
    return e

# ========= MAIN =========
def main():
    prod_deploys = json.loads((DATA_DIR / "prod_deploys.json").read_text(encoding="utf-8"))
    commits_path = DATA_DIR / "prod_commits.jsonl"
    files_path   = DATA_DIR / "prod_files.jsonl"

    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()

    with driver.session(database=DB) as session:
        # 1) Contraintes / index
        session.execute_write(setup_constraints)

        # 2) Nœuds Repo + Branch + Tag (depuis prod_deploys.json)
        session.execute_write(upsert_repo_branches_tags, prod_deploys, REPO_NAME)

        # 3) Commits + Authors + relations COMMITTED_BY / IN_RELEASE / CONTAINS (branches)
        with commits_path.open("r", encoding="utf-8") as f:
            batch = []
            for line in f:
                if not line.strip():
                    continue
                batch.append(json.loads(line))
                if len(batch) >= BATCH_SIZE_COMMITS:
                    session.execute_write(upsert_commits_batch, batch)
                    batch = []
            if batch:
                session.execute_write(upsert_commits_batch, batch)

        # 4) Files + relations TOUCHED + Dir
        with files_path.open("r", encoding="utf-8") as f:
            for batch in chunks((json.loads(l) for l in f if l.strip()), BATCH_SIZE_FILES):
                session.execute_write(upsert_files_batch, batch)

    driver.close()
    print("✅ Ingestion terminée.")

# ========= QUERIES =========
def setup_constraints(tx):
    statements = [
        "CREATE CONSTRAINT repo IF NOT EXISTS FOR (r:Repo) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT commit IF NOT EXISTS FOR (c:Commit) REQUIRE c.sha IS UNIQUE",
        "CREATE CONSTRAINT tag IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT author IF NOT EXISTS FOR (a:Author) REQUIRE a.email IS UNIQUE",
        "CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path)",
        "CREATE INDEX dir_path IF NOT EXISTS FOR (d:Dir) ON (d.path)",
        "CREATE INDEX branch_name IF NOT EXISTS FOR (b:Branch) ON (b.name)",
    ]
    for stmt in statements:
        tx.run(stmt)


def upsert_repo_branches_tags(tx, prod_deploys: dict, repo_name: str):
    main_branch = prod_deploys.get("main_branch", "main")
    releases = prod_deploys.get("prod_releases", [])

    # Repo + main branch
    tx.run("""
    MERGE (r:Repo {name:$repo})
    MERGE (b:Branch {name:$branch})
    ON CREATE SET b.is_main=true
    MERGE (r)-[:HAS_BRANCH]->(b)
    """, repo=repo_name, branch=main_branch)

    # Tags
    for rel in releases:
        tx.run("""
        MERGE (t:Tag {name:$name})
        SET t.released_at = $released_at, t.tag_sha = $sha
        WITH t
        MATCH (r:Repo {name:$repo})
        MERGE (r)-[:HAS_TAG]->(t)
        """, name=rel["tag"], released_at=rel.get("released_at"), sha=rel.get("tag_sha"), repo=repo_name)

def upsert_commits_batch(tx, batch: list[dict]):
    """
    batch d'objets issus de prod_commits.jsonl
    Chaque item:
      {
        "tag": "...",
        "commit": {...},
        "stats": {"files_changed":..,"lines_added":..,"lines_deleted":..}
      }
    """
    # Préparer les lignes
    rows = []
    for it in batch:
        c = it["commit"]
        rows.append({
            "tag": it["tag"],
            "sha": c["sha"],
            "subject": c.get("subject"),
            "date": c.get("committer_when") or c.get("author_when"),
            "isMerge": bool(c.get("merge")),
            "author_name": c.get("author_name"),
            "author_email": normalize_email(c.get("author_email","")),
            "branches": c.get("branches_containing", []),
        })

    # Commits + Authors + relations
    tx.run("""
    UNWIND $rows AS row
    MERGE (c:Commit {sha: row.sha})
      ON CREATE SET c.subject = row.subject, c.date = row.date, c.files_changed = 0, c.isMerge = row.isMerge
      ON MATCH  SET c.subject = coalesce(c.subject, row.subject),
                  c.date    = coalesce(c.date, row.date),
                  c.isMerge = coalesce(c.isMerge, row.isMerge)
    MERGE (a:Author {email: row.author_email})
      ON CREATE SET a.name = row.author_name
      ON MATCH  SET a.name = coalesce(a.name, row.author_name)
    MERGE (a)-[:COMMITTED_BY]->(c)
    WITH row, c
    MERGE (t:Tag {name: row.tag})
    MERGE (c)-[:IN_RELEASE]->(t)
    WITH row, c
    UNWIND row.branches AS br
      MERGE (b:Branch {name: br})
      MERGE (:Repo {name:$repo})-[:HAS_BRANCH]->(b)
      MERGE (b)-[:CONTAINS]->(c)
    """, rows=rows, repo=REPO_NAME)

def upsert_files_batch(tx, batch: list[dict]):
    """
    batch d'objets issus de prod_files.jsonl
    Chaque item:
      {
        "tag":"...","sha":"...","path":"...","change_type":"M",
        "additions":X,"deletions":Y,"dir":"...","ext":".py"
      }
    """
    tx.run("""
    UNWIND $rows AS row
    MERGE (c:Commit {sha: row.sha})
    MERGE (f:File {path: row.path})
      ON CREATE SET f.ext = row.ext
      ON MATCH  SET f.ext = coalesce(f.ext, row.ext)
    MERGE (c)-[r:TOUCHED]->(f)
      ON CREATE SET r.add = row.additions, r.del = row.deletions, r.type = row.change_type
      ON MATCH  SET r.add = coalesce(r.add, row.additions),
                  r.del = coalesce(r.del, row.deletions),
                  r.type = coalesce(r.type, row.change_type)
    WITH row, f
    MERGE (d:Dir {path: row.dir})
    MERGE (f)-[:IN_DIR]->(d)
    """, rows=batch)

# ========= RUN =========
if __name__ == "__main__":
    main()
