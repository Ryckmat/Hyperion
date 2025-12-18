"""Point d'entrée CLI Hyperion."""
import click
from pathlib import Path
import sys

from hyperion.__version__ import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Hyperion - Git Repository Profiler & Knowledge Graph
    
    Analyse vos dépôts Git et génère automatiquement de la documentation technique structurée.
    """
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--output", "-o", default="data/repositories/", help="Dossier de sortie")
@click.option("--name", "-n", help="Nom du repo (auto-détecté si omis)")
def profile(repo_path: str, output: str, name: str):
    """
    Profile un dépôt Git et génère profile.yaml
    
    Analyse complète :
    - Commits, contributeurs, hotspots
    - Métriques qualité (code/tests/docs)
    - Détection CI/CD et licence
    - Stats par extension et répertoire
    
    Exemple :
        hyperion profile /path/to/repo --output data/repositories/
    """
    click.echo(f"🔍 Analyse du dépôt : {repo_path}")
    click.echo("⚠️  Module core en cours de développement")
    click.echo("📋 Voir : https://github.com/Ryckmat/Hyperion/issues")
    sys.exit(1)


@cli.command()
@click.argument("profile_yaml", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["markdown", "html"]), default="markdown")
@click.option("--output", "-o", default="output/", help="Dossier de sortie")
def generate(profile_yaml: str, format: str, output: str):
    """
    Génère la documentation depuis profile.yaml
    
    Formats supportés :
    - markdown : index.md + registre.md
    - html : dashboard.html (futur)
    
    Exemple :
        hyperion generate data/repositories/mon-repo/profile.yaml --output output/mon-repo/
    """
    click.echo(f"📝 Génération documentation ({format}) depuis : {profile_yaml}")
    click.echo("⚠️  Module generators en cours de développement")
    click.echo("📋 Voir : https://github.com/Ryckmat/Hyperion/issues")
    sys.exit(1)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--tags-pattern", default=r"^v?\d+\.\d+\.\d+$", help="Pattern regex tags prod")
@click.option("--output", "-o", default="data/repositories/", help="Dossier de sortie")
def export(repo_path: str, tags_pattern: str, output: str):
    """
    Exporte l'historique production (releases taggées)
    
    Génère :
    - prod_deploys.json : Index releases avec agrégats
    - prod_commits.jsonl : Commits par release (1 par ligne)
    - prod_files.jsonl : Fichiers modifiés (1 par ligne)
    
    Exemple :
        hyperion export /path/to/repo --tags-pattern "^v\d+\.\d+\.\d+$"
    """
    click.echo(f"📦 Export historique prod : {repo_path}")
    click.echo(f"   Pattern tags : {tags_pattern}")
    click.echo("⚠️  Module core en cours de développement")
    click.echo("📋 Voir : https://github.com/Ryckmat/Hyperion/issues")
    sys.exit(1)


@cli.command()
@click.argument("data_dir", type=click.Path(exists=True))
@click.option("--uri", default=None, help="Neo4j URI (défaut: env NEO4J_URI)")
@click.option("--user", default=None, help="Neo4j user (défaut: env NEO4J_USER)")
@click.option("--password", default=None, help="Neo4j password (défaut: env NEO4J_PASSWORD)")
@click.option("--database", default=None, help="Neo4j database (défaut: env NEO4J_DATABASE)")
def ingest(data_dir: str, uri: str, user: str, password: str, database: str):
    """
    Ingestion Neo4j depuis exports Hyperion
    
    Crée le graphe de connaissances :
    - Repos, branches, tags
    - Commits, auteurs, fichiers
    - Relations TOUCHED, IN_RELEASE, etc.
    
    Exemple :
        hyperion ingest data/repositories/mon-repo/ --uri bolt://localhost:7687
    """
    click.echo(f"🗄️  Ingestion Neo4j depuis : {data_dir}")
    click.echo("⚠️  Module integrations en cours de développement")
    click.echo("📋 Voir : https://github.com/Ryckmat/Hyperion/issues")
    sys.exit(1)


@cli.command()
def info():
    """
    Affiche les informations système Hyperion
    """
    from hyperion import config
    
    click.echo("=" * 60)
    click.echo(f"🚀 Hyperion v{__version__}")
    click.echo("=" * 60)
    click.echo()
    click.echo("📁 Chemins :")
    click.echo(f"   PROJECT_ROOT    : {config.PROJECT_ROOT}")
    click.echo(f"   CONFIG_DIR      : {config.CONFIG_DIR}")
    click.echo(f"   TEMPLATES_DIR   : {config.TEMPLATES_DIR}")
    click.echo(f"   DATA_DIR        : {config.DATA_DIR}")
    click.echo(f"   OUTPUT_DIR      : {config.OUTPUT_DIR}")
    click.echo()
    click.echo("🔧 Configuration Neo4j :")
    click.echo(f"   URI             : {config.NEO4J_URI}")
    click.echo(f"   USER            : {config.NEO4J_USER}")
    click.echo(f"   DATABASE        : {config.NEO4J_DATABASE}")
    click.echo()
    click.echo("⚙️  Batch sizes :")
    click.echo(f"   COMMITS         : {config.BATCH_SIZE_COMMITS}")
    click.echo(f"   FILES           : {config.BATCH_SIZE_FILES}")
    click.echo()
    click.echo("🔍 Filtres actifs :")
    click.echo(f"   Extensions      : {len(config.FILTERS.get('ignore_extensions', []))} ignorées")
    click.echo(f"   Préfixes        : {len(config.FILTERS.get('ignore_prefixes', []))} ignorés")
    click.echo(f"   Fichiers        : {len(config.FILTERS.get('ignore_files', []))} ignorés")
    click.echo()


if __name__ == "__main__":
    cli()
