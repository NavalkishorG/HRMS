from datetime import datetime, timedelta, timezone

from app.core.config import settings


def classify(worked_hours: float) -> tuple[bool, float]:
    half_day = worked_hours < settings.HALF_DAY_MIN_HOURS
    overtime = max(0.0, worked_hours - settings.FULL_DAY_HOURS)
    return half_day, overtime


def test_half_day_threshold():
    half_day, overtime = classify(3.5)
    assert half_day is True
    assert overtime == 0.0


def test_overtime_threshold():
    half_day, overtime = classify(10.0)
    assert half_day is False
    assert overtime == 2.0
