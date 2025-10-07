#!/usr/bin/env python3
import json, yaml, datetime as dt, pathlib

# --- 1. Charger les données JSON
summary = json.loads(open("git_summary.json", "rb").read().decode("utf-8-sig"))

# --- 2. Nettoyage / filtres
filtered_hotspots = [
    h for h in summary.get("hotspots_top10", [])
    if not h["path"].endswith((".pem", ".ai", ".lock"))
]

# --- 3. Calculs complémentaires
first = dt.datetime.strptime(summary["first_commit"][:10], "%Y-%m-%d")
last = dt.datetime.strptime(summary["last_commit"][:10], "%Y-%m-%d")
years = max(1, (last.year - first.year))
avg_per_year = round(summary["commits"] / years, 1)
avg_changes_hotspot = (
    round(sum(h["changes"] for h in filtered_hotspots) / len(filtered_hotspots), 1)
    if filtered_hotspots else 0
)

# --- 4. Construction du dictionnaire YAML
hyperion_yaml = {
    "service": "requests",
    "owner": {
        "team": "Open Source / PSF",
        "contacts": ["https://github.com/psf/requests"],
    },
    "repositories": [
        {
            "name": "requests",
            "url": "https://github.com/psf/requests",
            "main_language": "python",
            "default_branch": "main",
            "stars": 52000,
            "license": "Apache-2.0",
        }
    ],
    "tech": {
        "runtime": "python3",
        "framework": "none",
        "ci": "github-actions",
    },
    "git_summary": {
        "commits": summary["commits"],
        "first_commit": summary["first_commit"][:10],
        "last_commit": summary["last_commit"][:10],
        "contributors": summary["contributors"],
        "hotspots_top10": filtered_hotspots,
    },
    "metrics": {
        "evolution_years": years,
        "avg_commits_per_year": avg_per_year,
        "avg_changes_per_hotspot": avg_changes_hotspot,
    },
    "notes": [
        "Certains fichiers binaires (.pem, .ai) ont été ignorés car non pertinents pour l’analyse du code.",
        "requests/models.py, sessions.py et adapters.py concentrent la majorité de l’activité.",
    ],
}

# --- 5. Sauvegarde dans data/
out_dir = pathlib.Path("data")
out_dir.mkdir(exist_ok=True)
out_file = out_dir / "requests.yaml"
with open(out_file, "w", encoding="utf-8") as f:
    yaml.dump(hyperion_yaml, f, allow_unicode=True, sort_keys=False)

print(f"✅ Fichier généré : {out_file}")
