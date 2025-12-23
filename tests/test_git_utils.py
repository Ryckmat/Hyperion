"""Tests pour hyperion.utils.git_utils."""

import pytest

from hyperion.utils.git_utils import GitCommandError, GitRepo


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


def test_get_name_from_path(tmp_path):
    """Test get_name quand pas de remote (utilise nom du dossier)."""
    # Créer un repo Git temporaire sans remote
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    repo = GitRepo(str(repo_dir))
    assert repo.get_name() == "test_repo"


def test_detect_main_branch_with_origin_head(hyperion_repo):
    """Test détection branche principale avec origin/HEAD."""
    repo = GitRepo(str(hyperion_repo))
    branch = repo.detect_main_branch()
    assert branch in ["main", "master", "trunk", "develop"]


def test_detect_main_branch_custom_candidates(hyperion_repo):
    """Test avec candidats personnalisés."""
    repo = GitRepo(str(hyperion_repo))
    branch = repo.detect_main_branch(candidates=["main", "master"])
    assert branch in ["main", "master"]


def test_get_commits_with_since(hyperion_repo):
    """Test get_commits avec filtre since."""
    repo = GitRepo(str(hyperion_repo))

    # Tous les commits
    all_commits = repo.get_commits()

    # Commits récents seulement
    recent_commits = repo.get_commits(since="30.days")

    assert len(recent_commits) <= len(all_commits)


def test_get_numstat_parsing(hyperion_repo):
    """Test parsing des numstat."""
    repo = GitRepo(str(hyperion_repo))
    numstat = repo.get_numstat()

    # Vérifier le format
    for additions, deletions, path in numstat:
        assert isinstance(additions, int)
        assert isinstance(deletions, int)
        assert isinstance(path, str)
        assert additions >= 0
        assert deletions >= 0


def test_count_recent_commits_various_periods(hyperion_repo):
    """Test comptage commits sur différentes périodes."""
    repo = GitRepo(str(hyperion_repo))

    count_30 = repo.count_recent_commits(days=30)
    count_90 = repo.count_recent_commits(days=90)
    count_365 = repo.count_recent_commits(days=365)

    # Plus la période est longue, plus il y a de commits
    assert count_30 <= count_90 <= count_365


def test_detect_language_unknown(tmp_path):
    """Test détection langage pour repo sans fichiers."""
    # Créer un repo vide
    repo_dir = tmp_path / "empty_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    repo = GitRepo(str(repo_dir))
    language = repo.detect_language()
    assert language == "unknown"


def test_detect_ci_unknown(tmp_path):
    """Test détection CI pour repo sans CI."""
    # Créer un repo sans CI
    repo_dir = tmp_path / "no_ci_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    repo = GitRepo(str(repo_dir))
    ci = repo.detect_ci()
    assert ci == "unknown"


def test_detect_license_unknown(tmp_path):
    """Test détection license pour repo sans license."""
    # Créer un repo sans license
    repo_dir = tmp_path / "no_license_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    repo = GitRepo(str(repo_dir))
    license_name = repo.detect_license()
    assert license_name is None


def test_get_date_range_empty_repo(tmp_path):
    """Test get_date_range pour repo sans commits."""
    # Créer un repo vide
    repo_dir = tmp_path / "empty_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    repo = GitRepo(str(repo_dir))
    first, last = repo.get_date_range()
    # Repo vide = pas de dates
    assert first is None and last is None


def test_detect_license_mit(tmp_path):
    """Test détection licence MIT."""
    repo_dir = tmp_path / "mit_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    # Créer un fichier LICENSE avec MIT
    license_file = repo_dir / "LICENSE"
    license_file.write_text("MIT License\n\nCopyright (c) 2024\n")

    repo = GitRepo(str(repo_dir))
    assert repo.detect_license() == "MIT"


def test_detect_license_bsd(tmp_path):
    """Test détection licence BSD."""
    repo_dir = tmp_path / "bsd_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    license_file = repo_dir / "LICENSE"
    license_file.write_text(
        "BSD License\n\nRedistribution and use in source and binary forms\n"
    )

    repo = GitRepo(str(repo_dir))
    assert repo.detect_license() == "BSD-3-Clause"


def test_detect_license_gpl3(tmp_path):
    """Test détection licence GPL-3.0."""
    repo_dir = tmp_path / "gpl_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    license_file = repo_dir / "LICENSE"
    license_file.write_text("GNU General Public License version 3\n")

    repo = GitRepo(str(repo_dir))
    assert repo.detect_license() == "GPL-3.0"


def test_detect_license_gpl2(tmp_path):
    """Test détection licence GPL-2.0."""
    repo_dir = tmp_path / "gpl2_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    license_file = repo_dir / "LICENSE"
    license_file.write_text("GNU General Public License version 2\n")

    repo = GitRepo(str(repo_dir))
    assert repo.detect_license() == "GPL-2.0"


def test_detect_license_mpl(tmp_path):
    """Test détection licence MPL."""
    repo_dir = tmp_path / "mpl_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    license_file = repo_dir / "LICENSE"
    license_file.write_text("Mozilla Public License version 2.0\n")

    repo = GitRepo(str(repo_dir))
    assert repo.detect_license() == "MPL-2.0"


def test_detect_license_unknown_content(tmp_path):
    """Test détection licence inconnue."""
    repo_dir = tmp_path / "unknown_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    license_file = repo_dir / "LICENSE"
    license_file.write_text("Custom proprietary license\n")

    repo = GitRepo(str(repo_dir))
    assert repo.detect_license() == "UNKNOWN"


def test_detect_license_gpl_generic(tmp_path):
    """Test détection GPL sans version spécifique."""
    repo_dir = tmp_path / "gpl_generic_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    license_file = repo_dir / "LICENSE"
    license_file.write_text(
        "GNU General Public License\n\nThis program is free software\n"
    )

    repo = GitRepo(str(repo_dir))
    license_name = repo.detect_license()
    assert license_name in ["GPL", "GPL-3.0", "GPL-2.0"]


def test_get_remote_url_error_handling(hyperion_repo):
    """Test gestion d'erreur dans get_remote_url."""
    import unittest.mock as mock

    repo = GitRepo(str(hyperion_repo))

    # Mock _run_git pour lever une exception inattendue
    with mock.patch.object(
        repo, "_run_git", side_effect=RuntimeError("Unexpected error")
    ):
        # Ne doit pas crasher, retourne None
        result = repo.get_remote_url()
        assert result is None


def test_run_git_check_false(hyperion_repo):
    """Test _run_git avec check=False retourne [] sur erreur."""
    repo = GitRepo(str(hyperion_repo))

    # Commande invalide avec check=False
    result = repo._run_git("invalid-command", "args", check=False)
    # Doit retourner une liste (potentiellement vide)
    assert isinstance(result, list)


def test_detect_language_git_error(tmp_path):
    """Test detect_language quand git ls-files échoue."""
    import unittest.mock as mock

    repo_dir = tmp_path / "error_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    repo = GitRepo(str(repo_dir))

    # Mock _run_git pour lever une exception
    with mock.patch.object(repo, "_run_git", side_effect=RuntimeError("Git error")):
        language = repo.detect_language()
        assert language == "unknown"


def test_detect_license_read_error(tmp_path):
    """Test detect_license quand lecture fichier échoue."""
    import unittest.mock as mock

    repo_dir = tmp_path / "read_error_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    # Créer un fichier LICENSE
    license_file = repo_dir / "LICENSE"
    license_file.write_text("Some content")

    repo = GitRepo(str(repo_dir))

    # Mock read_text pour lever une exception
    with mock.patch(
        "pathlib.Path.read_text", side_effect=PermissionError("Access denied")
    ):
        # Doit continuer et retourner None (pas de crash)
        result = repo.detect_license()
        assert result is None


def test_detect_main_branch_exception_handling(tmp_path):
    """Test gestion exception dans detect_main_branch."""
    import unittest.mock as mock

    repo_dir = tmp_path / "exception_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    # Créer un commit initial
    test_file = repo_dir / "test.txt"
    test_file.write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    repo = GitRepo(str(repo_dir))

    # Mock _run_git pour lever une exception inattendue
    with mock.patch.object(repo, "_run_git", side_effect=RuntimeError("Git error")):
        # Ne doit pas crasher, fallback vers "main"
        branch = repo.detect_main_branch()
        assert branch == "main"


def test_get_commits_malformed_line(hyperion_repo):
    """Test get_commits ignore les lignes malformées."""
    import unittest.mock as mock

    repo = GitRepo(str(hyperion_repo))

    # Mock _run_git pour retourner une ligne malformée
    with mock.patch.object(
        repo,
        "_run_git",
        return_value=["malformed|line", "good|line|a|b|c|d|e|f|parents"],
    ):
        commits = repo.get_commits()
        # Seule la ligne bien formée doit être parsée
        assert len(commits) == 1


def test_get_numstat_malformed_lines(hyperion_repo):
    """Test get_numstat ignore les lignes malformées."""
    import unittest.mock as mock

    repo = GitRepo(str(hyperion_repo))

    # Mock _run_git pour retourner des lignes malformées
    with mock.patch.object(
        repo,
        "_run_git",
        return_value=[
            "",  # Ligne vide
            "malformed",  # Pas assez de parties
            "10\t5\tvalid.py",  # Ligne valide
        ],
    ):
        numstat = repo.get_numstat()
        # Seule la ligne valide doit être parsée
        assert len(numstat) == 1
        assert numstat[0] == (10, 5, "valid.py")


def test_get_numstat_binary_files(hyperion_repo):
    """Test get_numstat gère les fichiers binaires."""
    import unittest.mock as mock

    repo = GitRepo(str(hyperion_repo))

    # Mock _run_git pour retourner des stats avec fichiers binaires
    with mock.patch.object(
        repo,
        "_run_git",
        return_value=[
            "-\t-\tbinary.png",  # Fichier binaire
            "10\t5\ttext.py",  # Fichier texte
        ],
    ):
        numstat = repo.get_numstat()
        assert len(numstat) == 2
        # Fichier binaire doit avoir 0/0
        assert numstat[0] == (0, 0, "binary.png")
        assert numstat[1] == (10, 5, "text.py")


def test_get_numstat_invalid_numbers(hyperion_repo):
    """Test get_numstat gère les nombres invalides."""
    import unittest.mock as mock

    repo = GitRepo(str(hyperion_repo))

    # Mock _run_git pour retourner des stats avec nombres invalides
    with mock.patch.object(
        repo,
        "_run_git",
        return_value=[
            "abc\tdef\tinvalid.py",  # Nombres invalides
            "10\t5\tvalid.py",  # Ligne valide
        ],
    ):
        numstat = repo.get_numstat()
        assert len(numstat) == 2
        # Ligne invalide doit avoir 0/0
        assert numstat[0] == (0, 0, "invalid.py")
        assert numstat[1] == (10, 5, "valid.py")


def test_get_contributors_malformed_line(hyperion_repo):
    """Test get_contributors ignore les lignes malformées."""
    import unittest.mock as mock

    repo = GitRepo(str(hyperion_repo))

    # Mock _run_git pour retourner des lignes malformées
    with mock.patch.object(
        repo,
        "_run_git",
        return_value=["malformed line", "     5  John Doe <john@example.com>"],
    ):
        contributors = repo.get_contributors()
        # Seule la ligne bien formée doit être parsée
        assert len(contributors) == 1
        assert contributors[0]["name"] == "John Doe"
