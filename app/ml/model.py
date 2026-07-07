"""
model.py
--------
Predictive-maintenance machine-learning model (scikit-learn).

What it does
------------
Given a machine's ``operating_hours``, ``health_score`` and age, it estimates the
probability that the machine will need maintenance soon ("failure risk"), and
turns that into a human-readable risk level and recommended action.

About the training data (important, and documented honestly)
------------------------------------------------------------
A real deployment would train this model on **historical sensor and maintenance
logs** collected from the factory floor. For this portfolio project we do not
have years of real machine history, so we generate **realistic synthetic data**
whose statistical relationships mirror how machines actually degrade:

    * more operating hours            -> higher failure risk
    * lower health score              -> higher failure risk
    * older machines                  -> higher failure risk

The model then *learns* these relationships from the synthetic data and produces
genuine probability predictions. Training on synthetic data is a standard,
accepted approach for demonstrating an ML pipeline when real data is unavailable.

Design notes
------------
* The model is trained lazily on first use and cached in memory (``lru_cache``),
  so there is no binary model file to commit and no repeated retraining.
* ``random_state`` is fixed so predictions are deterministic and reproducible.
* Training a RandomForest on a few thousand synthetic rows takes well under a
  second, so lazy training adds no meaningful latency.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Fixed seed -> reproducible training data and predictions.
RANDOM_STATE = 42

# The three numeric features the model is trained on.
FEATURE_NAMES = ["operating_hours", "health_score", "machine_age_days"]

# Risk thresholds (probability of needing maintenance soon).
HIGH_RISK = 0.70
MEDIUM_RISK = 0.40


def _generate_training_data(
    n_samples: int = 4000, seed: int = RANDOM_STATE
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic (features, label) training data.

    The label is 1 = "will need maintenance soon", 0 = "healthy for now". It is
    drawn from a latent probability that increases with operating hours and age
    and decreases with health score -- the real-world degradation pattern.
    """
    rng = np.random.default_rng(seed)

    operating_hours = rng.uniform(0, 60_000, n_samples)
    health_score = rng.uniform(0, 100, n_samples)
    machine_age_days = rng.uniform(0, 4_000, n_samples)

    # Latent linear score -> squashed to a 0..1 probability with a sigmoid.
    latent = (
        (operating_hours / 60_000) * 2.5
        + (machine_age_days / 4_000) * 1.5
        - (health_score / 100) * 4.0
        - 0.5
    )
    probability = 1.0 / (1.0 + np.exp(-latent))
    labels = (rng.uniform(0, 1, n_samples) < probability).astype(int)

    features = np.column_stack([operating_hours, health_score, machine_age_days])
    return features, labels


@lru_cache(maxsize=1)
def _get_model() -> Pipeline:
    """Train (once) and cache the predictive-maintenance model.

    ``lru_cache`` guarantees the model is trained a single time per process and
    then reused for every prediction.
    """
    features, labels = _generate_training_data()
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=120,
                    max_depth=8,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    model.fit(features, labels)
    return model


def _risk_level(risk: float) -> str:
    """Map a 0..1 probability to Low / Medium / High."""
    if risk >= HIGH_RISK:
        return "High"
    if risk >= MEDIUM_RISK:
        return "Medium"
    return "Low"


def _recommendation(risk: float, status: Optional[str]) -> str:
    """Turn the risk into a concrete, human-readable recommended action."""
    if status == "Maintenance":
        return "Machine is already under maintenance — complete the open ticket."
    if risk >= HIGH_RISK:
        return "High risk — schedule maintenance immediately."
    if risk >= MEDIUM_RISK:
        return "Medium risk — plan maintenance within the next cycle."
    return "Low risk — no immediate action needed; keep monitoring."


def predict_failure_risk(
    operating_hours: float,
    health_score: float,
    installation_date: date,
    status: Optional[str] = None,
) -> dict:
    """Predict a machine's maintenance failure risk.

    Args:
        operating_hours: cumulative hours the machine has run.
        health_score: current condition 0 (failed) .. 100 (perfect).
        installation_date: when the machine was installed (used to derive age).
        status: optional current machine status (e.g. "Maintenance").

    Returns:
        A dict with ``failure_risk`` (percent 0..100), ``risk_level``
        (Low/Medium/High), ``recommendation`` and ``machine_age_days``.
    """
    machine_age_days = max((date.today() - installation_date).days, 0)

    features = np.array(
        [[operating_hours, health_score, machine_age_days]], dtype=float
    )
    model = _get_model()

    # predict_proba returns [P(no maintenance), P(maintenance soon)].
    risk = float(model.predict_proba(features)[0][1])

    return {
        "failure_risk": round(risk * 100, 1),
        "risk_level": _risk_level(risk),
        "recommendation": _recommendation(risk, status),
        "machine_age_days": int(machine_age_days),
    }
