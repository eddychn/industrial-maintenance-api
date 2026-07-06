"""
health_service.py
-----------------
Business rules for classifying machine health.

The thresholds live here (and only here) so that if the manufacturing engineers
decide that "Warning" should start at 65 instead of 70, there is exactly one
line to change and every endpoint stays consistent.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Classification thresholds (health_score is on a 0-100 scale).
# ---------------------------------------------------------------------------
HEALTHY_THRESHOLD = 70.0   # score >= 70            -> Healthy
WARNING_THRESHOLD = 40.0   # 40 <= score < 70       -> Warning
#                            score < 40              -> Critical


def classify_health(health_score: float) -> str:
    """Map a numeric health score onto a human-readable condition.

    Args:
        health_score: machine condition from 0 (failed) to 100 (perfect).

    Returns:
        One of ``"Healthy"``, ``"Warning"`` or ``"Critical"``.
    """
    if health_score >= HEALTHY_THRESHOLD:
        return "Healthy"
    if health_score >= WARNING_THRESHOLD:
        return "Warning"
    return "Critical"
