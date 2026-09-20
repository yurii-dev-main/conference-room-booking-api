from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.services.pricing import PricingEngine


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 21, hour, minute, tzinfo=timezone.utc)


def test_pricing_standard_hours() -> None:
    start = dt(9, 0)
    end = dt(11, 0)
    cost = PricingEngine.calculate_room_cost(start, end, Decimal("1000.00"))
    assert cost == Decimal("2000.00")


def test_pricing_crossing_morning_to_standard() -> None:
    start = dt(8, 0)
    end = dt(10, 0)
    cost = PricingEngine.calculate_room_cost(start, end, Decimal("1000.00"))
    # 08:00-09:00 @ 0.9 (900) + 09:00-10:00 @ 1.0 (1000) = 1900.00
    assert cost == Decimal("1900.00")


def test_pricing_crossing_peak_hours() -> None:
    start = dt(11, 0)
    end = dt(13, 0)
    cost = PricingEngine.calculate_room_cost(start, end, Decimal("1000.00"))
    # 11:00-12:00 @ 1.0 (1000) + 12:00-13:00 @ 1.15 (1150) = 2150.00
    assert cost == Decimal("2150.00")


def test_pricing_crossing_into_evening_hours() -> None:
    start = dt(17, 0)
    end = dt(19, 0)
    cost = PricingEngine.calculate_room_cost(start, end, Decimal("1000.00"))
    # 17:00-18:00 @ 1.0 (1000) + 18:00-19:00 @ 0.8 (800) = 1800.00
    assert cost == Decimal("1800.00")


def test_pricing_with_service_prices() -> None:
    start = dt(10, 0)
    end = dt(12, 0)
    room_cost, services_cost, total = PricingEngine.calculate_total(
        start,
        end,
        Decimal("1000.00"),
        [Decimal("500.00"), Decimal("300.00")],
    )
    assert room_cost == Decimal("2000.00")
    assert services_cost == Decimal("800.00")
    assert total == Decimal("2800.00")


def test_pricing_sub_hour_fractional() -> None:
    start = dt(8, 30)
    end = dt(9, 30)
    cost = PricingEngine.calculate_room_cost(start, end, Decimal("1000.00"))
    # 0.5h * 1000 * 0.9 (450) + 0.5h * 1000 * 1.0 (500) = 950.00
    assert cost == Decimal("950.00")


def test_pricing_invalid_interval() -> None:
    with pytest.raises(ValueError):
        PricingEngine.calculate_room_cost(dt(11, 0), dt(10, 0), Decimal("1000.00"))
