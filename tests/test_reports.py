from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.seed import seed_data
from src.models import Booking, BookingStatus, Room


@pytest.mark.asyncio
async def test_reports_with_seeded_data(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Seed initial rooms and services
    await seed_data(db_session)

    # 2. Query Room A
    from sqlalchemy import select

    room_a = (
        await db_session.execute(select(Room).where(Room.name == "Room A"))
    ).scalar_one()

    # 3. Add booking for Room A: 2 hours (09:00 to 11:00) on 2026-11-01
    # Standard rate 2000/hr -> 4000 UAH room cost + 500 UAH projector service
    booking = Booking(
        room_id=room_a.id,
        start_time=datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc),
        total_price=Decimal("4500.00"),
        status=BookingStatus.CONFIRMED,
        services_snapshot=[{"id": 1, "name": "Projector", "price": "500.00"}],
    )
    db_session.add(booking)
    await db_session.commit()

    # 4. Test Occupancy Report for 2026-11-01 (1 day -> 17 operating hours)
    occ_res = await client.get(
        "/api/v1/reports/occupancy",
        params={"start_date": "2026-11-01", "end_date": "2026-11-01"},
    )
    assert occ_res.status_code == 200
    occ_data = occ_res.json()
    assert occ_data["days_count"] == 1
    assert len(occ_data["rooms"]) == 3

    room_a_occ = next(r for r in occ_data["rooms"] if r["room_name"] == "Room A")
    assert float(room_a_occ["total_booked_hours"]) == 2.0
    assert float(room_a_occ["available_hours"]) == 17.0
    # (2 / 17) * 100 = 11.76%
    assert float(room_a_occ["occupancy_rate_pct"]) == 11.76

    # 5. Test Revenue Report
    rev_res = await client.get(
        "/api/v1/reports/revenue",
        params={"start_date": "2026-11-01", "end_date": "2026-11-01"},
    )
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert float(rev_data["total_revenue"]) == 4500.0
    assert float(rev_data["rooms_revenue"]) == 4000.0
    assert float(rev_data["services_revenue"]) == 500.0

    # 6. Test Popular Services Report
    pop_res = await client.get("/api/v1/reports/popular-services")
    assert pop_res.status_code == 200
    pop_data = pop_res.json()
    assert len(pop_data["services"]) >= 3
    # Projector was ordered once
    top_service = pop_data["services"][0]
    assert top_service["service_name"] == "Projector"
    assert top_service["order_count"] == 1
    assert float(top_service["total_revenue"]) == 500.0


@pytest.mark.asyncio
async def test_reports_invalid_date_range(client: AsyncClient) -> None:
    res = await client.get(
        "/api/v1/reports/occupancy",
        params={"start_date": "2026-11-10", "end_date": "2026-11-01"},
    )
    assert res.status_code == 400
