"""DEMO heat-risk levels and advisory templates.

The thresholds below are DEMONSTRATION values chosen for this prototype.
They are NOT official IMD heatwave criteria and must not be used as such.
"""

# (lower bound in C, level) -- checked from highest to lowest.
DEMO_THRESHOLDS = [
    (45.0, "SEVERE"),
    (40.0, "HIGH"),
    (37.0, "CAUTION"),
    (float("-inf"), "NORMAL"),
]

ADVISORIES = {
    "NORMAL": "No elevated heat risk expected. Routine precautions only.",
    "CAUTION": "Warm day expected. Stay hydrated and limit strenuous outdoor activity at midday.",
    "HIGH": "High heat risk expected. Avoid outdoor work 12:00-16:00, drink water often, check on elderly and children.",
    "SEVERE": "Severe heat risk expected. Stay indoors during peak hours, seek medical help for heat-illness symptoms.",
}

DISCLAIMER = (
    "DEMO prototype output from a model trained on SYNTHETIC data. "
    "Risk levels use demo thresholds, not official IMD criteria. "
    "Not an official forecast or warning."
)


def classify(tmax_c: float) -> str:
    for lower, level in DEMO_THRESHOLDS:
        if tmax_c >= lower:
            return level
    return "NORMAL"
