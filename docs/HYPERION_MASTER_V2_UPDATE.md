# 🚀 Mise à jour Hyperion Master v2

**Auteur** : Ryckman Matthieu  
**Date** : 23 décembre 2024

## ✅ Modifications apportées

Le script `hyperion_master.sh` a été mis à jour avec la **nouvelle ingestion v2**.

### Nouvelle fonctionnalité

**Ingestion v2 multi-sources** :
- Analyse repository Git
- Indexation documentation
- Analyse code (AST)
- Intégration Qdrant + Neo4j

### Nouveau menu

```
🚀 HYPERION MASTER V2 - Contrôle complet

Vérifier et démarrer les services ? (o/n): 
Ingérer v2 (Git + Docs + Code) ? (o/n):  ← NOUVEAU
Générer documentation ? (o/n): 
Lancer dashboard React ? (o/n): 
Lancer Open WebUI (chat) ? (o/n): 
```

## 📥 Installation

Le script mis à jour est disponible dans `/tmp/hyperion_master_v2.sh`.

Pour l'installer manuellement :

```bash
cd /home/kortazo/Documents/Hyperion

# Backup ancien script
cp scripts/deploy/hyperion_master.sh scripts/deploy/hyperion_master.sh.backup

# Copier nouveau script
cp /tmp/hyperion_master_v2.sh scripts/deploy/hyperion_master.sh

# Rendre exécutable
chmod +x scripts/deploy/hyperion_master.sh
```

## 🎯 Utilisation

```bash
cd /home/kortazo/Documents/Hyperion
./scripts/deploy/hyperion_master.sh
```

Workflow recommandé :
1. **Vérifier services** : o
2. **Ingérer v2** : o
   - Chemin : `/tmp/requests`
   - Docs : o
3. **Dashboard** : o
4. **Open WebUI** : o

## 📊 Ce que fait l'ingestion v2

Quand tu réponds "o" à "Ingérer v2" :
1. Le script demande le chemin du repo (ex: `/tmp/requests`)
2. Demande si tu veux inclure la documentation
3. Lance : `python3 scripts/maintenance/ingest_generalized.py --repo /tmp/requests --docs /tmp/requests/docs`
4. Affiche les stats :
   ```
   📦 Ingestion Git: /tmp/requests
   💻 Ingestion Code Analysis: /tmp/requests
   📚 Ingestion Documentation: /tmp/requests/docs
   
   ✅ Ingestion terminée
   📊 Stats: {"git": 1247, "docs": 23, "code": 156}
   ```

## 🔧 Fonction ajoutée

```bash
run_ingestion_v2() {
  # Demande repo à analyser
  # Options : docs oui/non
  # Lance scripts/maintenance/ingest_generalized.py
  # Affiche stats
}
```

## ✅ Commit

```bash
git add scripts/deploy/hyperion_master.sh
git commit -m "feat(deploy): ajout ingestion v2 dans orchestrateur

- Nouveau menu 'Ingérer v2 (Git + Docs + Code)'
- Appelle scripts/maintenance/ingest_generalized.py
- Workflow interactif avec confirmation
- Stats d'ingestion affichées
"
```

---

**Note** : Le nouveau script est dans `/tmp/hyperion_master_v2.sh` et est prêt à être copié !
