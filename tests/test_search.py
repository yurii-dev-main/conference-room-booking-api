from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Booking, BookingStatus, Room


@pytest.mark.asyncio
async def test_search_rooms_by_capacity_and_availability(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Create two rooms: Small (capacity 10) and Large (capacity 50)
    small_room = Room(
        name="Small Room",
        capacity=10,
        base_hourly_rate=Decimal("1000.00"),
        is_active=True,
    )
    large_room = Room(
        name="Large Room",
        capacity=50,
        base_hourly_rate=Decimal("3000.00"),
        is_active=True,
    )
    db_session.add_all([small_room, large_room])
    await db_session.commit()
    await db_session.refresh(small_room)
    await db_session.refresh(large_room)

    # 2. Book small room from 10:00 to 12:00
    booking = Booking(
        room_id=small_room.id,
        start_time=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc),
        total_price=Decimal("2000.00"),
        status=BookingStatus.CONFIRMED,
        services_snapshot=[],
    )
    db_session.add(booking)
    await db_session.commit()

    # 3. Search during the booked interval with min_capacity=5
    # Small room is booked, so only Large room should be returned
    search_res = await client.post(
        "/api/v1/rooms/search",
        json={
            "start_time": "2026-10-01T10:30:00Z",
            "end_time": "2026-10-01T11:30:00Z",
            "min_capacity": 5,
        },
    )
    assert search_res.status_code == 200
    rooms = search_res.json()
    assert len(rooms) == 1
    assert rooms[0]["name"] == "Large Room"
    assert rooms[0]["capacity"] == 50
    # 1 hour standard rate for large room (3000)
    assert float(rooms[0]["calculated_rental_cost"]) == 3000.0

    # 4. Search in non-overlapping slot (14:00 to 16:00) with min_capacity=5
    # Both rooms should be available
    search_res_2 = await client.post(
        "/api/v1/rooms/search",
        json={
            "start_time": "2026-10-01T14:00:00Z",
            "end_time": "2026-10-01T16:00:00Z",
            "min_capacity": 5,
        },
    )
    assert search_res_2.status_code == 200
    rooms_2 = search_res_2.json()
    assert len(rooms_2) == 2

    # 5. Search with min_capacity=30
    # Only Large room meets capacity
    search_res_3 = await client.post(
        "/api/v1/rooms/search",
        json={
            "start_time": "2026-10-01T14:00:00Z",
            "end_time": "2026-10-01T16:00:00Z",
            "min_capacity": 30,
        },
    )
    assert search_res_3.status_code == 200
    rooms_3 = search_res_3.json()
    assert len(rooms_3) == 1
    assert rooms_3[0]["name"] == "Large Room"
