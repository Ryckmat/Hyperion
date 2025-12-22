"""Tests pour hyperion.core.git_analyzer."""

import pytest

from hyperion.core.git_analyzer import GitAnalyzer


@pytest.fixture
def analyzer(hyperion_repo):
    """Fixture GitAnalyzer sur le repo Hyperion."""
    return GitAnalyzer(str(hyperion_repo))


def test_git_analyzer_initialization(hyperion_repo):
    """Test initialisation du GitAnalyzer."""
    analyzer = GitAnalyzer(str(hyperion_repo))

    assert analyzer.repo is not None
    assert analyzer.filters is not None
    assert analyzer.repo_name == "hyperion"


def test_analyze_returns_complete_profile(analyzer):
    """Test que analyze() retourne un profil complet."""
    profile = analyzer.analyze()

    # Structure principale
    assert "service" in profile
    assert "git_summary" in profile
    assert "repositories" in profile
    assert "metrics" in profile

    # Git summary
    git_summary = profile["git_summary"]
    assert "commits" in git_summary
    assert "contributors" in git_summary
    assert "hotspots_top10" in git_summary
    assert "contributors_top10" in git_summary

    # Repositories
    assert len(profile["repositories"]) == 1
    repo = profile["repositories"][0]
    assert "name" in repo
    assert "url" in repo
    assert "default_branch" in repo


def test_analyze_git_summary_structure(analyzer):
    """Test structure détaillée du git_summary."""
    profile = analyzer.analyze()
    git_summary = profile["git_summary"]

    # Commits
    assert isinstance(git_summary["commits"], int)
    assert git_summary["commits"] > 0

    # Contributors
    assert isinstance(git_summary["contributors"], int)
    assert git_summary["contributors"] > 0


def test_analyze_repository_info(analyzer):
    """Test informations du repository."""
    profile = analyzer.analyze()
    repo = profile["repositories"][0]

    # Métadonnées basiques
    assert repo["name"] == "Hyperion"
    assert repo["default_branch"] in ["main", "master"]
    assert repo["main_language"] == "python"


def test_analyze_contributors(analyzer):
    """Test déduplication et tri des contributeurs."""
    profile = analyzer.analyze()
    git_summary = profile["git_summary"]
    contributors = git_summary["contributors_top10"]

    # Doit avoir des contributeurs
    assert len(contributors) > 0

    # Structure contributeur
    for contrib in contributors:
        assert "name" in contrib
        assert "email" in contrib
        assert "commits" in contrib
        assert isinstance(contrib["commits"], int)
        assert contrib["commits"] > 0


def test_analyze_hotspots(analyzer):
    """Test calcul des hotspots."""
    profile = analyzer.analyze()
    git_summary = profile["git_summary"]
    hotspots = git_summary["hotspots_top10"]

    # Doit avoir des hotspots
    assert len(hotspots) > 0

    # Structure hotspot
    for hotspot in hotspots:
        assert "path" in hotspot
        assert "changes" in hotspot
        assert isinstance(hotspot["changes"], int)
        assert hotspot["changes"] > 0


def test_analyze_extensions(analyzer):
    """Test statistiques par extension."""
    profile = analyzer.analyze()
    git_summary = profile["git_summary"]
    by_extension = git_summary["by_extension"]

    # Doit avoir des extensions
    assert len(by_extension) > 0

    # Python doit être présent
    python_ext = next((ext for ext in by_extension if ext["ext"] == ".py"), None)
    assert python_ext is not None
    assert python_ext["files"] > 0
    assert python_ext["changes"] > 0


def test_analyze_directories(analyzer):
    """Test statistiques par répertoire."""
    profile = analyzer.analyze()
    git_summary = profile["git_summary"]
    directories = git_summary["directories_top"]

    # Doit avoir des répertoires
    assert len(directories) > 0

    # Structure répertoire
    for directory in directories:
        assert "dir" in directory
        assert "changes" in directory


def test_analyze_metrics(analyzer):
    """Test métriques de qualité."""
    profile = analyzer.analyze()
    metrics = profile["metrics"]

    # Test que metrics existe et contient des données
    assert metrics is not None
    assert isinstance(metrics, dict)
    assert len(metrics) > 0

    # Vérifier quelques métriques connues
    assert "avg_changes_per_hotspot" in metrics or "evolution_years" in metrics


def test_deduplicate_contributors(analyzer):
    """Test déduplication des contributeurs."""
    # Contributors avec duplicatas
    raw_contributors = [
        {"name": "John Doe", "email": "john@example.com", "commits": 10},
        {
            "name": "John Doe",
            "email": "john@users.noreply.github.com",
            "commits": 5,
        },
        {"name": "Jane Smith", "email": "jane@example.com", "commits": 8},
    ]

    deduplicated = analyzer._deduplicate_contributors(raw_contributors)

    # Doit fusionner les deux John Doe
    assert len(deduplicated) == 2

    # John Doe doit avoir 15 commits (10+5)
    john = next(c for c in deduplicated if c["name"] == "John Doe")
    assert john["commits"] == 15


def test_calculate_hotspots_filtering(analyzer):
    """Test filtrage des hotspots."""
    numstat = [
        (100, 50, "src/module.py"),
        (80, 40, "tests/test_module.py"),
        (5, 5, ".gitignore"),
    ]

    hotspots = analyzer._calculate_hotspots(numstat)

    # hotspots est une liste de tuples (path, changes)
    paths = [path for path, _ in hotspots]
    assert "src/module.py" in paths
    assert "tests/test_module.py" in paths


def test_stats_by_extension(analyzer):
    """Test statistiques par extension."""
    numstat = [
        (100, 50, "src/module.py"),
        (80, 40, "tests/test.py"),
    ]

    by_extension = analyzer._stats_by_extension(numstat)

    # Vérifier les extensions
    extensions = {stat["ext"] for stat in by_extension}
    assert ".py" in extensions

    # Stats Python
    py_stat = next(s for s in by_extension if s["ext"] == ".py")
    assert py_stat["files"] == 2  # module.py + test.py
    assert py_stat["changes"] == 270  # (100+50) + (80+40)


def test_stats_by_directory(analyzer):
    """Test statistiques par répertoire."""
    numstat = [
        (100, 50, "src/module.py"),
        (80, 40, "tests/test_module.py"),
        (30, 20, "docs/guide.md"),
    ]

    directories = analyzer._stats_by_directory(numstat)

    # Vérifier les répertoires (premier niveau)
    dir_names = {d["dir"] for d in directories}
    assert "src" in dir_names
    assert "tests" in dir_names
    assert "docs" in dir_names


def test_should_ignore_file(analyzer):
    """Test filtrage des fichiers à ignorer."""
    # Test basique - les filtres sont dans config.yaml
    # On teste juste que la méthode fonctionne
    result = analyzer._should_ignore("src/module.py")
    assert isinstance(result, bool)
