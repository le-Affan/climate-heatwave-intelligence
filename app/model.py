"""Next-day Tmax forecast: linear regression on the last 7 days + seasonality."""
import datetime as dt
import json
import math
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

N_LAGS = 7
FEATURES = ["intercept"] + [f"tmax_d-{N_LAGS - 1 - i}" for i in range(N_LAGS)] + ["sin_doy", "cos_doy"]
MODEL_PATH = Path(os.environ.get("MODEL_PATH", Path(__file__).resolve().parent.parent / "model" / "model.json"))


def build_features(recent_tmax: list[float], last_date: dt.date) -> np.ndarray:
    """recent_tmax: 7 daily values, oldest first; last_date: date of the newest value."""
    if len(recent_tmax) != N_LAGS:
        raise ValueError(f"expected {N_LAGS} values, got {len(recent_tmax)}")
    target = last_date + dt.timedelta(days=1)
    angle = 2 * math.pi * target.timetuple().tm_yday / 365.25
    return np.array([1.0, *recent_tmax, math.sin(angle), math.cos(angle)])


class LinearModel:
    def __init__(self, coefficients: list[float], meta: dict):
        self.coef = np.asarray(coefficients, dtype=float)
        self.meta = meta

    def predict(self, recent_tmax: list[float], last_date: dt.date) -> float:
        return float(build_features(recent_tmax, last_date) @ self.coef)


@lru_cache(maxsize=1)
def get_model() -> LinearModel:
    meta = json.loads(MODEL_PATH.read_text())
    return LinearModel(meta["coefficients"], meta)
