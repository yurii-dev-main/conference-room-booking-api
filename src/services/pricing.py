from collections.abc import Sequence
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal


class TariffWindow:
    def __init__(self, start_time: time, end_time: time, multiplier: Decimal) -> None:
        self.start_time = start_time
        self.end_time = end_time
        self.multiplier = multiplier


TARIFF_WINDOWS = [
    TariffWindow(time(6, 0), time(9, 0), Decimal("0.9")),
    TariffWindow(time(9, 0), time(12, 0), Decimal("1.0")),
    TariffWindow(time(12, 0), time(14, 0), Decimal("1.15")),
    TariffWindow(time(14, 0), time(18, 0), Decimal("1.0")),
    TariffWindow(time(18, 0), time(23, 0), Decimal("0.8")),
]


class PricingEngine:
    @staticmethod
    def calculate_room_cost(
        start_time: datetime,
        end_time: datetime,
        base_hourly_rate: Decimal,
    ) -> Decimal:
        """Calculate room rental cost by segmenting time interval.

        Segments the interval into tariff windows and applies hourly multipliers.
        """
        if end_time <= start_time:
            raise ValueError("end_time must be greater than start_time")

        current_date = start_time.date()
        end_date = end_time.date()
        total_cost = Decimal("0.0")

        # Iterate through all days spanning the booking interval
        while current_date <= end_date:
            for window in TARIFF_WINDOWS:
                window_start = datetime.combine(
                    current_date, window.start_time, tzinfo=start_time.tzinfo
                )
                window_end = datetime.combine(
                    current_date, window.end_time, tzinfo=start_time.tzinfo
                )

                overlap_start = max(start_time, window_start)
                overlap_end = min(end_time, window_end)

                if overlap_end > overlap_start:
                    duration_seconds = Decimal(
                        (overlap_end - overlap_start).total_seconds()
                    )
                    duration_hours = duration_seconds / Decimal("3600.0")
                    segment_cost = duration_hours * base_hourly_rate * window.multiplier
                    total_cost += segment_cost

            current_date += timedelta(days=1)

        return total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_total(
        cls,
        start_time: datetime,
        end_time: datetime,
        base_hourly_rate: Decimal,
        service_prices: Sequence[Decimal] = (),
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Calculate room cost, extra services total, and combined total price."""
        room_cost = cls.calculate_room_cost(start_time, end_time, base_hourly_rate)
        services_cost = sum(service_prices, Decimal("0.00")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_cost = (room_cost + services_cost).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return room_cost, services_cost, total_cost
