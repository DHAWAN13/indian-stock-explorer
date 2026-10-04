from datetime import datetime, timedelta, timezone

import pytest

from app.services.quote_freshness import get_quote_freshness


def test_recent_quote_is_fresh():
    now = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
    assert get_quote_freshness(now - timedelta(days=2), now) == "fresh"


def test_old_quote_is_stale():
    now = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
    assert get_quote_freshness(now - timedelta(days=6), now) == "stale"


def test_future_quote_is_stale():
    now = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
    assert get_quote_freshness(now + timedelta(minutes=10), now) == "stale"


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        get_quote_freshness(datetime(2026, 10, 5, 10, 0))