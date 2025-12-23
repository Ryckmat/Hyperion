"""Tests de base pour vérifier la structure."""

from hyperion.__version__ import __version__


def test_version():
    """Test version Hyperion."""
    assert __version__ == "2.0.0", f"Version is {__version__!r}"


def test_project_structure(project_root):
    """Test structure du projet."""
    # Vérifier dossiers principaux
    assert (project_root / "src" / "hyperion").exists()
    assert (project_root / "templates").exists()
    assert (project_root / "config").exists()
    assert (project_root / "data").exists()
    assert (project_root / "docs").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "scripts").exists()

    # Vérifier fichiers racine
    assert (project_root / "README.md").exists()
    assert (project_root / "docs" / "CHANGELOG.md").exists()
    assert (project_root / "setup.py").exists()
    assert (project_root / "requirements.txt").exists()
    assert (project_root / ".gitignore").exists()


def test_config_exists(project_root):
    """Test fichier config/filters.yaml."""
    filters = project_root / "config" / "filters.yaml"
    assert filters.exists()


def test_templates_exist(templates_dir):
    """Test templates Jinja2."""
    assert (templates_dir / "markdown" / "index.md.j2").exists()
    assert (templates_dir / "markdown" / "registre.md.j2").exists()


def test_cli_imports():
    """Test imports CLI."""
    from hyperion.cli import main

    assert hasattr(main, "cli")


def test_config_imports():
    """Test imports config."""
    from hyperion import config

    assert hasattr(config, "PROJECT_ROOT")
    assert hasattr(config, "FILTERS")
    assert hasattr(config, "NEO4J_URI")
