import datetime as dt
import math

import pytest

from app.model import FEATURES, get_model
from app.risk import classify
from app.workload import run

DAY = dt.date(2024, 5, 10)


def test_model_file_matches_features():
    model = get_model()
    assert len(model.coef) == len(FEATURES)
    assert model.meta["data_is_synthetic"] is True


def test_forecast_is_finite_and_deterministic():
    model = get_model()
    a = model.predict([40.0] * 7, DAY)
    assert math.isfinite(a)
    assert a == model.predict([40.0] * 7, DAY)


def test_hotter_history_gives_hotter_forecast():
    model = get_model()
    assert model.predict([43.0] * 7, DAY) > model.predict([33.0] * 7, DAY)


def test_wrong_history_length_rejected():
    with pytest.raises(ValueError):
        get_model().predict([40.0] * 6, DAY)


@pytest.mark.parametrize(
    "tmax,level",
    [(30.0, "NORMAL"), (36.9, "NORMAL"), (37.0, "CAUTION"), (40.0, "HIGH"), (44.9, "HIGH"), (45.0, "SEVERE")],
)
def test_demo_thresholds(tmax, level):
    assert classify(tmax) == level


def test_workload_is_deterministic():
    a, b = run(200, seed=7), run(200, seed=7)
    assert a["checksum"] == b["checksum"]
    assert a["risk_counts"] == b["risk_counts"]
    assert sum(a["risk_counts"].values()) == 200
