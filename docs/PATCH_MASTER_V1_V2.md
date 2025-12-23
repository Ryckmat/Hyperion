# 🔧 PATCH : Ajouter ingestion V1 au script master

**Fichier** : `scripts/deploy/hyperion_master.sh`

---

## 1️⃣ Ajouter la fonction `run_ingestion_v1()`

**Position** : Juste AVANT la fonction `run_ingestion_v2()` (ligne ~248)

```bash
# ----------------------------------------------------------------------------
# Ingestion v1 (profils Git)  
# ----------------------------------------------------------------------------
run_ingestion_v1() {
  section "📥 INGESTION V1 - Profils Git (Stats agrégées)"
  
  echo ""
  echo -e "${CYAN}Profil YAML à ingérer :${NC}"
  echo -e "${YELLOW}   Format: data/repositories/<nom>/profile.yaml${NC}"
  read -p "   Chemin : " profile_path
  
  if [ -z "$profile_path" ]; then
    warn "Aucun chemin fourni, abandon"
    return 0
  fi
  
  if [ ! -f "$profile_path" ]; then
    fail "Profil introuvable: $profile_path"
    return 1
  fi
  
  echo ""
  echo -e "${YELLOW}Ingestion profil: $profile_path${NC}"
  read -p "Confirmer ingestion v1 ? (o/n): " confirm
  
  if [[ ! "$confirm" =~ ^[Oo]$ ]]; then
    warn "Ingestion v1 annulée"
    return 0
  fi
  
  cd "$PROJECT_ROOT"
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  
  echo ""
  if python3 -c "
from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
ing = Neo4jIngester()
stats = ing.ingest_profile('$profile_path')
print(f'✅ Stats: {stats}')
ing.close()
"; then
    echo ""
    ok "Ingestion v1 terminée !"
    echo -e "${GREEN}   Nodes créés: :Repo, :Contributor, :Hotspot, :Directory, :Extension${NC}"
  else
    echo ""
    fail "Échec ingestion v1"
    return 1
  fi
}
```

---

## 2️⃣ Modifier le MAIN

### A. Ajouter la question v1 (ligne ~372)

**REMPLACER** :
```bash
read -p "Vérifier et démarrer les services ? (o/n): " do_verify
read -p "Ingérer v2 (Git + Docs + Code) ? (o/n): " do_ingest_v2
```

**PAR** :
```bash
read -p "Vérifier et démarrer les services ? (o/n): " do_verify
read -p "Ingérer v1 (profils Git) ? (o/n): " do_ingest_v1
read -p "Ingérer v2 (Code Analysis) ? (o/n): " do_ingest_v2
```

### B. Modifier le récapitulatif (ligne ~379)

**REMPLACER** :
```bash
banner "🎯 Récapitulatif"
[[ "$do_verify" =~ ^[Oo]$ ]] && echo "✅ Vérification services"
[[ "$do_ingest_v2" =~ ^[Oo]$ ]] && echo "✅ Ingestion v2 (multi-sources)"
```

**PAR** :
```bash
banner "🎯 Récapitulatif"
[[ "$do_verify" =~ ^[Oo]$ ]] && echo "✅ Vérification services"
[[ "$do_ingest_v1" =~ ^[Oo]$ ]] && echo "✅ Ingestion v1 (profils Git)"
[[ "$do_ingest_v2" =~ ^[Oo]$ ]] && echo "✅ Ingestion v2 (Code Analysis)"
```

### C. Ajouter l'exécution v1 (ligne ~395)

**REMPLACER** :
```bash
# 1) Ingestion v2 (avant de lancer les services)
if [[ "$do_ingest_v2" =~ ^[Oo]$ ]]; then
  run_ingestion_v2
fi
```

**PAR** :
```bash
# 1) Ingestion v1 (profils Git)
if [[ "$do_ingest_v1" =~ ^[Oo]$ ]]; then
  run_ingestion_v1
fi

# 2) Ingestion v2 (Code Analysis)
if [[ "$do_ingest_v2" =~ ^[Oo]$ ]]; then
  run_ingestion_v2
fi
```

---

## ✅ Résultat final

Après modification, le menu sera :

```
🚀 HYPERION MASTER V2 - Contrôle complet

Vérifier et démarrer les services ? (o/n): 
Ingérer v1 (profils Git) ? (o/n):          ← NOUVEAU !
Ingérer v2 (Code Analysis) ? (o/n): 
Générer documentation ? (o/n): 
Lancer dashboard React ? (o/n): 
Lancer Open WebUI (chat) ? (o/n): 
```

### Cas d'usage

**V1 seul** : Stats Git agrégées (Repo, Contributor, Hotspot)
```
Ingérer v1 ? o
Ingérer v2 ? n
```

**V2 seul** : Structure code (File, Function, Class)
```
Ingérer v1 ? n
Ingérer v2 ? o
```

**V1 + V2** : Tout (compatible, même base Neo4j)
```
Ingérer v1 ? o
Ingérer v2 ? o
```

---

## 🧪 Test

```bash
./scripts/deploy/hyperion_master.sh

# Tester v1 seul
Ingérer v1 ? o
  Chemin: data/repositories/requests/profile.yaml
  
# Puis tester v2
Ingérer v2 ? o
  Chemin: /tmp/requests
```

---

**Applique ces modifications manuellement dans ton éditeur !** 📝
