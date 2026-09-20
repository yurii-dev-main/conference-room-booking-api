from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Booking, BookingStatus, Room


@pytest.mark.asyncio
async def test_create_and_get_room(client: AsyncClient) -> None:
    # 1. Create a service
    service_res = await client.post(
        "/api/v1/services",
        json={"name": "Projector", "price": "450.00"},
    )
    assert service_res.status_code == 201
    service_id = service_res.json()["id"]

    # 2. Create a room with the service
    room_res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Emerald Hall",
            "capacity": 40,
            "base_hourly_rate": "1800.00",
            "service_ids": [service_id],
        },
    )
    assert room_res.status_code == 201
    room_data = room_res.json()
    assert room_data["name"] == "Emerald Hall"
    assert room_data["capacity"] == 40
    assert float(room_data["base_hourly_rate"]) == 1800.0
    assert len(room_data["services"]) == 1
    assert room_data["services"][0]["id"] == service_id

    # 3. Get room by ID
    get_res = await client.get(f"/api/v1/rooms/{room_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Emerald Hall"

    # 4. List rooms
    list_res = await client.get("/api/v1/rooms")
    assert list_res.status_code == 200
    assert any(r["id"] == room_data["id"] for r in list_res.json())


@pytest.mark.asyncio
async def test_update_room(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Ruby Room",
            "capacity": 25,
            "base_hourly_rate": "1200.00",
            "service_ids": [],
        },
    )
    room_id = create_res.json()["id"]

    patch_res = await client.patch(
        f"/api/v1/rooms/{room_id}",
        json={"name": "Ruby Grand Room", "capacity": 35},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["name"] == "Ruby Grand Room"
    assert updated_data["capacity"] == 35


@pytest.mark.asyncio
async def test_delete_room_soft_delete(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Sapphire Hall",
            "capacity": 20,
            "base_hourly_rate": "1000.00",
        },
    )
    room_id = create_res.json()["id"]

    del_res = await client.delete(f"/api/v1/rooms/{room_id}")
    assert del_res.status_code == 204

    # Getting deleted room returns 404
    get_res = await client.get(f"/api/v1/rooms/{room_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_room_blocked_by_future_booking(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create room
    room = Room(
        name="Diamond Hall",
        capacity=50,
        base_hourly_rate=2500,
        is_active=True,
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    # Add active future booking
    future_start = datetime.now(timezone.utc) + timedelta(days=2)
    future_end = future_start + timedelta(hours=3)
    booking = Booking(
        room_id=room.id,
        start_time=future_start,
        end_time=future_end,
        total_price=7500,
        status=BookingStatus.CONFIRMED,
        services_snapshot=[],
    )
    db_session.add(booking)
    await db_session.commit()

    # Attempt to delete should fail with 400
    del_res = await client.delete(f"/api/v1/rooms/{room.id}")
    assert del_res.status_code == 400
    assert "active future bookings" in del_res.json()["detail"]


@pytest.mark.asyncio
async def test_room_validation_errors(client: AsyncClient) -> None:
    # Invalid negative capacity
    res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Invalid Room",
            "capacity": -5,
            "base_hourly_rate": "1000.00",
        },
    )
    assert res.status_code == 422
