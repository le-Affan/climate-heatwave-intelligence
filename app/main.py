"""Heatwave prediction prototype API (KJS-CES-01)."""
import datetime as dt
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.model import N_LAGS, get_model
from app.risk import ADVISORIES, DISCLAIMER, classify

Tmax = Annotated[float, Field(ge=-10.0, le=60.0)]


class PredictRequest(BaseModel):
    location: str | None = Field(default=None, max_length=64)
    last_date: dt.date = Field(description="Date of the newest value in recent_tmax_c")
    recent_tmax_c: list[Tmax] = Field(
        min_length=N_LAGS, max_length=N_LAGS, description="Last 7 daily max temperatures in C, oldest first"
    )


class PredictResponse(BaseModel):
    location: str | None
    forecast_date: dt.date
    forecast_tmax_c: float
    risk_level: str
    advisory: str
    disclaimer: str


app = FastAPI(title="Heatwave Prediction Prototype (KJS-CES-01)", version="0.1.0")


def predict(req: PredictRequest) -> PredictResponse:
    forecast = round(get_model().predict(req.recent_tmax_c, req.last_date), 1)
    level = classify(forecast)
    return PredictResponse(
        location=req.location,
        forecast_date=req.last_date + dt.timedelta(days=1),
        forecast_tmax_c=forecast,
        risk_level=level,
        advisory=ADVISORIES[level],
        disclaimer=DISCLAIMER,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": get_model().meta["model"]}


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(req: PredictRequest) -> PredictResponse:
    return predict(req)
