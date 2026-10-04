from datetime import datetime, timedelta, timezone

MAX_QUOTE_AGE = timedelta(days=5)
MAX_FUTURE_SKEW = timedelta(minutes=5)


def get_quote_freshness(
    as_of: datetime,
    now: datetime | None = None,
) -> str:
    """Allow five calendar days for weekends and market holidays."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("Quote timestamp must include a timezone.")

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("Current time must include a timezone.")

    age = (
        current_time.astimezone(timezone.utc)
        - as_of.astimezone(timezone.utc)
    )

    if age > MAX_QUOTE_AGE or age < -MAX_FUTURE_SKEW:
        return "stale"

    return "fresh"