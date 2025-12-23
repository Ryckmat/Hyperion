# 🗄️ Structure Neo4j Hyperion v1 + v2

**Auteur** : Ryckman Matthieu  
**Date** : 23 décembre 2024

---

## 📊 Vue d'ensemble

Hyperion utilise **la même base Neo4j** pour deux types de données complémentaires :

- **V1** : Statistiques Git agrégées (repos, contributeurs, hotspots)
- **V2** : Structure de code détaillée (fichiers, fonctions, dépendances)

Les deux coexistent **sans collision** grâce à des labels différents.

---

## 🏗️ Modèle v1 (Existant)

### Nodes

| Label | Propriétés | Description |
|-------|-----------|-------------|
| `:Repo` | name, url, commits, contributors, language | Repository principal |
| `:Contributor` | name, email, commits | Contributeur Git |
| `:Hotspot` | path, changes | Fichiers les plus modifiés |
| `:Directory` | dir, changes | Répertoires actifs |
| `:Extension` | ext, files, changes | Extensions de fichiers |

### Relations

```cypher
(:Repo)-[:HAS_CONTRIBUTOR]->(:Contributor)
(:Repo)-[:HAS_HOTSPOT]->(:Hotspot)
(:Repo)-[:HAS_DIRECTORY]->(:Directory)
(:Repo)-[:HAS_EXTENSION]->(:Extension)
```

### Exemple requête v1

```cypher
// Top contributeurs d'un repo
MATCH (r:Repo {name: "requests"})-[:HAS_CONTRIBUTOR]->(c:Contributor)
RETURN c.name, c.commits
ORDER BY c.commits DESC
LIMIT 10
```

---

## 🆕 Modèle v2 (Nouveau)

### Nodes

| Label | Propriétés | Description |
|-------|-----------|-------------|
| `:File` | path, repo, num_functions, num_classes | Fichier Python |
| `:Function` | id, name, args, returns, is_async | Fonction Python |
| `:Class` | id, name, bases, methods | Classe Python |

### Relations

```cypher
(:File)-[:CONTAINS]->(:Function)       # Fichier contient fonction
(:File)-[:CONTAINS]->(:Class)          # Fichier contient classe
(:File)-[:DEPENDS_ON]->(:File)         # Dépendance import
(:Function)-[:CALLS]->(:Function)      # Appel de fonction (TODO)
```

### Exemple requêtes v2

```cypher
// Fichiers avec le plus de fonctions
MATCH (f:File {repo: "requests"})
RETURN f.path, f.num_functions
ORDER BY f.num_functions DESC
LIMIT 10

// Dépendances d'un fichier
MATCH (f:File {path: "/tmp/requests/requests/api.py"})-[:DEPENDS_ON]->(dep:File)
RETURN dep.path

// Graphe de dépendances complet
MATCH path = (f:File {repo: "requests"})-[:DEPENDS_ON*1..3]->(dep:File)
RETURN path
LIMIT 100
```

---

## 🔄 Workflow Ingestion

### V1 : Stats Git

```bash
# Utilise le script existant
python -m hyperion.modules.integrations.neo4j_ingester \
  --profile data/repositories/requests/profile.yaml
```

**Résultat Neo4j** :
```
Created:
- 1 :Repo (requests)
- 10 :Contributor
- 10 :Hotspot
- 50 :Directory
- 5 :Extension
```

### V2 : Structure Code

```bash
# Nouveau script v2
python scripts/maintenance/ingest_generalized.py \
  --repo /tmp/requests \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-user neo4j \
  --neo4j-password password
```

**Résultat Neo4j** :
```
Created:
- 156 :File
- 342 :Function
- 89 :Class
- 234 :DEPENDS_ON relations
- 431 :CONTAINS relations
```

---

## 📈 Statistiques combinées

### Requête mixte v1 + v2

```cypher
// Hotspots v1 vs Complexité v2
MATCH (r:Repo {name: "requests"})-[:HAS_HOTSPOT]->(h:Hotspot)
MATCH (f:File {path: h.path})
RETURN h.path, h.changes AS git_changes, f.num_functions AS complexity
ORDER BY h.changes DESC
LIMIT 10
```

### Dashboard combiné

```cypher
// Vue globale repo
MATCH (r:Repo {name: "requests"})
OPTIONAL MATCH (r)-[:HAS_CONTRIBUTOR]->(c:Contributor)
OPTIONAL MATCH (f:File {repo: "requests"})
OPTIONAL MATCH (f)-[:CONTAINS]->(fn:Function)
RETURN 
  r.name AS repo,
  r.commits AS total_commits,
  count(DISTINCT c) AS contributors,
  count(DISTINCT f) AS files,
  count(DISTINCT fn) AS functions
```

---

## 🔧 Configuration Neo4j

### Contraintes v1 (existantes)

```cypher
CREATE CONSTRAINT repo_name IF NOT EXISTS 
FOR (r:Repo) REQUIRE r.name IS UNIQUE;

CREATE CONSTRAINT contributor_id IF NOT EXISTS 
FOR (c:Contributor) REQUIRE c.id IS UNIQUE;
```

### Contraintes v2 (nouvelles)

```cypher
CREATE CONSTRAINT file_path IF NOT EXISTS 
FOR (f:File) REQUIRE f.path IS UNIQUE;

CREATE CONSTRAINT function_id IF NOT EXISTS 
FOR (fn:Function) REQUIRE fn.id IS UNIQUE;

CREATE CONSTRAINT class_id IF NOT EXISTS 
FOR (c:Class) REQUIRE c.id IS UNIQUE;
```

### Index performance

```cypher
// V1
CREATE INDEX hotspot_changes IF NOT EXISTS 
FOR (h:Hotspot) ON (h.changes);

// V2
CREATE INDEX file_repo IF NOT EXISTS 
FOR (f:File) ON (f.repo);

CREATE INDEX function_name IF NOT EXISTS 
FOR (fn:Function) ON (fn.name);
```

---

## 🎯 Cas d'usage

### 1. Impact Analysis (v2)

```cypher
// Fichiers impactés par une modification
MATCH (modified:File {path: $file_path})
MATCH (modified)<-[:DEPENDS_ON*1..5]-(impacted:File)
RETURN DISTINCT impacted.path, length(path) AS depth
ORDER BY depth
```

### 2. Hotspots + Complexité (v1 + v2)

```cypher
// Fichiers chauds ET complexes (risque élevé)
MATCH (r:Repo {name: "requests"})-[:HAS_HOTSPOT]->(h:Hotspot)
MATCH (f:File {path: h.path})
WHERE h.changes > 50 AND f.num_functions > 10
RETURN h.path, h.changes, f.num_functions
ORDER BY h.changes DESC
```

### 3. Onboarding (v2)

```cypher
// Fichiers essentiels à comprendre
MATCH (f:File {repo: "requests"})
MATCH (f)-[:CONTAINS]->(fn:Function)
WITH f, count(fn) AS complexity
ORDER BY complexity DESC
LIMIT 10
RETURN f.path, complexity
```

---

## 🔍 Vérification

### Stats v1

```cypher
MATCH (r:Repo) RETURN count(r) AS repos;
MATCH (c:Contributor) RETURN count(c) AS contributors;
MATCH (h:Hotspot) RETURN count(h) AS hotspots;
```

### Stats v2

```cypher
MATCH (f:File) RETURN count(f) AS files;
MATCH (fn:Function) RETURN count(fn) AS functions;
MATCH (c:Class) RETURN count(c) AS classes;
MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS dependencies;
```

### Vue complète

```cypher
// Tous les labels
CALL db.labels() YIELD label
RETURN label
ORDER BY label;

// Résultat attendu:
// - Class
// - Contributor  
// - Directory
// - Extension
// - File
// - Function
// - Hotspot
// - Repo
```

---

## ✅ Avantages de la coexistence

1. **Complémentarité** : Stats Git (v1) + Structure code (v2)
2. **Requêtes croisées** : Mixer les deux modèles
3. **Pas de migration** : V1 continue de fonctionner
4. **Une seule base** : Simplicité opérationnelle
5. **Performance** : Index séparés par label

---

## 🚀 Prochaines étapes

- [ ] Ajouter relations `:CALLS` entre fonctions
- [ ] Indexer docstrings dans Qdrant
- [ ] Dashboard Neo4j Browser avec requêtes mixtes
- [ ] API GraphQL sur Neo4j
- [ ] Visualisation D3.js du graphe complet

---

**Tout est prêt pour l'ingestion v2 !** 🎉
