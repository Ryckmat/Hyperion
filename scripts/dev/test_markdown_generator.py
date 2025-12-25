#!/usr/bin/env python3
"""Test du MarkdownGenerator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperion.generators.markdown_generator import MarkdownGenerator


def main():
    """Test génération documentation Markdown."""

    profile_path = (
        Path(__file__).parent.parent / "data" / "repositories" / "requests" / "profile.yaml"
    )

    if not profile_path.exists():
        print(f"❌ Profil introuvable : {profile_path}")
        print(
            "💡 Lance d'abord : python3 scripts/hyperion_full_workflow.py /home/kortazo/Documents/requests"
        )
        sys.exit(1)

    print("=" * 70)
    print("📝 TEST MARKDOWN GENERATOR")
    print("=" * 70)
    print(f"\n📁 Profil : {profile_path}")

    # Créer le générateur
    generator = MarkdownGenerator()

    # Lister les templates disponibles
    print(f"\n📄 Templates disponibles : {', '.join(generator.list_templates())}")

    # Générer la documentation
    print("\n⏳ Génération en cours...")

    docs = generator.generate(str(profile_path))

    print("\n✅ Documentation générée !")

    for filename, content in docs.items():
        output_file = Path(__file__).parent.parent / "output" / "requests" / filename
        print(f"\n📄 {filename} ({len(content)} caractères)")
        print(f"   └─ Sauvegardé : {output_file}")

        # Afficher un aperçu
        lines = content.split("\n")
        print("\n   Aperçu (10 premières lignes) :")
        for line in lines[:10]:
            print(f"   │ {line}")
        print("   │ ...")
        print(f"   └─ Total : {len(lines)} lignes")

    print("\n" + "=" * 70)
    print("🎉 TEST RÉUSSI !")
    print("=" * 70)
    print("\n💡 Ouvre les fichiers générés dans output/requests/")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
