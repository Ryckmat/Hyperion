from fastapi.testclient import TestClient
import yaml
import hyperion.api.main as api_main


def test_list_repos_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "DATA_DIR", tmp_path)
    client = TestClient(api_main.app)
    r = client.get("/api/repos")
    assert r.status_code == 200
    assert r.json()["repos"] == []


def test_list_repos_with_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "DATA_DIR", tmp_path)

    repo_dir = tmp_path / "repositories" / "requests"
    repo_dir.mkdir(parents=True)

    profile = {
        "service": "requests",
        "repositories": [{"main_language": "Python", "license": "Apache-2.0"}],
        "git_summary": {
            "commits": 123,
            "contributors": 4,
            "first_commit": "2020-01-01",
            "last_commit": "2025-12-22",
            "contributors_top10": [{"name": "a", "commits": 10}],
            "hotspots_top10": [{"path": "x.py", "changes": 3}],
        },
        "metrics": {"dummy": True},
    }

    with open(repo_dir / "profile.yaml", "w") as f:
        yaml.safe_dump(profile, f)

    client = TestClient(api_main.app)
    r = client.get("/api/repos")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["repos"][0]["name"] == "requests"


def test_get_repo_404(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "DATA_DIR", tmp_path)
    client = TestClient(api_main.app)
    r = client.get("/api/repos/unknown")
    assert r.status_code == 404
