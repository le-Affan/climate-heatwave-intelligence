"""Generate a reproducible SYNTHETIC daily maximum-temperature (Tmax) series.

This is NOT observed weather data. It exists only to exercise the prototype
pipeline. See data/SOURCE.md for the generation method.

Usage (from repo root):  python -m scripts.generate_data
"""
import argparse
import csv
import datetime as dt
import math
from pathlib import Path

import numpy as np

SEED = 42
START = dt.date(2015, 1, 1)
END = dt.date(2024, 12, 31)
OUT = Path("data/synthetic_tmax.csv")


def seasonal_mean(doy: int) -> float:
    """Annual cycle peaking around mid-May (day-of-year ~135)."""
    t = 2 * math.pi * (doy - 135) / 365.25
    return 33.0 + 5.0 * math.cos(t) + 1.5 * math.cos(2 * t)


def generate(seed: int = SEED) -> list[tuple[dt.date, float]]:
    rng = np.random.default_rng(seed)
    n_days = (END - START).days + 1
    dates = [START + dt.timedelta(days=i) for i in range(n_days)]

    # Day-to-day weather noise: AR(1) anomaly (phi=0.7, innovation sd=1.2 C).
    anomaly = np.zeros(n_days)
    for i in range(1, n_days):
        anomaly[i] = 0.7 * anomaly[i - 1] + rng.normal(0.0, 1.2)

    # Synthetic "heat spells": per year, Poisson(2) events between early April
    # and early June, 3-7 days long, +3 to +6 C peak, sine-shaped.
    spells = np.zeros(n_days)
    for year in range(START.year, END.year + 1):
        for _ in range(rng.poisson(2)):
            start = dt.date(year, 1, 1) + dt.timedelta(days=int(rng.integers(90, 160)))
            length = int(rng.integers(3, 8))
            peak = rng.uniform(3.0, 6.0)
            for k in range(length):
                idx = (start - START).days + k
                if 0 <= idx < n_days:
                    spells[idx] += peak * math.sin(math.pi * (k + 0.5) / length)

    rows = []
    for i, d in enumerate(dates):
        trend = 0.03 * (d.year - START.year)  # small warming trend, C per year
        tmax = seasonal_mean(d.timetuple().tm_yday) + trend + anomaly[i] + spells[i]
        rows.append((d, round(float(tmax), 1)))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    rows = generate(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "tmax_c"])
        for d, t in rows:
            writer.writerow([d.isoformat(), t])
    print(f"wrote {len(rows)} SYNTHETIC rows to {args.out} (seed={args.seed})")


if __name__ == "__main__":
    main()
