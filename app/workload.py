"""Deterministic batch workload for resource measurements (Experiments 7 and 8).

Runs N predictions through the same validation + predict path as POST /predict
(without HTTP). Same --n and --seed => identical inputs and identical checksum.

Elapsed time covers input generation + validation + prediction + risk classification.

Usage:  python -m app.workload --n 200000 --seed 42
"""
import argparse
import datetime as dt
import hashlib
import json
import time
from collections import Counter

import numpy as np

from app.main import PredictRequest, predict

BASE_DATE = dt.date(2023, 1, 1)
CHUNK = 10000  # inputs generated in fixed-size chunks so memory stays flat for large N


def make_inputs(n: int, seed: int):
    """Yield n deterministic request dicts (synthetic Tmax histories, 25-47 C)."""
    rng = np.random.default_rng(seed)
    for done in range(0, n, CHUNK):
        size = min(CHUNK, n - done)
        offsets = rng.integers(0, 730, size=size)
        temps = np.round(rng.uniform(25.0, 47.0, size=(size, 7)), 1)
        for o, t in zip(offsets, temps):
            yield {"last_date": (BASE_DATE + dt.timedelta(days=int(o))).isoformat(), "recent_tmax_c": t.tolist()}


def run(n: int, seed: int) -> dict:
    digest = hashlib.sha256()
    levels = Counter()

    start = time.perf_counter()
    for item in make_inputs(n, seed):
        res = predict(PredictRequest(**item))
        digest.update(f"{res.forecast_tmax_c}:{res.risk_level};".encode())
        levels[res.risk_level] += 1
    elapsed = time.perf_counter() - start

    return {
        "n": n,
        "seed": seed,
        "elapsed_s": round(elapsed, 4),
        "throughput_per_s": round(n / elapsed, 1),
        "checksum": digest.hexdigest()[:16],
        "risk_counts": dict(sorted(levels.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(run(args.n, args.seed)))


if __name__ == "__main__":
    main()
