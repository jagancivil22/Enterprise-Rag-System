import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login():
    response = client.post("/auth/login", json={"username": "alice", "password": "secret"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_ingest_and_query():
    # Login as admin
    login_resp = client.post("/auth/login", json={"username": "alice", "password": "secret"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Ingest a small text file
    files = {"file": ("test.txt", b"Q3 revenue is $10M", "text/plain")}
    data = {"allowed_roles": "admin,analyst"}
    ingest_resp = client.post("/ingest", headers=headers, files=files, data=data)
    assert ingest_resp.status_code == 200
    
    # Query as analyst (alice has analyst role)
    query_resp = client.post("/query", headers=headers, json={"question": "What is Q3 revenue?"})
    assert query_resp.status_code == 200
    assert "10M" in query_resp.json()["answer"]