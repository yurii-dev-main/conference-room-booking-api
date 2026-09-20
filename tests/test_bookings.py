import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking_success(client: AsyncClient) -> None:
    # 1. Setup service and room
    srv_res = await client.post(
        "/api/v1/services",
        json={"name": "4K Projector", "price": "600.00"},
    )
    srv_id = srv_res.json()["id"]

    room_res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Amber Conference Room",
            "capacity": 25,
            "base_hourly_rate": "2000.00",
            "service_ids": [srv_id],
        },
    )
    room_id = room_res.json()["id"]

    # 2. Book 10:00 to 12:00 (2h @ 2000 standard rate = 4000) + 600 service = 4600
    booking_res = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_time": "2026-10-15T10:00:00Z",
            "end_time": "2026-10-15T12:00:00Z",
            "selected_service_ids": [srv_id],
        },
    )
    assert booking_res.status_code == 201
    data = booking_res.json()
    assert data["room_id"] == room_id
    assert float(data["room_cost"]) == 4000.0
    assert float(data["services_cost"]) == 600.0
    assert float(data["total_price"]) == 4600.0
    assert len(data["services_snapshot"]) == 1
    assert data["services_snapshot"][0]["name"] == "4K Projector"
    assert float(data["services_snapshot"][0]["price"]) == 600.0


@pytest.mark.asyncio
async def test_booking_conflict_same_slot(client: AsyncClient) -> None:
    room_res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Topaz Boardroom",
            "capacity": 15,
            "base_hourly_rate": "1500.00",
        },
    )
    room_id = room_res.json()["id"]

    # First booking
    res1 = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_time": "2026-10-16T10:00:00Z",
            "end_time": "2026-10-16T12:00:00Z",
        },
    )
    assert res1.status_code == 201

    # Overlapping booking attempt
    res2 = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": room_id,
            "start_time": "2026-10-16T11:00:00Z",
            "end_time": "2026-10-16T13:00:00Z",
        },
    )
    assert res2.status_code == 409
    assert "already booked" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_concurrent_bookings_exact_same_slot(client: AsyncClient) -> None:
    room_res = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Onyx Meeting Room",
            "capacity": 20,
            "base_hourly_rate": "1800.00",
        },
    )
    room_id = room_res.json()["id"]

    payload = {
        "room_id": room_id,
        "start_time": "2026-10-17T14:00:00Z",
        "end_time": "2026-10-17T16:00:00Z",
    }

    # Simulate two simultaneous booking requests for the exact same room and slot
    res1, res2 = await asyncio.gather(
        client.post("/api/v1/bookings", json=payload),
        client.post("/api/v1/bookings", json=payload),
    )

    status_codes = sorted([res1.status_code, res2.status_code])
    # Exactly one request must succeed (201) and the other must be rejected (409)
    assert status_codes == [201, 409]
