from fastapi.testclient import TestClient

from app.main import app
from app.risk import DEMO_THRESHOLDS

client = TestClient(app)
LEVELS = {level for _, level in DEMO_THRESHOLDS}
VALID = {"location": "demo-site", "last_date": "2024-05-10", "recent_tmax_c": [38.1, 38.9, 39.4, 40.2, 41.0, 41.6, 42.3]}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_predict_valid():
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200
    body = r.json()
    assert body["forecast_date"] == "2024-05-11"
    assert -10 <= body["forecast_tmax_c"] <= 60
    assert body["risk_level"] in LEVELS
    assert body["advisory"]
    assert "DEMO" in body["disclaimer"] and "SYNTHETIC" in body["disclaimer"]


def test_predict_too_few_values():
    r = client.post("/predict", json={**VALID, "recent_tmax_c": [40.0] * 6})
    assert r.status_code == 422


def test_predict_out_of_range_value():
    r = client.post("/predict", json={**VALID, "recent_tmax_c": [40.0] * 6 + [99.0]})
    assert r.status_code == 422


def test_predict_non_numeric_value():
    r = client.post("/predict", json={**VALID, "recent_tmax_c": [40.0] * 6 + ["hot"]})
    assert r.status_code == 422


def test_predict_bad_date():
    r = client.post("/predict", json={**VALID, "last_date": "2024-13-45"})
    assert r.status_code == 422


def test_predict_missing_field():
    r = client.post("/predict", json={"recent_tmax_c": [40.0] * 7})
    assert r.status_code == 422
