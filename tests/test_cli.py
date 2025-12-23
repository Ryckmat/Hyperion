"""Tests pour hyperion.cli.main."""

import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from hyperion.cli.main import cli


@pytest.fixture
def runner():
    """Fixture Click CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_output_dir():
    """Fixture répertoire de sortie temporaire."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_cli_help(runner):
    """Test affichage de l'aide."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Hyperion" in result.output
    assert "Git Repository Profiler" in result.output


def test_cli_version(runner):
    """Test affichage de la version."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "2.0.0" in result.output


def test_profile_command_help(runner):
    """Test aide de la commande profile."""
    result = runner.invoke(cli, ["profile", "--help"])
    assert result.exit_code == 0
    assert "profile" in result.output.lower()
    assert "repo_path" in result.output.lower()


def test_profile_command_missing_repo(runner):
    """Test profile avec repo manquant."""
    result = runner.invoke(cli, ["profile", "/path/that/does/not/exist"])
    assert result.exit_code != 0


def test_profile_command_success(runner, hyperion_repo, temp_output_dir):
    """Test profile sur le repo Hyperion."""
    result = runner.invoke(
        cli, ["profile", str(hyperion_repo), "--output", str(temp_output_dir)]
    )

    # Doit réussir
    assert result.exit_code == 0
    assert "Analyse du dépôt" in result.output
    assert "Analyse terminée" in result.output

    # Vérifier que le fichier profile.yaml a été créé
    profile_file = temp_output_dir / "Hyperion" / "profile.yaml"
    assert profile_file.exists()

    # Vérifier le contenu
    with open(profile_file) as f:
        profile = yaml.safe_load(f)
        assert "service" in profile
        assert "git_summary" in profile


def test_profile_command_with_name(runner, hyperion_repo, temp_output_dir):
    """Test profile avec nom custom."""
    result = runner.invoke(
        cli,
        [
            "profile",
            str(hyperion_repo),
            "--output",
            str(temp_output_dir),
            "--name",
            "CustomName",
        ],
    )

    assert result.exit_code == 0

    # Vérifier que le fichier est créé avec le nom custom
    profile_file = temp_output_dir / "CustomName" / "profile.yaml"
    assert profile_file.exists()


def test_generate_command_help(runner):
    """Test aide de la commande generate."""
    result = runner.invoke(cli, ["generate", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.output.lower()


def test_generate_command_missing_profile(runner):
    """Test generate avec profile manquant."""
    result = runner.invoke(cli, ["generate", "/path/that/does/not/exist"])
    assert result.exit_code != 0


def test_generate_command_success(runner, hyperion_repo, temp_output_dir):
    """Test génération de documentation."""
    # D'abord créer un profil
    profile_dir = temp_output_dir / "test_repo"
    profile_dir.mkdir(parents=True)
    profile_file = profile_dir / "profile.yaml"

    # Créer un profil minimal
    profile_data = {
        "service": "test_repo",
        "owner": {"team": "Test", "contacts": []},
        "repositories": [{"name": "test_repo", "url": None}],
        "git_summary": {
            "commits": 10,
            "contributors": 1,
            "recent_commits_90d": 5,
            "hotspots_top10": [],
            "contributors_top10": [],
            "by_extension": [],
            "directories_top": [],
        },
        "tech": {"runtime": "python", "framework": "none", "ci": "unknown"},
        "metrics": {},
    }

    with open(profile_file, "w") as f:
        yaml.dump(profile_data, f)

    # Générer la documentation
    output_dir = temp_output_dir / "output"
    result = runner.invoke(
        cli, ["generate", str(profile_file), "--output", str(output_dir)]
    )

    assert result.exit_code == 0
    assert "Documentation générée" in result.output


def test_export_command_help(runner):
    """Test aide de la commande export."""
    result = runner.invoke(cli, ["export", "--help"])
    assert result.exit_code == 0
    assert "export" in result.output.lower()


def test_ingest_command_help(runner):
    """Test aide de la commande ingest."""
    result = runner.invoke(cli, ["ingest", "--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output.lower()


def test_ingest_command_missing_profile(runner):
    """Test ingest avec profile manquant."""
    result = runner.invoke(cli, ["ingest", "/path/that/does/not/exist"])
    assert result.exit_code != 0


def test_info_command_help(runner):
    """Test aide de la commande info."""
    result = runner.invoke(cli, ["info", "--help"])
    assert result.exit_code == 0
    assert "info" in result.output.lower()


def test_info_command_success(runner):
    """Test affichage des informations."""
    result = runner.invoke(cli, ["info"])

    assert result.exit_code == 0
    assert "Hyperion" in result.output
    # Doit afficher des informations sur le projet


def test_profile_error_handling(runner):
    """Test gestion d'erreur dans profile."""
    # Créer un fichier temporaire (pas un repo Git)
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ["profile", tmpdir])
        assert result.exit_code != 0
        assert "erreur" in result.output.lower() or "error" in result.output.lower()


def test_generate_command_html_format(runner, temp_output_dir):
    """Test generate avec format HTML (pas implémenté)."""
    # Créer un profil minimal
    profile_dir = temp_output_dir / "test_html"
    profile_dir.mkdir(parents=True)
    profile_file = profile_dir / "profile.yaml"

    profile_data = {"service": "test_html"}

    with open(profile_file, "w") as f:
        yaml.dump(profile_data, f)

    # Tenter génération HTML
    result = runner.invoke(cli, ["generate", str(profile_file), "--format", "html"])

    # Doit échouer car HTML pas implémenté
    assert result.exit_code != 0
    assert "HTML" in result.output


def test_generate_command_error(runner, temp_output_dir):
    """Test generate avec fichier profile invalide."""
    # Créer un profil invalide (manque des champs requis)
    profile_file = temp_output_dir / "invalid.yaml"
    profile_file.write_text("invalid: yaml content without service field\n")

    # Doit échouer avec erreur
    result = runner.invoke(cli, ["generate", str(profile_file)])
    assert result.exit_code != 0
    assert "Erreur" in result.output or "❌" in result.output


def test_export_command_success(runner, hyperion_repo):
    """Test export command (pas encore implémenté)."""
    # Note: on ne passe pas --output car le paramètre est inutilisé (_output)
    result = runner.invoke(cli, ["export", str(hyperion_repo)])

    # Doit afficher un message d'avertissement  et exit code 1
    assert result.exit_code == 1
    # Vérifier qu'un message est affiché
    assert len(result.output) > 0


def test_ingest_command_success(runner, temp_output_dir):
    """Test ingest avec succès."""
    import unittest.mock as mock

    # Créer un profil minimal
    profile_file = temp_output_dir / "profile.yaml"
    profile_data = {
        "service": "test_ingest",
        "owner": {"team": "Test", "contacts": []},
        "repositories": [{"name": "test_ingest"}],
        "git_summary": {"commits": 10},
    }

    with open(profile_file, "w") as f:
        yaml.dump(profile_data, f)

    # Mock Neo4jIngester dans le bon module
    with mock.patch(
        "hyperion.modules.integrations.neo4j_ingester.Neo4jIngester"
    ) as MockIngester:
        mock_instance = MockIngester.return_value
        mock_instance.ingest_profile.return_value = {
            "repo": 1,
            "contributors": 5,
            "hotspots": 10,
            "directories": 3,
            "extensions": 2,
        }

        result = runner.invoke(cli, ["ingest", str(profile_file)])

        assert result.exit_code == 0
        assert "Ingestion terminée" in result.output
        assert "Contributeurs : 5" in result.output
        mock_instance.close.assert_called_once()


def test_ingest_command_with_clear(runner, temp_output_dir):
    """Test ingest avec --clear."""
    import unittest.mock as mock

    profile_file = temp_output_dir / "profile.yaml"
    profile_data = {
        "service": "test_clear",
        "git_summary": {"commits": 5},
    }

    with open(profile_file, "w") as f:
        yaml.dump(profile_data, f)

    with mock.patch(
        "hyperion.modules.integrations.neo4j_ingester.Neo4jIngester"
    ) as MockIngester:
        mock_instance = MockIngester.return_value
        mock_instance.ingest_profile.return_value = {
            "repo": 1,
            "contributors": 2,
            "hotspots": 5,
            "directories": 1,
            "extensions": 1,
        }

        result = runner.invoke(cli, ["ingest", str(profile_file), "--clear"])

        assert result.exit_code == 0
        assert "Nettoyage des données" in result.output
        mock_instance.clear_repo.assert_called_once_with("test_clear")


def test_ingest_command_error(runner, temp_output_dir):
    """Test ingest avec erreur."""
    import unittest.mock as mock

    profile_file = temp_output_dir / "profile.yaml"
    profile_data = {"service": "test_error"}

    with open(profile_file, "w") as f:
        yaml.dump(profile_data, f)

    with mock.patch(
        "hyperion.modules.integrations.neo4j_ingester.Neo4jIngester"
    ) as MockIngester:
        MockIngester.side_effect = RuntimeError("Connection failed")

        result = runner.invoke(cli, ["ingest", str(profile_file)])

        assert result.exit_code != 0
        assert "Erreur" in result.output or "❌" in result.output
