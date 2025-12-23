"""Générateur de documentation Markdown depuis profils Hyperion."""

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from hyperion.config import OUTPUT_DIR, TEMPLATES_DIR


class MarkdownGenerator:
    """
    Génère de la documentation Markdown depuis des profils YAML Hyperion.

    Utilise les templates Jinja2 pour créer :
    - index.md : Vue d'ensemble du projet
    - registre.md : Documentation technique détaillée

    Example:
        >>> generator = MarkdownGenerator()
        >>> docs = generator.generate("data/repositories/requests/profile.yaml")
        >>> print(docs["index.md"][:100])
    """

    def __init__(self, templates_dir: str | None = None):
        """
        Initialise le générateur Markdown.

        Args:
            templates_dir: Dossier contenant les templates Jinja2
                          (défaut: config.TEMPLATES_DIR / "markdown")
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = TEMPLATES_DIR / "markdown"

        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Dossier templates introuvable : {self.templates_dir}")

        # Configurer Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        profile_path: str,
        output_dir: str | None = None,
        formats: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Génère la documentation Markdown depuis un profil YAML.

        Args:
            profile_path: Chemin vers le fichier profile.yaml
            output_dir: Dossier de sortie (défaut: OUTPUT_DIR/{service})
            formats: Liste des formats à générer (défaut: ["index", "registre"])

        Returns:
            Dictionnaire {filename: content}
        """
        # Charger le profil
        profile = self._load_profile(profile_path)
        service = profile["service"]

        # Formats par défaut
        if formats is None:
            formats = ["index", "registre"]

        # Générer chaque format
        docs = {}
        for fmt in formats:
            template_file = f"{fmt}.md.j2"

            try:
                template = self.env.get_template(template_file)
                content = template.render(**profile)
                docs[f"{fmt}.md"] = content
            except Exception as e:
                print(f"⚠️  Template {template_file} non trouvé ou erreur : {e}")
                continue

        # Sauvegarder si output_dir spécifié
        output_path = Path(output_dir) if output_dir else OUTPUT_DIR / service

        output_path.mkdir(parents=True, exist_ok=True)

        for filename, content in docs.items():
            file_path = output_path / filename
            file_path.write_text(content, encoding="utf-8")

        return docs

    def generate_all(
        self, profiles_dir: str, output_base: str | None = None
    ) -> dict[str, dict[str, str]]:
        """
        Génère la documentation pour tous les profils d'un dossier.

        Args:
            profiles_dir: Dossier contenant les repos (ex: data/repositories/)
            output_base: Dossier de sortie de base (défaut: OUTPUT_DIR)

        Returns:
            Dictionnaire {service: {filename: content}}
        """
        profiles_path = Path(profiles_dir)

        if not profiles_path.exists():
            raise FileNotFoundError(f"Dossier introuvable : {profiles_dir}")

        all_docs = {}

        # Parcourir les sous-dossiers
        for repo_dir in profiles_path.iterdir():
            if not repo_dir.is_dir():
                continue

            profile_file = repo_dir / "profile.yaml"
            if not profile_file.exists():
                continue

            service = repo_dir.name

            # Output dir pour ce service
            output_dir = Path(output_base) / service if output_base else OUTPUT_DIR / service

            try:
                docs = self.generate(str(profile_file), str(output_dir))
                all_docs[service] = docs
                print(f"✅ Documentation générée pour {service}")
            except Exception as e:
                print(f"❌ Erreur pour {service} : {e}")

        return all_docs

    def _load_profile(self, profile_path: str) -> dict:
        """Charge un profil YAML."""
        path = Path(profile_path)
        if not path.exists():
            raise FileNotFoundError(f"Profil introuvable : {profile_path}")

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_templates(self) -> list[str]:
        """Liste les templates Markdown disponibles."""
        templates = []
        for file in self.templates_dir.glob("*.md.j2"):
            templates.append(file.stem)
        return sorted(templates)

    def preview(self, profile_path: str, template: str = "index") -> str:
        """
        Prévisualise un template sans sauvegarder.

        Args:
            profile_path: Chemin vers le profil YAML
            template: Nom du template (sans .md.j2)

        Returns:
            Contenu Markdown généré
        """
        profile = self._load_profile(profile_path)

        template_file = f"{template}.md.j2"
        tpl = self.env.get_template(template_file)

        return tpl.render(**profile)
