from datetime import date, datetime, time, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Booking, BookingStatus, Room, Service
from src.schemas.reports import (
    OccupancyReportResponse,
    PopularServiceItem,
    PopularServicesResponse,
    RevenueReportResponse,
    RoomOccupancy,
)


class ReportsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_occupancy_report(
        self, start_date: date, end_date: date
    ) -> OccupancyReportResponse:
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be greater than or equal to start_date",
            )

        days_count = (end_date - start_date).days + 1
        operating_hours_per_day = Decimal("17.0")  # Working hours: 06:00 to 23:00
        total_available_hours = (
            operating_hours_per_day * Decimal(days_count)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        range_start = datetime.combine(start_date, time(0, 0), tzinfo=timezone.utc)
        range_end = datetime.combine(
            end_date, time(23, 59, 59, 999999), tzinfo=timezone.utc
        )

        rooms_stmt = select(Room).where(Room.is_active.is_(True)).order_by(Room.id)
        rooms = (await self.session.execute(rooms_stmt)).scalars().all()

        room_occupancies: list[RoomOccupancy] = []

        for room in rooms:
            # Query confirmed bookings overlapping the requested date range
            bookings_stmt = select(Booking).where(
                Booking.room_id == room.id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.start_time <= range_end,
                Booking.end_time >= range_start,
            )
            bookings = (await self.session.execute(bookings_stmt)).scalars().all()

            total_seconds = Decimal("0.0")
            for b in bookings:
                b_start = (
                    b.start_time
                    if b.start_time.tzinfo is not None
                    else b.start_time.replace(tzinfo=timezone.utc)
                )
                b_end = (
                    b.end_time
                    if b.end_time.tzinfo is not None
                    else b.end_time.replace(tzinfo=timezone.utc)
                )
                overlap_start = max(b_start, range_start)
                overlap_end = min(b_end, range_end)
                if overlap_end > overlap_start:
                    total_seconds += Decimal(
                        (overlap_end - overlap_start).total_seconds()
                    )

            booked_hours = (total_seconds / Decimal("3600.0")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Formula: (total_booked_hours /
            #           (operating_hours_per_day * days_count)) * 100
            if total_available_hours > Decimal("0"):
                occupancy_rate = (
                    (booked_hours / total_available_hours) * Decimal("100.0")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                occupancy_rate = Decimal("0.00")

            room_occupancies.append(
                RoomOccupancy(
                    room_id=room.id,
                    room_name=room.name,
                    total_booked_hours=booked_hours,
                    available_hours=total_available_hours,
                    occupancy_rate_pct=occupancy_rate,
                )
            )

        return OccupancyReportResponse(
            start_date=start_date,
            end_date=end_date,
            days_count=days_count,
            rooms=room_occupancies,
        )

    async def get_revenue_report(
        self, start_date: date, end_date: date
    ) -> RevenueReportResponse:
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be greater than or equal to start_date",
            )

        range_start = datetime.combine(start_date, time(0, 0), tzinfo=timezone.utc)
        range_end = datetime.combine(
            end_date, time(23, 59, 59, 999999), tzinfo=timezone.utc
        )

        # SQL aggregation for total revenue in selected range
        total_stmt = select(
            func.coalesce(func.sum(Booking.total_price), Decimal("0.00"))
        ).where(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time >= range_start,
            Booking.start_time <= range_end,
        )
        total_revenue = (await self.session.execute(total_stmt)).scalar_one()

        bookings_stmt = select(Booking).where(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time >= range_start,
            Booking.start_time <= range_end,
        )
        bookings = (await self.session.execute(bookings_stmt)).scalars().all()

        services_revenue = Decimal("0.00")
        for b in bookings:
            for s in b.services_snapshot:
                services_revenue += Decimal(str(s.get("price", "0.00")))

        services_revenue = services_revenue.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_revenue = Decimal(str(total_revenue)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        rooms_revenue = (total_revenue - services_revenue).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return RevenueReportResponse(
            start_date=start_date,
            end_date=end_date,
            total_revenue=total_revenue,
            rooms_revenue=rooms_revenue,
            services_revenue=services_revenue,
        )

    async def get_popular_services_report(self) -> PopularServicesResponse:
        services_stmt = select(Service).order_by(Service.id)
        services = (await self.session.execute(services_stmt)).scalars().all()

        bookings_stmt = select(Booking).where(Booking.status == BookingStatus.CONFIRMED)
        bookings = (await self.session.execute(bookings_stmt)).scalars().all()

        stats: dict[int, dict[str, Any]] = {
            s.id: {
                "service_id": s.id,
                "service_name": s.name,
                "order_count": 0,
                "total_revenue": Decimal("0.00"),
            }
            for s in services
        }

        for b in bookings:
            for item in b.services_snapshot:
                raw_id = item.get("id")
                if raw_id is not None:
                    sid = int(raw_id)
                    if sid in stats:
                        stats[sid]["order_count"] += 1
                        stats[sid]["total_revenue"] += Decimal(
                            str(item.get("price", "0.00"))
                        )
                    else:
                        stats[sid] = {
                            "service_id": sid,
                            "service_name": str(item.get("name", "Unknown")),
                            "order_count": 1,
                            "total_revenue": Decimal(str(item.get("price", "0.00"))),
                        }

        sorted_items = sorted(
            stats.values(),
            key=lambda x: (x["order_count"], x["total_revenue"]),
            reverse=True,
        )

        return PopularServicesResponse(
            services=[
                PopularServiceItem(
                    service_id=item["service_id"],
                    service_name=item["service_name"],
                    order_count=item["order_count"],
                    total_revenue=item["total_revenue"].quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    ),
                )
                for item in sorted_items
            ]
        )
