import pytest
from fastapi.testclient import TestClient
from rag_agent import app
from rag.dependencies import state

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_endpoint_missing_query():
    response = client.post("/chat", json={"language": "en"})
    assert response.status_code == 422  # Validation error

def test_chat_endpoint_mocked_response(monkeypatch):
    # This is a conceptual test showing how to mock the app_state
    # to avoid loading real models during unit tests.
    
    async def mock_ask(query, app_state, session):
        return {
            "status": "ok",
            "answer": "Mocked answer",
            "sources": []
        }, session
    
    import rag_agent
    monkeypatch.setattr(rag_agent, "ask", mock_ask)
    
    response = client.post("/chat", json={"query": "Test query"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Mocked answer"

