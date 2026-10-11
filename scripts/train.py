"""Train the linear-regression forecaster and evaluate it against a persistence
baseline on a chronological held-out test set. Writes model/model.json.

Usage (from repo root):  python -m scripts.train
"""
import csv
import datetime as dt
import json
from pathlib import Path

import numpy as np

from app.model import FEATURES, N_LAGS, build_features
from app.risk import classify

DATA = Path("data/synthetic_tmax.csv")
OUT = Path("model/model.json")
TEST_START = dt.date(2023, 1, 1)  # train: target dates before 2023; test: 2023-2024


def load(path: Path) -> tuple[list[dt.date], list[float]]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return [dt.date.fromisoformat(r["date"]) for r in rows], [float(r["tmax_c"]) for r in rows]


def metrics(pred: np.ndarray, actual: np.ndarray) -> dict:
    err = pred - actual
    level_acc = np.mean([classify(p) == classify(a) for p, a in zip(pred, actual)])
    return {
        "mae_c": round(float(np.mean(np.abs(err))), 3),
        "rmse_c": round(float(np.sqrt(np.mean(err**2))), 3),
        "risk_level_accuracy": round(float(level_acc), 3),
    }


def main() -> None:
    dates, tmax = load(DATA)
    X, y, persist, target_dates = [], [], [], []
    for i in range(N_LAGS, len(tmax)):
        recent = tmax[i - N_LAGS : i]
        X.append(build_features(recent, dates[i - 1]))
        y.append(tmax[i])
        persist.append(recent[-1])
        target_dates.append(dates[i])
    X, y, persist = np.array(X), np.array(y), np.array(persist)
    is_test = np.array([d >= TEST_START for d in target_dates])

    coef, *_ = np.linalg.lstsq(X[~is_test], y[~is_test], rcond=None)
    model_pred = X[is_test] @ coef

    result = {
        "model": "linear_regression_least_squares",
        "features": FEATURES,
        "coefficients": [round(float(c), 6) for c in coef],
        "data_file": str(DATA),
        "data_is_synthetic": True,
        "train_period": f"{target_dates[0]} .. {TEST_START - dt.timedelta(days=1)}",
        "test_period": f"{TEST_START} .. {target_dates[-1]}",
        "n_train": int((~is_test).sum()),
        "n_test": int(is_test.sum()),
        "test_metrics": {
            "linear_regression": metrics(model_pred, y[is_test]),
            "persistence_baseline": metrics(persist[is_test], y[is_test]),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("n_train", "n_test", "test_metrics")}, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
