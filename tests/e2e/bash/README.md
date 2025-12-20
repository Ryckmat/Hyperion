# Tests End-to-End Hyperion

Suite complète de tests automatisés pour valider le fonctionnement d'Hyperion.

## 📋 Vue d'ensemble

Les tests E2E valident l'ensemble de la stack Hyperion :
- ✅ Santé des services (API, Qdrant, Ollama, Neo4j, OpenWebUI)
- ✅ Ingestion RAG (Git → Chunks → Embeddings → Qdrant)
- ✅ Requêtes RAG (Question → Retrieval → LLM → Réponse)
- ✅ Ingestion Neo4j (Création graphe de connaissance)
- ✅ Function OpenWebUI (Intégration chat)
- ✅ Performance (Benchmarks temps réponse)

## 🚀 Utilisation

### Méthode recommandée : Script Master

Le script master prépare automatiquement l'environnement :

```bash
cd tests/e2e/bash
./run_tests_master.sh
```

Ce script va :
1. Vérifier que Qdrant et Ollama sont lancés
2. Démarrer l'API Hyperion automatiquement
3. Vérifier/proposer l'ingestion de données test
4. Lancer tous les tests E2E
5. Proposer le nettoyage à la fin

### Méthode manuelle : Tests uniquement

Si l'environnement est déjà prêt :

```bash
cd tests/e2e/bash
./test_e2e_complete.sh
```

### Lancer un test spécifique

```bash
# Test santé services
./test_services_health.sh

# Test ingestion RAG
./test_rag_ingestion.sh

# Test requêtes RAG
./test_rag_query.sh

# Test Neo4j
./test_neo4j_ingestion.sh

# Test OpenWebUI
./test_openwebui_function.sh

# Test performance
./test_performance.sh
```

## 📊 Critères de succès

### Services
- API FastAPI : `http://localhost:8000/health` accessible
- Qdrant : `http://localhost:6333` accessible
- Ollama : `http://localhost:11434` accessible avec modèles
- Neo4j : `http://localhost:7474` accessible (optionnel)
- OpenWebUI : `http://localhost:3000` accessible

### Ingestion RAG
- Chunks extraits > 0
- Points ajoutés dans Qdrant > 0
- Temps ingestion < 60s pour petit repo

### Requêtes RAG
- Réponses générées pour toutes les questions
- Sources retournées > 0
- Temps réponse moyen < 5s

### Performance (SLO)
- **p95 < 10s** : 95% des requêtes en moins de 10 secondes (tolérance cold start)
- **p95 < 15s** : Acceptable avec cold start initial
- **Taux succès > 95%** : moins de 5% d'échecs
- **Moyenne < 8s** : Temps moyen sur toutes requêtes

## 🛠️ Pré-requis

1. **Services lancés** :
   ```bash
   # Avec docker-compose
   docker-compose up -d
   
   # Ou avec script master
   ./hyperion_master.sh
   ```

2. **Dépendances Python** :
   ```bash
   source venv/bin/activate.fish
   pip install -r requirements.txt
   ```

3. **Modèle Ollama** :
   ```bash
   ollama pull qwen2.5:32b
   ```

## 📁 Structure

```
tests/e2e/bash/
├── run_tests_master.sh           # 🎖️ Script master (RECOMMANDÉ)
├── test_e2e_complete.sh          # Orchestrateur tests
├── test_services_health.sh       # Test santé services
├── test_rag_ingestion.sh         # Test ingestion RAG
├── test_rag_query.sh             # Test requêtes RAG
├── test_neo4j_ingestion.sh       # Test Neo4j
├── test_openwebui_function.sh    # Test OpenWebUI
├── test_performance.sh           # Benchmarks
├── utils/
│   ├── common.sh                 # Fonctions utilitaires
│   └── colors.sh                 # Affichage coloré
└── README.md                     # Ce fichier
```

## 🔍 Troubleshooting

### Problème : Services non accessibles
```bash
# Vérifier Docker
docker ps

# Vérifier logs
docker logs hyperion-api
docker logs qdrant
docker logs open-webui

# Redémarrer services
docker-compose restart
```

### Problème : Timeout requêtes RAG
```bash
# Vérifier Ollama
ollama list
systemctl status ollama

# Tester manuellement
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:32b",
  "prompt": "Hello"
}'
```

### Problème : Ingestion échoue
```bash
# Vérifier Qdrant
curl http://localhost:6333/collections

# Vérifier logs API
docker logs hyperion-api

# Vérifier espace disque
df -h
```

## 📈 Résultats attendus

```
╔════════════════════════════════════════════════════════════════╗
║ 🧪 HYPERION - Tests End-to-End
╚════════════════════════════════════════════════════════════════╝

▶ Test: Santé Services
✅ Santé Services - PASSED

▶ Test: Ingestion RAG
✅ Ingestion RAG - PASSED

▶ Test: Requêtes RAG
✅ Requêtes RAG - PASSED

▶ Test: Ingestion Neo4j
✅ Ingestion Neo4j - PASSED

▶ Test: OpenWebUI Function
✅ OpenWebUI Function - PASSED

▶ Test: Performance
✅ Performance - PASSED

╔════════════════════════════════════════════════════════════════╗
║ 📊 RÉSULTATS TESTS E2E
╚════════════════════════════════════════════════════════════════╝

Total tests    : 6
✅ Réussis     : 6
❌ Échoués     : 0

🎉 TOUS LES TESTS SONT PASSÉS !
```

## 🔗 Liens utiles

- Dashboard : http://localhost:3000
- API Docs : http://localhost:8000/docs
- Qdrant UI : http://localhost:6333/dashboard
- Neo4j Browser : http://localhost:7474
