---
title: "Registre technique — {{ service }}"
description: "Vue détaillée du dépôt {{ service }}"
tags: ["registre", "hyperion", "{{ service }}"]
---

# Registre technique — {{ service }}

## 📦 Dépôt
- **URL :** [{{ repositories[0].url }}]({{ repositories[0].url }})
- **Branche par défaut :** {{ repositories[0].default_branch }}
- **Langage :** {{ repositories[0].main_language }}
- **Licence :** {{ repositories[0].license }}
- **CI :** {{ tech.ci }}

---

## 🔍 Extensions dominantes
| Extension | Fichiers | Changements |
|------------|-----------|-------------|
{% for e in git_summary.by_extension %}
| {{ e.ext }} | {{ e.files }} | {{ e.changes }} |
{% endfor %}

---

## 🔥 Hotspots
| Fichier | Changements |
|----------|-------------|
{% for h in git_summary.hotspots_top10 %}
| {{ h.path }} | {{ h.changes }} |
{% endfor %}

---

## 👥 Contributeurs principaux
| Nom | Email | Commits |
|------|--------|----------|
{% for c in git_summary.contributors_top10 %}
| {{ c.name }} | {{ c.email }} | {{ c.commits }} |
{% endfor %}

---

## 🧩 KPIs
| Indicateur | Valeur |
|-------------|--------|
| Évolution (années) | {{ metrics.evolution_years }} |
| Commits/an | {{ metrics.avg_commits_per_year }} |
| Moy. changements/hotspot | {{ metrics.avg_changes_per_hotspot }} |
| Densité changements/fichier .py | {{ metrics.py_changes_per_file_avg }} |
| Ratio code/tests/docs | {{ metrics.changes_ratio.code_py }} % / {{ metrics.changes_ratio.tests }} % / {{ metrics.changes_ratio.docs }} % |

---

> *Données extraites localement. Sources : Git history, fichiers et métadonnées.*
