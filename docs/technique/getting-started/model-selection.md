# 🎯 Guide de Sélection des Modèles LLM - Hyperion v2.5.0

## 📋 Vue d'Ensemble

Hyperion est une **plateforme d'intelligence locale pour repositories Git** qui utilise le RAG (Retrieval Augmented Generation) pour analyser et comprendre le code. Le choix du modèle LLM impacte directement les performances et l'expérience utilisateur.

## 🚀 Recommandations par Profil d'Usage

### 1. 🏃‍♂️ **Performance Ultra-Rapide** (Réponses <3s garanties)
```env
OLLAMA_MODEL=llama3.2:1b
LLM_MAX_TOKENS=128
LLM_TEMPERATURE=0.0
LLM_TIMEOUT=2
```

**Profils utilisateurs:**
- Développeurs en exploration rapide de code
- Sessions interactives courtes
- Environnements avec contraintes de ressources
- Démonstrations et POCs

**Avantages:**
- ⚡ **Ultra-rapide**: ~2-4 secondes par réponse
- 💾 **Léger**: ~1.3GB de mémoire
- 🔋 **Efficace**: Fonctionne sur laptops standard

**Limitations:**
- 📝 Réponses plus concises
- 🧠 Compréhension limitée des contextes complexes
- 🔍 Analyse technique de surface

---

### 2. ⚖️ **Équilibre Performance/Qualité** (Réponses 5-10s)
```env
OLLAMA_MODEL=llama3.1:8b
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.1
LLM_TIMEOUT=10
```

**Profils utilisateurs:**
- Développeurs seniors analysant du code
- Code reviews et audits de qualité
- Recherche de patterns et bonnes pratiques
- Usage quotidien en équipe

**Avantages:**
- 🎯 **Bon compromis**: Performance acceptable + qualité
- 📊 **Analyse décente**: Comprend les métriques Git
- 🔍 **Contexte élargi**: Meilleure compréhension des relations

**Cas d'usage optimaux:**
- Questions sur les contributeurs principaux
- Analyse des hotspots et technical debt
- Comparaisons entre repositories
- Onboarding de nouveaux développeurs

---

### 3. 🧠 **Qualité Premium** (Réponses 10-30s)
```env
OLLAMA_MODEL=qwen2.5:14b
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.1
LLM_TIMEOUT=30
```

**Profils utilisateurs:**
- Architectes techniques et tech leads
- Analyses approfondies de codebase
- Prédiction de risques et impact analysis
- Documentation technique détaillée

**Avantages:**
- 🎓 **Intelligence avancée**: Compréhension nuancée
- 📈 **Analyses complexes**: Corrélations et patterns
- 📚 **Réponses détaillées**: Explications complètes
- 🔗 **Contextualisation**: Liens entre concepts

**Cas d'usage optimaux:**
- Analyse d'architecture et design patterns
- Évaluation de risques techniques
- Planification de refactoring
- Documentation automatique

---

### 4. 🚀 **Expert/Recherche** (Réponses 30s+)
```env
OLLAMA_MODEL=qwen2.5:32b
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.2
LLM_TIMEOUT=60
```

**Profils utilisateurs:**
- Chercheurs en génie logiciel
- Audits de sécurité approfondis
- Analyses de conformité enterprise
- Recherche et développement

**Avantages:**
- 🏆 **Excellence technique**: Analyses de niveau expert
- 🔬 **Recherche approfondie**: Détection de patterns subtils
- 📋 **Rapports détaillés**: Documentation complète
- 🛡️ **Sécurité**: Identification de vulnérabilités

**Cas d'usage optimaux:**
- Audits de sécurité et compliance
- Recherche en qualité logicielle
- Analyses prédictives avancées
- Formation et enseignement

---

## 🔧 Configuration Dynamique

### Script de Configuration Automatique

```bash
#!/bin/bash
# hyperion-model-setup.sh

echo "🎯 Configuration du modèle LLM pour Hyperion"
echo "Sélectionnez votre profil d'usage:"
echo ""
echo "1) 🏃‍♂️ Performance Ultra-Rapide (<3s)"
echo "2) ⚖️ Équilibre Performance/Qualité (5-10s)"
echo "3) 🧠 Qualité Premium (10-30s)"
echo "4) 🚀 Expert/Recherche (30s+)"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
    1)
        MODEL="llama3.2:1b"
        TOKENS="128"
        TEMP="0.0"
        TIMEOUT="2"
        echo "✅ Configuration: Performance Ultra-Rapide"
        ;;
    2)
        MODEL="llama3.1:8b"
        TOKENS="512"
        TEMP="0.1"
        TIMEOUT="10"
        echo "✅ Configuration: Équilibre Performance/Qualité"
        ;;
    3)
        MODEL="qwen2.5:14b"
        TOKENS="1024"
        TEMP="0.1"
        TIMEOUT="30"
        echo "✅ Configuration: Qualité Premium"
        ;;
    4)
        MODEL="qwen2.5:32b"
        TOKENS="2048"
        TEMP="0.2"
        TIMEOUT="60"
        echo "✅ Configuration: Expert/Recherche"
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

# Télécharger le modèle
echo "📥 Téléchargement du modèle $MODEL..."
ollama pull $MODEL

# Mettre à jour la configuration
echo "📝 Mise à jour de la configuration..."
sed -i "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL/" src/hyperion/modules/rag/config.py
sed -i "s/LLM_MAX_TOKENS=.*/LLM_MAX_TOKENS=$TOKENS/" src/hyperion/modules/rag/config.py
sed -i "s/LLM_TEMPERATURE=.*/LLM_TEMPERATURE=$TEMP/" src/hyperion/modules/rag/config.py
sed -i "s/LLM_TIMEOUT=.*/LLM_TIMEOUT=$TIMEOUT/" src/hyperion/modules/rag/config.py

echo "🎉 Configuration terminée! Redémarrez l'API Hyperion."
```

---

## 📊 Benchmark des Performances

| Modèle | Taille | Temps Réponse | Qualité | RAM Requise | GPU Recommandé |
|--------|--------|---------------|---------|-------------|----------------|
| **llama3.2:1b** | 1.3GB | 2-4s | ⭐⭐⭐ | 4GB | Non |
| **llama3.1:8b** | 4.7GB | 5-10s | ⭐⭐⭐⭐ | 8GB | RTX 4060+ |
| **qwen2.5:14b** | 8.7GB | 10-30s | ⭐⭐⭐⭐⭐ | 16GB | RTX 4070+ |
| **qwen2.5:32b** | 19GB | 30s+ | ⭐⭐⭐⭐⭐ | 32GB | RTX 4090+ |

---

## 🎯 Recommandations par Contexte

### 🏢 **Entreprise/Production**
- **Standard**: `llama3.1:8b` (équilibre optimal)
- **Mission critique**: `qwen2.5:14b` (qualité premium)

### 👨‍💻 **Développement/Debug**
- **Exploration rapide**: `llama3.2:1b`
- **Analyse approfondie**: `llama3.1:8b`

### 🎓 **Recherche/Formation**
- **Études de cas**: `qwen2.5:14b`
- **Publications scientifiques**: `qwen2.5:32b`

### 🚀 **Démonstration/POC**
- **Démos rapides**: `llama3.2:1b`
- **Présentations détaillées**: `llama3.1:8b`

---

## 🔄 Migration entre Modèles

### Changement de Modèle en Live

```bash
# 1. Télécharger le nouveau modèle
ollama pull llama3.1:8b

# 2. Modifier la configuration
export OLLAMA_MODEL="llama3.1:8b"

# 3. Redémarrer l'API (sans perdre les données)
pkill -f "hyperion.api.main"
python -m hyperion.api.main &

# 4. Vérifier le changement
curl -s http://localhost:8000/api/health | jq '.rag'
```

---

## 📈 Optimisations Avancées

### GPU Acceleration
```env
EMBEDDING_DEVICE=cuda  # Active GPU pour embeddings
CUDA_VISIBLE_DEVICES=0  # Spécifie GPU à utiliser
```

### Cache Optimizations
```env
QDRANT_CACHE_SIZE=1000  # Cache des requêtes fréquentes
LLM_CACHE_ENABLED=true  # Cache des réponses LLM
```

### Batch Processing
```env
RAG_BATCH_SIZE=5       # Traitement par lots
EMBEDDING_BATCH_SIZE=32  # Embeddings par lots
```

---

## 🎉 Conclusion

Le choix du modèle LLM pour Hyperion dépend de vos priorités:

- **Vitesse**: `llama3.2:1b` pour l'exploration rapide
- **Équilibre**: `llama3.1:8b` pour l'usage quotidien
- **Qualité**: `qwen2.5:14b` pour l'analyse approfondie
- **Excellence**: `qwen2.5:32b` pour la recherche

**Recommandation générale**: Commencer avec `llama3.1:8b` et ajuster selon vos besoins spécifiques.