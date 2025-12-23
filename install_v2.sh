#!/bin/bash
# Script d'installation Hyperion v2
# Auteur: Ryckman Matthieu

set -e

REPO_ROOT="/home/kortazo/Documents/Hyperion"
ARCHIVE="/tmp/hyperion_v2_modules.tar.gz"

echo "🚀 Installation Hyperion v2..."

# Télécharger l'archive (à placer dans /tmp d'abord)
if [ ! -f "$ARCHIVE" ]; then
    echo "❌ Archive non trouvée: $ARCHIVE"
    echo "📥 Télécharge d'abord: hyperion_v2_modules.tar.gz"
    echo "   et place-la dans /tmp/"
    exit 1
fi

# Extraire
cd "$REPO_ROOT"
tar -xzf "$ARCHIVE"

echo "✅ Installation terminée !"
echo ""
echo "📊 Vérification:"
ls -1 src/hyperion/modules/
echo ""
echo "🎯 Prochaine étape:"
echo "   cd $REPO_ROOT"
echo "   git status"
echo "   git add ."
echo "   git commit -m 'feat(v2): architecture complète 8 modules'"
