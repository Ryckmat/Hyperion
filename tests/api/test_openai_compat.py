from fastapi.testclient import TestClient

import hyperion.api.main as api_main
import hyperion.api.openai_compat as oai


class FakeEngine:
    def chat(self, question: str, repo=None, history=None):
        return {"answer": f"echo:{question}", "sources": []}


def test_models():
    client = TestClient(api_main.app)
    r = client.get("/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "list"
    assert data["data"][0]["id"] == "hyperion-rag"


def test_chat_completions_smoke(monkeypatch):
    # IMPORTANT: openai_compat a importé get_query_engine depuis api.main
    monkeypatch.setattr(api_main, "get_query_engine", lambda: FakeEngine())
    monkeypatch.setattr(oai, "get_query_engine", lambda: FakeEngine())

    client = TestClient(api_main.app)
    payload = {
        "model": "hyperion-rag",
        "messages": [{"role": "user", "content": "ping"}],
        "stream": False,
    }
    r = client.post("/v1/chat/completions", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "echo:ping"


def test_chat_completions_requires_messages():
    client = TestClient(api_main.app)
    r = client.post("/v1/chat/completions", json={"messages": []})
    assert r.status_code in (400, 422)
