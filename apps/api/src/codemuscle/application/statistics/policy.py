from datetime import date


def classify_area(
    *,
    total_attempts: int,
    independent_success_rate: float,
    failed_attempt_rate: float,
    last_practiced_date: date | None,
    recent_success_rate: float | None,
    older_success_rate: float | None,
    today: date,
) -> tuple[str, list[str]]:
    if last_practiced_date is None:
        return "NEGLECTED", ["No practice attempts recorded"]
    inactive_days = (today - last_practiced_date).days
    if inactive_days >= 30:
        return "NEGLECTED", [f"Not practiced for {inactive_days} days"]
    reasons: list[str] = []
    if total_attempts >= 3 and independent_success_rate < 0.5:
        reasons.append("Independent success rate is below 50%")
    if total_attempts >= 3 and failed_attempt_rate >= 0.35:
        reasons.append("Failed attempt rate is at least 35%")
    if reasons:
        return "WEAK", reasons
    if (
        total_attempts >= 4
        and recent_success_rate is not None
        and older_success_rate is not None
        and recent_success_rate >= older_success_rate + 0.2
    ):
        return "IMPROVING", ["Recent success rate improved by at least 20 percentage points"]
    return "STABLE", ["Practice and success rates are within stable thresholds"]


def trend_label(recent_success_rate: float | None, older_success_rate: float | None) -> str:
    if recent_success_rate is None or older_success_rate is None:
        return "INSUFFICIENT_DATA"
    difference = recent_success_rate - older_success_rate
    if difference >= 0.2:
        return "IMPROVING"
    if difference <= -0.2:
        return "DECLINING"
    return "STEADY"
