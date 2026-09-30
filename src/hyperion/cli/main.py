"""Point d'entrée CLI Hyperion."""

import sys
from pathlib import Path

import click
import yaml

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
    from hyperion.core.git_analyzer import GitAnalyzer

    click.echo(f"🔍 Analyse du dépôt : {repo_path}")

    try:
        # Analyser
        analyzer = GitAnalyzer(repo_path)
        profile_data = analyzer.analyze()

        repo_name = name or profile_data["service"]

        # Créer dossier output
        output_dir = Path(output) / repo_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarder YAML
        yaml_file = output_dir / "profile.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(profile_data, f, allow_unicode=True, sort_keys=False)

        # Stats
        click.echo("\n✅ Analyse terminée !")
        click.echo(f"   • Repo          : {repo_name}")
        click.echo(f"   • Commits       : {profile_data['git_summary']['commits']:,}")
        click.echo(f"   • Contributeurs : {profile_data['git_summary']['contributors']:,}")
        click.echo(f"   • Profil YAML   : {yaml_file}")

    except Exception as e:
        click.echo(f"❌ Erreur : {e}", err=True)
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
    from hyperion.modules.generators.markdown_generator import MarkdownGenerator

    click.echo(f"📝 Génération documentation ({format}) depuis : {profile_yaml}")

    if format == "html":
        click.echo("⚠️  Format HTML pas encore implémenté")
        sys.exit(1)

    try:
        # Charger le profil pour récupérer le nom
        with open(profile_yaml) as f:
            profile_data = yaml.safe_load(f)

        repo_name = profile_data["service"]

        # Générer
        generator = MarkdownGenerator()

        output_dir = Path(output) / repo_name if output == "output/" else Path(output)

        docs = generator.generate(profile_yaml, str(output_dir))

        click.echo("\n✅ Documentation générée !")
        for filename in docs:
            click.echo(f"   • {output_dir / filename}")

    except Exception as e:
        click.echo(f"❌ Erreur : {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--tags-pattern", default=r"^v?\d+\.\d+\\.\\d+$", help=r"Pattern regex tags prod")
@click.option(
    "--output",
    "-o",
    "output_dir",
    default="data/repositories/",
    help="Dossier de sortie",
)
def export(repo_path: str, tags_pattern: str, output_dir: str):
    """
    Exporte l'historique production (releases taggées)

    Génère :
    - prod_deploys.json : Index releases avec agrégats
    - prod_commits.jsonl : Commits par release (1 par ligne)
    - prod_files.jsonl : Fichiers modifiés (1 par ligne)

    Exemple :
        hyperion export /path/to/repo --tags-pattern "^v\\d+\\.\\d+\\.\\d+$"
    """
    click.echo(f"📦 Export historique prod : {repo_path}")
    click.echo(f"   Pattern tags : {tags_pattern}")
    repo_name = Path(repo_path).resolve().name
    out_dir = Path(output_dir) / repo_name
    out_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"   Output dir    : {out_dir}")
    click.echo("⚠️  Module core en cours de développement")
    click.echo("📋 Voir : https://github.com/Ryckmat/Hyperion/issues")
    sys.exit(1)


@cli.command()
@click.argument("profile_yaml", type=click.Path(exists=True))
@click.option("--uri", default=None, help="Neo4j URI (défaut: env NEO4J_URI)")
@click.option("--user", default=None, help="Neo4j user (défaut: env NEO4J_USER)")
@click.option("--password", default=None, help="Neo4j password (défaut: env NEO4J_PASSWORD)")
@click.option("--database", default=None, help="Neo4j database (défaut: env NEO4J_DATABASE)")
@click.option("--clear", is_flag=True, help="Nettoyer les données existantes")
def ingest(profile_yaml: str, uri: str, user: str, password: str, database: str, clear: bool):
    """
    Ingestion Neo4j depuis profil Hyperion

    Crée le graphe de connaissances :
    - Repos, branches, tags
    - Commits, auteurs, fichiers
    - Relations TOUCHED, IN_RELEASE, etc.

    Exemple :
        hyperion ingest data/repositories/mon-repo/profile.yaml --clear
    """
    from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester

    click.echo(f"🗄️  Ingestion Neo4j depuis : {profile_yaml}")

    try:
        # Charger le profil
        with open(profile_yaml) as f:
            profile_data = yaml.safe_load(f)

        repo_name = profile_data["service"]

        # Créer l'ingester
        ingester = Neo4jIngester(uri=uri, user=user, password=password, database=database)
        click.echo("✅ Connexion Neo4j établie")

        # Clear si demandé
        if clear:
            click.echo(f"🧹 Nettoyage des données pour '{repo_name}'...")
            ingester.clear_repo(repo_name)

        # Ingestion
        click.echo("⏳ Ingestion en cours...")
        stats = ingester.ingest_profile(profile_yaml)

        click.echo("\n✅ Ingestion terminée !")
        click.echo(f"   • Repo          : {stats['repo']}")
        click.echo(f"   • Contributeurs : {stats['contributors']}")
        click.echo(f"   • Hotspots      : {stats['hotspots']}")
        click.echo(f"   • Répertoires   : {stats['directories']}")
        click.echo(f"   • Extensions    : {stats['extensions']}")

        ingester.close()

    except Exception as e:
        click.echo(f"❌ Erreur : {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--host", default="localhost", help="Host de l'API")
@click.option("--port", default=8000, help="Port de l'API")
@click.option("--reload", is_flag=True, help="Mode développement avec reload")
def server(host: str, port: int, reload: bool):
    """
    Lance le serveur API Hyperion (point d'entrée principal)

    Cette commande démarre l'API Gateway avec tous les services intégrés :
    - API REST FastAPI
    - Endpoints OpenAI-compatibles
    - Métriques et monitoring
    - Cache et sécurité

    Exemple :
        hyperion server --host 0.0.0.0 --port 8000
    """
    import uvicorn

    click.echo(f"🚀 Démarrage serveur Hyperion v{__version__}")
    click.echo(f"   • Host: {host}")
    click.echo(f"   • Port: {port}")
    click.echo(f"   • Mode dev: {'Oui' if reload else 'Non'}")
    click.echo()
    click.echo("📊 Endpoints disponibles :")
    click.echo(f"   • API REST     : http://{host}:{port}/api/")
    click.echo(f"   • Docs         : http://{host}:{port}/docs")
    click.echo(f"   • Health       : http://{host}:{port}/api/health")
    click.echo(f"   • OpenAI       : http://{host}:{port}/v1/")
    click.echo()

    try:
        uvicorn.run("hyperion.api.main:app", host=host, port=port, reload=reload, log_level="info")
    except Exception as e:
        click.echo(f"❌ Erreur serveur : {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--profile",
    default="minimal",
    help="Profil de services",
    type=click.Choice(["minimal", "full"]),
)
@click.option("--detach", "-d", is_flag=True, help="Mode détaché")
def services(profile: str, detach: bool):
    """
    Lance tous les services Docker Hyperion

    Profils disponibles :
    - minimal : qdrant, ollama, hyperion-api (démarrage rapide)
    - full : tous les services (neo4j, prometheus, mlflow, dashboard)

    Exemple :
        hyperion services --profile full --detach
    """
    import subprocess

    click.echo(f"🐳 Lancement des services Docker (profil: {profile})")

    compose_args = ["docker", "compose"]

    if profile == "full":
        compose_args.extend(["--profile", "full"])

    compose_args.append("up")

    if detach:
        compose_args.append("-d")

    try:
        click.echo(f"   • Commande: {' '.join(compose_args)}")
        subprocess.run(compose_args, check=True)

        if detach:
            click.echo("\n✅ Services lancés en arrière-plan")
            click.echo("   • Vérifier : docker compose ps")
            click.echo("   • Logs     : docker compose logs -f")

    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Erreur Docker : {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo("❌ Docker ou docker-compose non trouvé", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    default="detailed",
    help="Format d'affichage",
    type=click.Choice(["detailed", "compact"]),
)
def status(format: str):
    """
    Affiche le statut des services Hyperion

    Vérifie la connectivité vers :
    - API Hyperion
    - Qdrant (vector DB)
    - Ollama (LLM)
    - Neo4j (graph DB)
    - Services optionnels
    """
    import requests

    from hyperion.settings import settings

    click.echo(f"🔍 Statut des services Hyperion v{__version__}")
    click.echo("=" * 50)

    services_status = []

    # Test API Hyperion
    try:
        resp = requests.get(f"http://{settings.api_host}:{settings.api_port}/api/health", timeout=5)
        if resp.status_code == 200:
            services_status.append(
                ("API Hyperion", "🟢 OK", f"http://{settings.api_host}:{settings.api_port}")
            )
        else:
            services_status.append(("API Hyperion", "🟡 Erreur", f"Status: {resp.status_code}"))
    except Exception:
        services_status.append(
            ("API Hyperion", "🔴 Indisponible", f"http://{settings.api_host}:{settings.api_port}")
        )

    # Test Qdrant
    try:
        import requests

        resp = requests.get(f"http://{settings.qdrant_host}:{settings.qdrant_port}/", timeout=5)
        if resp.status_code == 200:
            services_status.append(
                ("Qdrant", "🟢 OK", f"http://{settings.qdrant_host}:{settings.qdrant_port}")
            )
        else:
            services_status.append(("Qdrant", "🟡 Erreur", f"Status: {resp.status_code}"))
    except Exception:
        services_status.append(
            ("Qdrant", "🔴 Indisponible", f"http://{settings.qdrant_host}:{settings.qdrant_port}")
        )

    # Test Ollama
    try:
        resp = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            services_status.append(("Ollama", "🟢 OK", settings.ollama_base_url))
        else:
            services_status.append(("Ollama", "🟡 Erreur", f"Status: {resp.status_code}"))
    except Exception:
        services_status.append(("Ollama", "🔴 Indisponible", settings.ollama_base_url))

    # Affichage
    if format == "compact":
        for name, status, _ in services_status:
            click.echo(f"{name}: {status}")
    else:
        for name, status, url in services_status:
            click.echo(f"   {name:<15} {status:<15} {url}")

    click.echo()


@cli.command()
@click.option("--suite", default="eval/suites/core.yaml", help="Suite d'évaluation à exécuter")
@click.option(
    "--format",
    "formats",
    multiple=True,
    default=["json", "markdown"],
    type=click.Choice(["json", "markdown", "html"]),
    help="Formats de rapport",
)
@click.option("--output", default="eval/reports", help="Dossier de sortie des rapports")
def eval(suite: str, formats: list, output: str):
    """
    Lance une évaluation du système RAG

    Exécute une suite de tests pour évaluer les performances du RAG :
    - Précision des réponses
    - Détection d'hallucinations
    - Temps de réponse
    - Score de confiance

    Exemple :
        hyperion eval --suite eval/suites/core.yaml --format json html
    """
    import asyncio
    from pathlib import Path

    click.echo("🧪 Lancement de l'évaluation RAG")
    click.echo(f"   • Suite : {suite}")
    click.echo(f"   • Formats : {', '.join(formats)}")
    click.echo()

    try:
        # Importer le système d'évaluation
        from eval.run import RAGEvaluator

        async def run_evaluation():
            evaluator = RAGEvaluator()

            # Vérifier que la suite existe
            suite_path = Path(suite)
            if not suite_path.exists():
                click.echo(f"❌ Suite non trouvée : {suite}")
                return False

            # Exécuter l'évaluation
            results = await evaluator.run_test_suite(str(suite_path))

            # Charger le nom de la suite
            suite_config = evaluator.load_test_suite(str(suite_path))
            suite_name = suite_config["name"]

            # Générer les rapports
            report_files = evaluator.generate_reports(results, suite_name, list(formats), output)

            click.echo("\n🎉 Évaluation terminée !")
            click.echo(
                f"   • Tests réussis : {sum(1 for r in results if r.success)}/{len(results)}"
            )

            avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0
            avg_confidence = (
                sum(r.confidence_score for r in results) / len(results) if results else 0
            )

            click.echo(f"   • Latence moyenne : {avg_latency:.0f}ms")
            click.echo(f"   • Confiance moyenne : {avg_confidence:.2f}")
            click.echo()
            click.echo("📋 Rapports générés :")
            for file in report_files:
                click.echo(f"   📄 {file}")

            return True

        # Exécution asynchrone
        success = asyncio.run(run_evaluation())
        if not success:
            sys.exit(1)

    except ImportError as e:
        click.echo(f"❌ Module d'évaluation non disponible : {e}")
        click.echo("   Vérifiez l'installation du framework d'évaluation")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Erreur lors de l'évaluation : {e}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """
    Affiche les informations système Hyperion
    """
    from hyperion.settings import settings

    click.echo("=" * 60)
    click.echo(f"🚀 Hyperion v{__version__}")
    click.echo("=" * 60)
    click.echo()
    click.echo("📁 Chemins :")
    click.echo(f"   PROJECT_ROOT    : {settings.project_root}")
    click.echo(f"   CONFIG_DIR      : {settings.config_dir}")
    click.echo(f"   TEMPLATES_DIR   : {settings.templates_dir}")
    click.echo(f"   DATA_DIR        : {settings.data_dir}")
    click.echo(f"   OUTPUT_DIR      : {settings.output_dir}")
    click.echo()
    click.echo("🔧 Configuration Neo4j :")
    click.echo(f"   URI             : {settings.neo4j_uri}")
    click.echo(f"   USER            : {settings.neo4j_user}")
    click.echo(f"   DATABASE        : {settings.neo4j_database}")
    click.echo()
    click.echo("🧠 Configuration LLM :")
    click.echo(f"   OLLAMA_URL      : {settings.ollama_base_url}")
    click.echo(f"   MODEL           : {settings.ollama_model}")
    click.echo(f"   TEMPERATURE     : {settings.llm_temperature}")
    click.echo()
    click.echo("⚙️  Performance :")
    click.echo(f"   BATCH_COMMITS   : {settings.batch_size_commits}")
    click.echo(f"   BATCH_FILES     : {settings.batch_size_files}")
    click.echo()
    click.echo("🔍 Filtres actifs :")
    filters = settings.load_filters()
    click.echo(f"   Extensions      : {len(filters.get('ignore_extensions', []))} ignorées")
    click.echo(f"   Préfixes        : {len(filters.get('ignore_prefixes', []))} ignorés")
    click.echo(f"   Fichiers        : {len(filters.get('ignore_files', []))} ignorés")
    click.echo()


# Alias pour entry_point console_scripts
main = cli


if __name__ == "__main__":
    cli()
