from fastapi.testclient import TestClient
import hyperion.api.main as api_main


class FakeEngine:
    def chat(self, question: str, repo=None, history=None):
        return {"answer": f"echo:{question}", "sources": []}


def test_health_smoke(monkeypatch):
    # Neo4j optionnel: on force un faux ingester si présent
    class FakeDriver:
        def verify_connectivity(self):  # noqa
            return True

    class FakeIngester:
        def __init__(self):  # noqa
            self.driver = FakeDriver()

        def close(self):  # noqa
            return None

    monkeypatch.setattr(api_main, "Neo4jIngester", FakeIngester, raising=False)
    monkeypatch.setattr(api_main, "get_query_engine", lambda: FakeEngine())

    client = TestClient(api_main.app)
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "api" in data
    assert "neo4j" in data
    assert "rag" in data


def test_root_smoke():
    client = TestClient(api_main.app)
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Hyperion API"
    assert "endpoints" in data


def test_chat_smoke(monkeypatch):
    monkeypatch.setattr(api_main, "get_query_engine", lambda: FakeEngine())

    client = TestClient(api_main.app)
    r = client.post("/api/chat", json={"question": "hello"})
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "echo:hello"
