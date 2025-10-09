#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export complet de l'historique "passé en prod" à partir d'un dépôt Git local.
- Détecte la branche principale (origin/HEAD sinon candidats)
- Sélectionne tous les tags "prod" (pattern configurable, par défaut SemVer vX.Y.Z) MERGED dans la branche principale
- Trie les tags par SemVer
- Pour chaque release (intervalle prev_tag..tag), exporte tous les commits + fichiers modifiés
- Calcule agrégats (auteurs, fichiers, additions/suppressions, rollups par dossier/extension)
- Calcule l'alignement main vs dernier tag (ahead/behind/diverged)

Sorties:
  - prod_deploys.json     (index des releases + agrégats)
  - prod_commits.jsonl    (1 commit par ligne)
  - prod_files.jsonl      (1 fichier modifié par ligne)

Usage:
  python export_prod_history.py
  # options:
  #   TAGS_REGEX='^v?\\d+\\.\\d+\\.\\d+$' python export_prod_history.py
  #   MAIN_BRANCH=main python export_prod_history.py
"""

import json, os, re, subprocess, sys
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path

TAGS_REGEX = os.environ.get("TAGS_REGEX", r"^v?\d+\.\d+\.\d+$")
MAIN_CANDIDATES = os.environ.get("MAIN_CANDIDATES", "main,master,trunk,develop").split(",")

def sh(*args) -> list[str]:
    return subprocess.check_output(args, stderr=subprocess.DEVNULL).decode("utf-8", "ignore").splitlines()

def detect_repo_name() -> str:
    try:
        remote = sh("git", "config", "--get", "remote.origin.url")[0].strip()
        m = re.search(r"/([^/]+?)(?:\.git)?$", remote)
        return m.group(1) if m else Path(".").resolve().name
    except Exception:
        return Path(".").resolve().name

def detect_main_branch() -> str:
    # origin/HEAD -> refs/remotes/origin/<branch>
    try:
        ref = sh("git", "symbolic-ref", "refs/remotes/origin/HEAD")[0]
        return ref.rsplit("/", 1)[-1].strip()
    except Exception:
        pass
    for cand in MAIN_CANDIDATES:
        try:
            sh("git", "rev-parse", "--verify", f"origin/{cand}")
            return cand
        except Exception:
            continue
    return "main"

def semver_key(tag: str):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", tag)
    if not m: return (0,0,0)
    return tuple(int(x) for x in m.groups())

def list_prod_tags(main_branch: str, tag_pattern: str) -> list[str]:
    merged = sh("git", "tag", "--merged", main_branch)
    return sorted([t.strip() for t in merged if re.match(tag_pattern, t.strip())], key=semver_key)

def tag_datetime(tag: str) -> str | None:
    try:
        # tag annoté → date de tag; sinon date du commit pointé
        line = sh("git", "for-each-ref", f"refs/tags/{tag}", "--format=%(taggerdate:iso8601)")[0].strip()
        if line:
            return iso(line)
    except Exception:
        pass
    try:
        sha = sh("git", "rev-list", "-n", "1", tag)[0].strip()
        dt_ = sh("git", "show", "-s", "--format=%cI", sha)[0].strip()
        return dt_
    except Exception:
        return None

def iso(s: str) -> str:
    # normalise en ISO-8601
    try:
        return datetime.fromisoformat(s.replace(" ", "T").replace("Z","+00:00")).isoformat()
    except Exception:
        return s

def commit_list(range_expr: str) -> list[dict]:
    fmt = r"%H|%P|%an|%ae|%aI|%cn|%ce|%cI|%s"
    lines = sh("git", "log", "--date=iso", "--pretty=format:"+fmt, range_expr)
    out = []
    for l in lines:
        parts = l.split("|", 8)
        if len(parts) != 9: 
            continue
        sha, parents, an, ae, ai, cn, ce, ci, subj = parts
        out.append({
            "sha": sha,
            "parent_shas": [p for p in parents.split(" ") if p],
            "author_name": an, "author_email": ae, "author_when": ai,
            "committer_name": cn, "committer_email": ce, "committer_when": ci,
            "subject": subj, "merge": len([p for p in parents.split(' ') if p]) > 1
        })
    return out

def branches_containing_commit(sha: str) -> list[str]:
    try:
        # toutes les branches locales qui contiennent le commit
        lines = sh("git", "branch", "--contains", sha, "--format=%(refname:short)")
        return sorted([ln.strip() for ln in lines if ln.strip()])
    except Exception:
        return []

def files_for_commit(sha: str) -> tuple[list[dict], dict]:
    """
    Retourne:
      - liste de fichiers avec additions/suppressions (numstat)
      - agrégat global {'files_changed', 'lines_added', 'lines_deleted'}
    """
    # numstat: additions \t deletions \t path
    numstat = sh("git", "show", "--numstat", "--format=", sha)
    files = []
    add_total = del_total = 0
    for line in numstat:
        parts = line.split("\t")
        if len(parts) != 3: 
            continue
        a, d, p = parts
        try:
            a = 0 if a == "-" else int(a)
            d = 0 if d == "-" else int(d)
        except ValueError:
            a, d = 0, 0
        files.append({"path": p, "additions": a, "deletions": d})
        add_total += a; del_total += d

    # name-status pour le type (A/M/D/R/C)
    types = {}
    for ln in sh("git", "diff-tree", "--no-commit-id", "--name-status", "-r", sha):
        ln = ln.strip()
        if not ln: continue
        # formats possibles: "M\tpath" | "R100\told\tnew"
        parts = ln.split("\t")
        code = parts[0]
        if code.startswith("R") or code.startswith("C"):
            # rename/copy -> dernier champ = new path
            p = parts[-1]
            t = code[0]
        else:
            t = code
            p = parts[1] if len(parts) > 1 else ""
        types[p] = t

    # associer change_type
    for f in files:
        f["change_type"] = types.get(f["path"], "M")

    return files, {
        "files_changed": len(files),
        "lines_added": add_total,
        "lines_deleted": del_total
    }

def rollups(files: list[dict]) -> tuple[list[dict], list[dict]]:
    by_dir = Counter()
    by_ext = defaultdict(lambda: {"files": set(), "changes": 0})
    for f in files:
        path = f["path"].replace("\\","/").lstrip("./")
        changes = f["additions"] + f["deletions"]
        # dir rollup
        top = path.split("/",1)[0] if "/" in path else "<root>"
        by_dir[top] += changes
        # ext rollup
        ext = "." + path.split(".")[-1] if "." in path else "<noext>"
        by_ext[ext]["files"].add(path)
        by_ext[ext]["changes"] += changes
    dir_list = [{"dir": d, "changes": ch} for d, ch in by_dir.most_common()]
    ext_list = [{"ext": e, "files": len(v["files"]), "changes": v["changes"]} for e, v in by_ext.items()]
    ext_list.sort(key=lambda x: x["changes"], reverse=True)
    return dir_list, ext_list

def ahead_behind(main_branch: str, prod_ref: str) -> dict:
    try:
        # nb commits ahead/behind
        ahead = int(sh("git", "rev-list", "--left-right", "--count", f"{prod_ref}...{main_branch}")[0].split()[1])
        behind = int(sh("git", "rev-list", "--left-right", "--count", f"{prod_ref}...{main_branch}")[0].split()[0])
        main_head = sh("git", "rev-parse", main_branch)[0].strip()
        prod_head = sh("git", "rev-parse", prod_ref)[0].strip()
        return {
            "main_ahead_of_prod_commits": ahead,
            "prod_ahead_of_main_commits": behind,
            "diverged": (ahead > 0 and behind > 0),
            "main_head": main_head,
            "prod_head": prod_head
        }
    except Exception:
        return {"main_ahead_of_prod_commits": None, "prod_ahead_of_main_commits": None, "diverged": None, "main_head": None, "prod_head": None}

def main():
    repo = detect_repo_name()
    main_branch = detect_main_branch()

    tags = list_prod_tags(main_branch, TAGS_REGEX)
    if not tags:
        print(f"[ERR] Aucun tag ne matche {TAGS_REGEX} (ou pas merge dans {main_branch})", file=sys.stderr)
        sys.exit(1)

    # Ouvertures fichiers sortie
    f_commits = open("prod_commits.jsonl", "w", encoding="utf-8")
    f_files   = open("prod_files.jsonl", "w", encoding="utf-8")

    releases = []
    # itère sur toutes les releases (paires successives)
    for i, tag in enumerate(tags):
        prev = tags[i-1] if i > 0 else None
        rng = f"{prev}..{tag}" if prev else tag  # si premier, on prend tout jusqu'à ce tag
        commits = commit_list(rng)

        # collecte fichiers + agrégats
        all_files = []
        authors = set()
        added = deleted = 0
        window_start = None
        window_end = None

        for c in commits:
            files, agg = files_for_commit(c["sha"])
            # branches
            brs = branches_containing_commit(c["sha"])
            c_out = {
                "tag": tag,
                "commit": {
                    **c,
                    "branches_containing": brs
                },
                "stats": agg
            }
            f_commits.write(json.dumps(c_out, ensure_ascii=False) + "\n")

            for f in files:
                f_files.write(json.dumps({
                    "tag": tag,
                    "sha": c["sha"],
                    "path": f["path"],
                    "change_type": f.get("change_type","M"),
                    "additions": f["additions"],
                    "deletions": f["deletions"],
                    "dir": f["path"].replace("\\","/").lstrip("./").split("/",1)[0] if "/" in f["path"] else "<root>",
                    "ext": ("." + f["path"].split(".")[-1]) if "." in f["path"] else "<noext>"
                }, ensure_ascii=False) + "\n")

            all_files.extend(files)
            authors.add(f"{c['author_name']} <{c['author_email']}>")
            added  += c_out["stats"]["lines_added"]
            deleted += c_out["stats"]["lines_deleted"]

            # fenêtre temporelle
            d = c["committer_when"] or c["author_when"]
            try:
                dt = datetime.fromisoformat(d.replace(" ", "T").replace("Z","+00:00"))
            except Exception:
                dt = None
            if dt:
                window_start = dt if (window_start is None or dt < window_start) else window_start
                window_end   = dt if (window_end   is None or dt > window_end)   else window_end

        # rollups
        roll_dir, roll_ext = rollups(all_files)
        releases.append({
            "tag": tag,
            "tag_sha": sh("git","rev-list","-n","1", tag)[0].strip(),
            "released_at": tag_datetime(tag),
            "range": {"from": prev, "to": tag},
            "window": {
                "start": window_start.isoformat() if window_start else None,
                "end": window_end.isoformat() if window_end else None
            },
            "counts": {
                "commits": len(commits),
                "authors": len(authors),
                "files_changed": len({f["path"] for f in all_files}),
                "lines_added": added,
                "lines_deleted": deleted
            },
            "rollup_by_dir": roll_dir,
            "rollup_by_ext": roll_ext,
        })

    f_commits.close(); f_files.close()

    # Alignement avec main vs dernier tag
    last_tag = tags[-1]
    align = ahead_behind(main_branch, last_tag)

    # JSON index
    index = {
        "repo": repo,
        "main_branch": main_branch,
        "tag_pattern": TAGS_REGEX,
        "prod_releases": releases,
        "alignment": align
    }
    Path("prod_deploys.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ Écrit: prod_deploys.json, prod_commits.jsonl, prod_files.jsonl")

if __name__ == "__main__":
    main()
