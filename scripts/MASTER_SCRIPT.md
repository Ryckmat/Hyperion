# 🚀 Script Master Hyperion

## 📦 `hyperion_full_workflow.py`

**Script complet qui fait TOUT** : Analyse Git → Profil YAML → Ingestion Neo4j

---

## 🎯 Usage

### Analyse simple
```bash
cd /home/kortazo/Documents/Hyperion

# Analyser le repo requests
python3 scripts/hyperion_full_workflow.py /home/kortazo/Documents/requests
```

### Avec options
```bash
# Nettoyer les données existantes avant ingestion
python3 scripts/hyperion_full_workflow.py /home/kortazo/Documents/requests --clear

# Skip l'ingestion Neo4j (juste analyse + YAML)
python3 scripts/hyperion_full_workflow.py /home/kortazo/Documents/requests --skip-neo4j
```

---

## 📊 Ce que fait le script

### ÉTAPE 1 : Analyse Git (30-60 sec)
- Clone le repo ou utilise un repo local
- Analyse commits, contributeurs, hotspots
- Calcule métriques qualité
- Déduplique contributeurs
- Filtre hotspots (ignore binaires, vendored, etc.)

### ÉTAPE 2 : Sauvegarde Profil
- Génère `data/repositories/{repo}/profile.yaml`
- Génère `data/repositories/{repo}/profile.json` (debug)

### ÉTAPE 3 : Ingestion Neo4j
- Crée contraintes et index
- Ingère Repository, Contributors, Hotspots
- Ingère Directories, Extensions, Metrics
- Vérifie que tout est bien ingéré

---

## 🗄️ Modèle Neo4j créé

```cypher
(:Repo {
  name, url, language, license, ci, runtime,
  commits, contributors, first_commit, last_commit,
  evolution_years, avg_commits_per_year,
  ratio_code, ratio_tests, ratio_docs
})

(:Contributor {id, name, email, commits})
(:Hotspot {path, changes, repo})
(:Directory {name, dir, changes, repo})
(:Extension {name, ext, files, changes, repo})

# Relations
(Repo)-[:HAS_CONTRIBUTOR {commits}]->(Contributor)
(Repo)-[:HAS_HOTSPOT {changes}]->(Hotspot)
(Repo)-[:HAS_DIRECTORY {changes}]->(Directory)
(Repo)-[:HAS_EXTENSION {files, changes}]->(Extension)
```

---

## 📋 Exemples de requêtes Neo4j

### Voir le repo
```cypher
MATCH (r:Repo {name: 'requests'})
RETURN r
```

### Top contributeurs
```cypher
MATCH (r:Repo {name: 'requests'})-[rel:HAS_CONTRIBUTOR]->(c:Contributor)
RETURN c.name, c.commits
ORDER BY c.commits DESC
LIMIT 10
```

### Top hotspots
```cypher
MATCH (r:Repo {name: 'requests'})-[rel:HAS_HOTSPOT]->(h:Hotspot)
RETURN h.path, h.changes
ORDER BY h.changes DESC
LIMIT 10
```

### Stats par extension
```cypher
MATCH (r:Repo {name: 'requests'})-[rel:HAS_EXTENSION]->(e:Extension)
RETURN e.ext, e.files, e.changes
ORDER BY e.changes DESC
```

### Graphe complet
```cypher
MATCH (r:Repo {name: 'requests'})-[rel]->(n)
RETURN r, rel, n
LIMIT 100
```

---

## 🎯 Exemple complet : Analyser requests

```bash
cd /home/kortazo/Documents/Hyperion

# 1. Lancer le workflow complet
python3 scripts/hyperion_full_workflow.py /home/kortazo/Documents/requests

# Output attendu :
# ================================================================================
# 🚀 HYPERION FULL WORKFLOW
# ================================================================================
# 
# 📁 Repository : /home/kortazo/Documents/requests
# 
# ================================================================================
# 📊 ÉTAPE 1/3 : ANALYSE GIT
# ================================================================================
# 
# ⏳ Analyse en cours de requests...
#    (Cela peut prendre 30-60 secondes selon la taille du repo)
# 
# ✅ Analyse terminée !
#    • Repo          : requests
#    • Commits       : 6,377
#    • Contributeurs : 805
#    • Hotspots      : 10
#    • Langage       : python
#    • Licence       : Apache-2.0
# 
# ================================================================================
# 💾 ÉTAPE 2/3 : SAUVEGARDE PROFIL
# ================================================================================
# 
# ✅ Profil YAML : data/repositories/requests/profile.yaml
# ✅ Profil JSON : data/repositories/requests/profile.json
# 
# ================================================================================
# 🗄️  ÉTAPE 3/3 : INGESTION NEO4J
# ================================================================================
# 
# ⏳ Connexion à Neo4j...
# ✅ Connexion établie !
# 
# ⏳ Ingestion du profil dans Neo4j...
# 
# ✅ Ingestion terminée !
#    • Repo créé     : 1
#    • Contributeurs : 10
#    • Hotspots      : 10
#    • Répertoires   : 10
#    • Extensions    : 10
#    • Métriques     : 1
# 
# 🔍 Vérification dans Neo4j...
# ✅ Repo trouvé dans Neo4j :
#    • Nom           : requests
#    • Commits       : 6,377
#    • Contributeurs : 10
#    • Hotspots      : 10
#    • Répertoires   : 10
#    • Extensions    : 10
# 
# ================================================================================
# 🎉 WORKFLOW TERMINÉ AVEC SUCCÈS !
# ================================================================================
# 
# 📊 RÉSUMÉ :
#    • Repository    : requests
#    • Commits       : 6,377
#    • Contributeurs : 805
#    • Période       : 2011-02-13 → 2024-12-18
#    • Langage       : python
#    • Profil YAML   : data/repositories/requests/profile.yaml
#    • Neo4j         : ✅ Ingéré
# 
# 🌐 Ouvre Neo4j Browser : http://localhost:7474
#    Query exemple : MATCH (r:Repo {name: 'requests'}) RETURN r
# 
# ================================================================================
```

---

## 🔧 Options du script

| Option | Description |
|--------|-------------|
| `--clear` | Nettoie les données existantes du repo dans Neo4j avant ingestion |
| `--skip-neo4j` | Skip l'ingestion Neo4j (juste analyse + YAML) |

---

## 🎉 C'est tout !

**Un seul script fait tout le workflow Hyperion !**

Lance-le et regarde la magie opérer ! 🚀
