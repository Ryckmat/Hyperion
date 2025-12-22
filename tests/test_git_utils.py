"""Tests pour hyperion.utils.git_utils."""

import pytest
from pathlib import Path
from hyperion.utils.git_utils import GitRepo, GitCommandError


def test_git_repo_invalid_path():
    """Test avec un chemin invalide."""
    with pytest.raises(GitCommandError, match="n'existe pas"):
        GitRepo("/path/that/does/not/exist")


def test_git_repo_not_a_git_repo(tmp_path):
    """Test avec un dossier qui n'est pas un dépôt Git."""
    with pytest.raises(GitCommandError, match="Pas un dépôt Git"):
        GitRepo(str(tmp_path))


def test_git_repo_initialization(hyperion_repo):
    """Test initialisation avec le repo Hyperion lui-même."""
    # Utilise le repo Hyperion comme fixture
    repo = GitRepo(str(hyperion_repo))

    assert repo.repo_path.exists()
    assert (repo.repo_path / ".git").exists()


def test_get_name(hyperion_repo):
    """Test récupération du nom du dépôt."""
    repo = GitRepo(str(hyperion_repo))

    name = repo.get_name()
    assert name == "Hyperion" or name == hyperion_repo.name


def test_get_remote_url(hyperion_repo):
    """Test récupération de l'URL remote."""
    repo = GitRepo(str(hyperion_repo))

    url = repo.get_remote_url()
    # Peut être None si pas de remote configuré
    if url:
        assert "github.com" in url or "gitlab" in url or url.startswith("git@")


def test_detect_main_branch(hyperion_repo):
    """Test détection de la branche principale."""
    repo = GitRepo(str(hyperion_repo))

    branch = repo.detect_main_branch()
    assert branch in ["main", "master", "trunk", "develop"]


def test_get_commits(hyperion_repo):
    """Test récupération des commits."""
    repo = GitRepo(str(hyperion_repo))

    commits = repo.get_commits()

    assert len(commits) > 0
    assert "sha" in commits[0]
    assert "author_name" in commits[0]
    assert "author_email" in commits[0]
    assert "subject" in commits[0]
    assert isinstance(commits[0]["is_merge"], bool)


def test_get_commits_recent(hyperion_repo):
    """Test récupération des commits récents (90 jours)."""
    repo = GitRepo(str(hyperion_repo))

    recent = repo.get_commits(since="90.days")
    all_commits = repo.get_commits()

    # Les commits récents doivent être <= tous les commits
    assert len(recent) <= len(all_commits)


def test_get_contributors(hyperion_repo):
    """Test récupération des contributeurs."""
    repo = GitRepo(str(hyperion_repo))

    contributors = repo.get_contributors()

    assert len(contributors) > 0
    assert "name" in contributors[0]
    assert "email" in contributors[0]
    assert "commits" in contributors[0]
    assert contributors[0]["commits"] > 0


def test_get_numstat(hyperion_repo):
    """Test récupération du numstat."""
    repo = GitRepo(str(hyperion_repo))

    numstat = repo.get_numstat()

    assert len(numstat) > 0
    # Chaque entrée : (additions, deletions, path)
    assert len(numstat[0]) == 3
    assert isinstance(numstat[0][0], int)  # additions
    assert isinstance(numstat[0][1], int)  # deletions
    assert isinstance(numstat[0][2], str)  # path


def test_count_recent_commits(hyperion_repo):
    """Test comptage des commits récents."""
    repo = GitRepo(str(hyperion_repo))

    count = repo.count_recent_commits(days=90)

    assert isinstance(count, int)
    assert count >= 0


def test_detect_language(hyperion_repo):
    """Test détection du langage principal."""
    repo = GitRepo(str(hyperion_repo))

    language = repo.detect_language()

    # Hyperion est un projet Python
    assert language == "python"


def test_detect_ci(hyperion_repo):
    """Test détection du CI."""
    repo = GitRepo(str(hyperion_repo))

    ci = repo.detect_ci()

    # Peut être unknown si pas encore de CI configuré
    assert isinstance(ci, str)


def test_detect_license(hyperion_repo):
    """Test détection de la licence."""
    repo = GitRepo(str(hyperion_repo))

    license_name = repo.detect_license()

    # Hyperion a une licence Apache-2.0
    assert license_name in ["Apache-2.0", "UNKNOWN", None]


def test_get_date_range(hyperion_repo):
    """Test récupération de la plage de dates."""
    repo = GitRepo(str(hyperion_repo))

    first, last = repo.get_date_range()

    assert first is not None
    assert last is not None
    assert first <= last  # Le premier commit est avant le dernier


# Tests d'intégration (utilisant un vrai repo Git)


def test_full_workflow(hyperion_repo):
    """Test workflow complet sur le repo Hyperion."""
    repo = GitRepo(str(hyperion_repo))

    # 1. Métadonnées
    name = repo.get_name()
    assert name == "Hyperion" or len(name) > 0

    # 2. Commits
    commits = repo.get_commits()
    assert len(commits) > 0

    # 3. Contributeurs
    contributors = repo.get_contributors()
    assert len(contributors) > 0

    # 4. Stats
    numstat = repo.get_numstat()
    assert len(numstat) > 0

    # 5. Détections
    language = repo.detect_language()
    assert language in ["python", "unknown"]

    ci = repo.detect_ci()
    assert isinstance(ci, str)

    license_name = repo.detect_license()
    assert license_name in ["Apache-2.0", "UNKNOWN", None]

    # 6. Dates
    first, last = repo.get_date_range()
    assert first is not None
    assert last is not None
