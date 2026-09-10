"""
Integration Tests for FastAPI Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "simulation_status" in data

def test_models_endpoint():
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "active_model" in data
    assert "available_models" in data
    assert "Temporal Transformer" in data["available_models"]

def test_scenarios_endpoint():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert len(data["scenarios"]) >= 5

def test_forecast_latest_endpoint():
    response = client.get("/api/forecast/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "forecast" in data
    assert "trajectory" in data["forecast"]
    assert "traffic_telemetry" in data

def test_mitre_endpoint():
    response = client.get("/api/mitre")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["matrix"]) == 9

def test_replay_step():
    response = client.post("/api/replay/step")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stepped"
