# Data source: SYNTHETIC

`synthetic_tmax.csv` is **synthetic (generated) data**. It is **not** observed weather data from IMD
or any other source, and does not describe any real location. It exists only to show the prototype
pipeline working (data → model → API → container → Kubernetes → benchmarks).

## Generation

Script: `scripts/generate_data.py`. Run it from the repo root with `python -m scripts.generate_data`.
The default seed is 42, and it uses the numpy `default_rng` generator.

The script builds one daily maximum temperature (Tmax, °C) per day from 2015-01-01 to
2024-12-31. Each value is the sum of five parts:

| Component | Definition |
|---|---|
| Seasonal mean | `33 + 5·cos(2π(doy−135)/365.25) + 1.5·cos(4π(doy−135)/365.25)`, which peaks around mid-May |
| Warming trend | +0.03 °C per year since 2015 |
| Daily noise | AR(1) anomaly: `a[t] = 0.7·a[t−1] + N(0, 1.2²)` |
| Heat spells | Each year has Poisson(2) events that start on day-of-year 90–159. Each lasts 3–7 days and has a sine-shaped bump peaking at +3 to +6 °C |
| Rounding | 0.1 °C |

All of these parameters were chosen by hand to look plausible. They were **not** fitted to real
observations.

## File summary (measured from the generated file)

- Columns: `date` (ISO), `tmax_c`
- 3653 rows, 2015-01-01 to 2024-12-31
- Mean 33.15 °C, min 24.8 °C, max 49.1 °C
- Days ≥ 37 °C: 809. Days ≥ 40 °C: 252. Days ≥ 45 °C: 8
- SHA-256 (seed 42): `51fea34a1eca4761341aaf13117586e3ef49e9a6a121779df7be68d4e556d682`

## Relation to the use case

The use case (KJS-CES-01) names the IMD Pune gridded Tmax data (GRD files: timestamp, latitude,
longitude, Tmax) as its real data source. This prototype does not use that data. To switch to real
data, replace this CSV with a `date,tmax_c` series for one grid cell or station, then retrain with
`python -m scripts.train`.
