"""Unit tests for the health endpoint."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from main import app


def test_health_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["platform"] == "i14y"
    assert "version" in data


def test_health_content_type():
    client = TestClient(app)
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
