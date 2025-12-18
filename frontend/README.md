# 🌐 Hyperion Dashboard

Interface web moderne pour explorer les dépôts Git analysés par Hyperion.

---

## 🚀 Démarrage rapide

### Prérequis
```bash
pip install fastapi uvicorn --break-system-packages
```

### Lancer le dashboard complet (API + Frontend)
```bash
cd /home/kortazo/Documents/Hyperion
python3 scripts/run_dashboard.py
```

**Dashboard** : http://localhost:3000  
**API** : http://localhost:8000  
**API Docs** : http://localhost:8000/docs

Le navigateur s'ouvre automatiquement ! 🎉

---

## 📊 Features

### Vue d'ensemble
- 📚 Liste de tous les repos analysés
- 🏷️ Langage, commits, contributeurs
- 📅 Période d'activité (première → dernière date)
- ⚖️ Licence détectée

### Détails repo
- 📊 **Stats principales** : Commits, contributeurs, activité récente, années
- 📈 **Métriques qualité** : Ratio code/tests/docs, commits/an
- 👥 **Top 10 contributeurs** : Nom, email, nombre de commits
- 🔥 **Top 10 hotspots** : Fichiers les plus modifiés

---

## 🎨 Stack technique

### Frontend
- **React 18** (standalone, sans build)
- **Tailwind CSS** (CDN)
- **Vanilla JS** (pas de bundler)

### Backend
- **FastAPI** (API REST)
- **Uvicorn** (serveur ASGI)

### Données
- **YAML** (profils analysés)
- **Neo4j** (graphe optionnel)

---

## 📁 Structure

```
frontend/
└── index.html    # Application React complète (single file)
```

**Avantages** :
- ✅ Pas de build nécessaire
- ✅ Pas de node_modules
- ✅ Démarrage instantané
- ✅ Facile à modifier

---

## 🔧 Développement

### Lancer séparément

#### API seule
```bash
python3 scripts/run_api.py
# → http://localhost:8000
```

#### Frontend seul
```bash
cd frontend
python3 -m http.server 3000
# → http://localhost:3000
```

---

## 🎯 Utilisation

### 1. Analyser un repo
```bash
python3 scripts/hyperion_full_workflow.py /path/to/repo
```

### 2. Lancer le dashboard
```bash
python3 scripts/run_dashboard.py
```

### 3. Explorer !
- Clique sur un repo pour voir les détails
- Explore contributeurs, hotspots, métriques
- Bouton "Retour" pour revenir à la liste

---

## 🌈 Personnalisation

Le dashboard est dans un seul fichier HTML/JS/CSS : `frontend/index.html`

Tu peux facilement :
- Changer les couleurs (Tailwind classes)
- Ajouter des graphiques (Chart.js déjà inclus)
- Modifier le layout
- Ajouter de nouveaux endpoints

---

## 🚧 Prochaines améliorations

- [ ] Graphiques interactifs (Chart.js)
- [ ] Filtres et recherche
- [ ] Comparaison de repos
- [ ] Graphe Neo4j interactif
- [ ] Export PDF des rapports
- [ ] Dark mode

---

## 💡 Note

Le dashboard utilise **React en mode standalone** (sans npm/webpack/vite) pour :
- Simplicité maximale
- Pas de dépendances Node
- Démarrage instantané
- Facile à comprendre et modifier

Pour un dashboard production, on pourrait migrer vers Vite + TypeScript.

---

🎉 **Dashboard prêt à l'emploi !**
