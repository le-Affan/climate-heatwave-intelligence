# Heatwave Prediction Prototype (KJS-CES-01)

This is a Cloud Computing mini-project prototype for the use case *Climate Intelligence for Heatwave
Monitoring, Prediction, and Early Warning*. You give it the last 7 days of maximum temperature. It
forecasts tomorrow's maximum temperature, assigns a **demo** heat-risk level and returns a template
advisory as JSON.

> **Educational prototype.** It is trained on **synthetic** data and uses **demo** thresholds that are
> not official IMD criteria. It is not an operational forecast or warning system.

## Layout

```
app/main.py           FastAPI service: GET /health, POST /predict
app/model.py          Feature builder + linear model loader
app/risk.py           DEMO risk thresholds, advisory templates, disclaimer
app/workload.py       Deterministic batch workload (for Experiments 7/8)
scripts/generate_data.py  Synthetic data generator (seeded)
scripts/train.py      Train + evaluate vs persistence baseline -> model/model.json
data/synthetic_tmax.csv, data/SOURCE.md
model/model.json      Coefficients + held-out test metrics (written by train.py)
tests/                pytest: API (valid/invalid input, health) + model/threshold/workload
```

## Run (Python 3.12 inside Docker, nothing installed on the host)

From the repo root:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work:z -w /work python:3.12-slim sh -c '
  pip install --user -q -r requirements-dev.txt
  python -m scripts.generate_data   # regenerate synthetic data (seed 42)
  python -m scripts.train           # retrain + print test metrics
  python -m pytest -v               # run tests
  python -m app.workload --n 200000 --seed 42'
```

To serve the API, run this and then open http://localhost:8000/docs:

```bash
docker run --rm -p 8000:8000 -v "$PWD":/work:z -w /work python:3.12-slim sh -c '
  pip install -q -r requirements.txt && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

Example request:

```bash
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"location":"demo-site","last_date":"2024-05-10","recent_tmax_c":[38.1,38.9,39.4,40.2,41.0,41.6,42.3]}'
```

`recent_tmax_c` must hold exactly 7 numbers between −10 and 60 °C, oldest first. `last_date` is the
date of the newest value. Any other input returns HTTP 422 with a validation message.

## Model

- **Forecast:** least-squares linear regression for next-day Tmax. The features are the last 7 daily
  Tmax values plus sin/cos of the forecast day-of-year, and the coefficients are in `model/model.json`.
- **Baseline:** persistence (tomorrow = today).
- **Evaluation:** chronological split. Training uses target days 2015-01-08 to 2022-12-31 (2915
  samples) and testing uses 2023–2024 (731 samples). Run `python -m scripts.train` to reproduce.

Results from the current `model/model.json` (synthetic test set, seed 42):

| Method | MAE (°C) | RMSE (°C) | Risk-level match |
|---|---|---|---|
| Linear regression | 0.987 | 1.237 | 0.880 |
| Persistence baseline | 1.052 | 1.311 | 0.893 |

The regression is slightly better than persistence on MAE and RMSE. It is slightly worse at matching
the demo risk level. Because the data is synthetic, these numbers show the pipeline works. They say
**nothing** about real-world forecasting skill.

## Demo risk levels (not official)

| Forecast Tmax | Level |
|---|---|
| < 37 °C | NORMAL |
| 37–39.9 °C | CAUTION |
| 40–44.9 °C | HIGH |
| ≥ 45 °C | SEVERE |

## Benchmark workload

`python -m app.workload --n N --seed S` sends N seeded inputs through the same validation and
prediction path as `POST /predict`, without HTTP. It prints elapsed time, throughput, a checksum and
the risk counts. The same N and S always give the same checksum, so runs can be compared. The
workload is single-threaded.

## Limitations

- The data is synthetic. Model metrics do not reflect real climate skill.
- It covers one series and one location. There are no spatial, regional or hotspot analytics, and no
  IMD GRD ingestion.
- The forecast horizon is next-day only. The model is linear, with no uncertainty estimate.
- Risk thresholds are demo values, not official IMD heatwave criteria (IMD criteria also depend on
  departure from normal, which is not modelled).
- Advisories are fixed templates (no LLM). There is no human-in-the-loop approval step.
- There is no authentication or rate limiting. The API stores no data and handles no personal data.
