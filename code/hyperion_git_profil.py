#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un YAML Hyperion complet à partir d'un dépôt Git local (Windows OK).
- Détecte nom du repo + remote
- Résumé git (commits, période, contributeurs dédupliqués)
- Hotspots recalculés (top 10) avec filtres binaires + vendored + bruit docs/README/HISTORY
- Top contributeurs (fusion d’alias/email variants)
- Stats par extension, top répertoires
- Détection CI & license locales
- KPIs: ratios code/tests/docs, densité moyenne de changements par fichier .py

Sortie: data/{repo}.yaml
Dépendances: PyYAML (pip install pyyaml)
"""
import subprocess, collections, yaml, datetime as dt, pathlib, re, os, sys

def sh(*args) -> list[str]:
    out = subprocess.check_output(args, stderr=subprocess.DEVNULL)
    return out.decode("utf-8", "ignore").splitlines()

# ---------- Repo & remote ----------
try:
    remote = sh("git","config","--get","remote.origin.url")[0].strip()
except Exception:
    remote = ""
m = re.search(r"/([^/]+?)(?:\.git)?$", remote)
repo_name = m.group(1) if m else pathlib.Path(".").resolve().name

# ---------- Log (hash|author|date|subject) ----------
tsv = sh("git","log","--date=iso","--pretty=format:%H|%an <%ae>|%ad|%s")
commits = len(tsv)
dates, authors = [], []
for l in tsv:
    parts = l.split("|", 3)
    if len(parts) >= 3:
        authors.append(parts[1])
        ds = parts[2].replace("\ufeff","")  # BOM safe
        try:
            dates.append(dt.datetime.fromisoformat(ds.replace("Z","+00:00")))
        except Exception:
            pass

first = min(dates).date().isoformat() if dates else None
last  = max(dates).date().isoformat() if dates else None

# ---------- Dédup contributeurs ----------
def normalize_email(email: str) -> str:
    e = email.strip().lower()
    e = re.sub(r"\+.*(?=@users\.noreply\.github\.com)","", e)  # noreply+tag
    if e.endswith("@gmail.com"):
        local, domain = e.split("@",1)
        local = local.replace(".","")           # john.smith -> johnsmith
        e = f"{local}@{domain}"
    return e

def normalize_name(name: str) -> str:
    n = re.sub(r"\s+"," ", name).strip()
    n = re.sub(r"\s*\[bot\]\s*$", "", n, flags=re.I)
    return n.title()

def canonical_author(s: str) -> tuple[str,str]:
    m = re.match(r"(.+)\s+<(.+)>$", s.strip())
    if not m:
        return (normalize_name(s), "")
    name, email = m.group(1), m.group(2)
    return (normalize_name(name), normalize_email(email))

canon_pairs = [canonical_author(a) for a in authors]
contributors_count = len({ f"{n} <{e}>" for n,e in canon_pairs })

# ---------- Top contributeurs (fusion nom+emails) ----------
agg = {}
for line in sh("git","shortlog","-sne"):
    line = line.strip()
    m = re.match(r"(\d+)\s+(.+)$", line)
    if not m: continue
    nb, who = int(m.group(1)), m.group(2)
    m2 = re.match(r"(.+)\s+<(.+)>$", who)
    if m2:
        name, email = normalize_name(m2.group(1)), normalize_email(m2.group(2))
    else:
        name, email = normalize_name(who), ""
    key = normalize_name(name)  # fusion sous le même nom
    if key in agg:
        agg[key]["commits"] += nb
        if email and email not in agg[key]["emails"]:
            agg[key]["emails"].append(email)
    else:
        agg[key] = {"name": name, "emails": [email] if email else [], "commits": nb}
contributors_top10 = sorted(
    ({"name": v["name"], "email": (v["emails"][0] if v["emails"] else ""), "commits": v["commits"]}
     for v in agg.values()),
    key=lambda x: x["commits"], reverse=True
)[:10]

# ---------- Normalisation des chemins (renames numstat) ----------
def normalize_path_from_numstat(p: str) -> str:
    p = p.replace("\\","/").strip()
    if " => " in p:
        p = re.sub(r"\{([^{}]*?)\s*=>\s*([^{}]*?)\}", r"\2", p)  # a/{old => new}/b.py
        p = p.split(" => ")[-1]                                   # old => new
    return p.lstrip("./")

# ---------- Numstat -> changements par fichier ----------
num = sh("git","log","--numstat","--pretty=format:")
changes = collections.Counter()
for line in num:
    parts = line.split("\t")
    if len(parts) == 3:
        add, rem, path = parts
        path = normalize_path_from_numstat(path)
        try:
            a = 0 if add == "-" else int(add)
            r = 0 if rem == "-" else int(rem)
        except ValueError:
            a, r = 0, 0
        changes[path] += a + r

# ---------- Filtres fichiers ----------
IGNORE_EXT = {
    ".pem",".crt",".cer",".der",".ai",".psd",".png",".jpg",".jpeg",".gif",".svg",".ico",".pdf",
    ".lock",".min.js",".map",".ttf",".otf",".woff",".woff2",".gz",".zip",".7z",".tar",".bz2",
    ".exe",".dll",".so",".dylib",
}
IGNORE_PREFIXES = [
    "requests/packages/",   # vendored historiques
    "ext/",                 # assets
    "docs/_build/", "docs/_static/", "docs/_themes/",
    ".git/", ".github/", ".gitlab/", "site-packages/", "dist-packages/",
    "node_modules/", "vendor/",
]
IGNORE_FILES = {"HISTORY.rst","HISTORY.md","CHANGELOG","CHANGELOG.md","README","README.md"}

def ignored(path: str) -> bool:
    p = normalize_path_from_numstat(path).lower()
    if any(p.startswith(pref) for pref in IGNORE_PREFIXES): return True
    if p.split("/")[-1] in {f.lower() for f in IGNORE_FILES}: return True
    if any(p.endswith(ext) for ext in IGNORE_EXT): return True
    return False

filtered = [(p,c) for p,c in changes.items() if not ignored(p)]
filtered.sort(key=lambda x: x[1], reverse=True)
hotspots_top10 = [{"path": p, "changes": c} for p,c in filtered[:10]]

# ---------- Stats par extension & top dossiers ----------
ext_files = collections.defaultdict(set)
ext_changes = collections.Counter()
dir_changes = collections.Counter()
for p, c in filtered:
    norm = normalize_path_from_numstat(p)
    topdir = norm.split("/",1)[0] if "/" in norm else "<root>"
    dir_changes[topdir] += c
    ext = pathlib.Path(norm).suffix.lower() or "<noext>"
    ext_files[ext].add(norm)
    ext_changes[ext] += c

by_ext = [{"ext": e, "files": len(fs), "changes": ext_changes[e]} for e, fs in ext_files.items()]
by_ext.sort(key=lambda x: x["changes"], reverse=True)
directories_top = [{"dir": d, "changes": ch} for d, ch in dir_changes.most_common(10)]

# ---------- Langage principal (heuristique ext) ----------
LANG_MAP = {".py":"python",".js":"javascript",".ts":"typescript",".java":"java",".go":"go",".rb":"ruby",".php":"php",".cs":"csharp",".cpp":"cpp",".c":"c"}
main_language = next((LANG_MAP.get(x["ext"], None) for x in by_ext if LANG_MAP.get(x["ext"])), "unknown")

# ---------- Activité récente (90 jours) ----------
recent = len(sh("git","log","--since=90.days","--pretty=format:%H"))

# ---------- KPIs ----------
years = max(1, (dt.date.fromisoformat(last).year - dt.date.fromisoformat(first).year) if (first and last) else 1)
avg_commits_per_year = round(commits / years, 1)
avg_changes_per_hotspot = round(sum(h["changes"] for h in hotspots_top10)/len(hotspots_top10), 1) if hotspots_top10 else 0

code_chg = sum(c for p,c in filtered if normalize_path_from_numstat(p).startswith(("requests/","src/")) and pathlib.Path(p).suffix==".py")
tests_chg = sum(c for p,c in filtered if normalize_path_from_numstat(p).startswith(("tests/","test/")))
docs_chg  = sum(c for p,c in filtered if normalize_path_from_numstat(p).startswith("docs/") or pathlib.Path(p).suffix in (".md",".rst",".adoc"))
total_chg = max(1, sum(c for _,c in filtered))
kpis = {
    "changes_ratio": {
        "code_py": round(100*code_chg/total_chg,1),
        "tests":   round(100*tests_chg/total_chg,1),
        "docs":    round(100*docs_chg/total_chg,1),
    },
    "py_changes_per_file_avg": round(
        (code_chg / max(1, next((x["files"] for x in by_ext if x["ext"]==".py"), 1))), 1
    ),
}

# ---------- CI & License (local) ----------
ci = "unknown"
wf = pathlib.Path(".github/workflows")
if wf.exists() and any(wf.iterdir()): ci = "github-actions"
elif pathlib.Path(".gitlab-ci.yml").exists(): ci = "gitlab-ci"
elif pathlib.Path("azure-pipelines.yml").exists(): ci = "azure-pipelines"

license_name = None
for cand in ["LICENSE","LICENSE.txt","LICENSE.md","COPYING","COPYING.txt"]:
    p = pathlib.Path(cand)
    if p.exists():
        head = p.read_text(errors="ignore")[:2000].lower()
        if "apache license" in head: license_name = "Apache-2.0"
        elif "mit license" in head:  license_name = "MIT"
        elif "bsd license" in head or "redistribution and use in source and binary forms" in head: license_name = "BSD-3-Clause"
        elif "gnu general public license" in head: license_name = "GPL"
        else: license_name = "UNKNOWN"
        break

# ---------- YAML ----------
yaml_obj = {
    "service": repo_name,
    "owner": {
        "team": "Open Source / PSF" if "requests" in repo_name.lower() else "Unknown",
        "contacts": [remote] if remote else [],
    },
    "repositories": [
        {
            "name": repo_name,
            "url": remote,
            "main_language": main_language,
            "default_branch": "main",
            "stars": None,                 # API si tu veux la vraie valeur
            "license": license_name,
        }
    ],
    "tech": {
        "runtime": "python3" if main_language=="python" else "unknown",
        "framework": "none",
        "ci": ci,
    },
    "git_summary": {
        "commits": commits,
        "first_commit": first,
        "last_commit": last,
        "contributors": contributors_count,
        "recent_commits_90d": recent,
        "hotspots_top10": hotspots_top10,
        "contributors_top10": contributors_top10,
        "by_extension": by_ext[:10],
        "directories_top": directories_top,
    },
    "metrics": {
        "evolution_years": years,
        "avg_commits_per_year": avg_commits_per_year,
        "avg_changes_per_hotspot": avg_changes_per_hotspot,
        "changes_ratio": kpis["changes_ratio"],
        "py_changes_per_file_avg": kpis["py_changes_per_file_avg"],
    },
    "notes": [
        "Hotspots calculés après filtrage des vendored/artefacts (prefixes & extensions).",
        "Contributeurs dédupliqués (noreply, variantes Gmail).",
        "Licence et CI détectées localement sans API distante.",
    ],
}

out_dir = pathlib.Path("data"); out_dir.mkdir(exist_ok=True)
out_file = out_dir / f"{repo_name}.yaml"
with open(out_file, "w", encoding="utf-8") as f:
    yaml.safe_dump(yaml_obj, f, allow_unicode=True, sort_keys=False)

print(f"✅ Fichier généré : {out_file}")
