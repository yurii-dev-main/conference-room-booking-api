from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.seed import seed_data
from src.models import Room, RoomService, Service


@pytest.mark.asyncio
async def test_seed_data_populates_tables(db_session: AsyncSession) -> None:
    await seed_data(db_session)

    rooms_count = (
        await db_session.execute(select(func.count()).select_from(Room))
    ).scalar_one()
    assert rooms_count == 3

    services_count = (
        await db_session.execute(select(func.count()).select_from(Service))
    ).scalar_one()
    assert services_count == 3

    links_count = (
        await db_session.execute(select(func.count()).select_from(RoomService))
    ).scalar_one()
    assert links_count == 9

    room_b = (
        await db_session.execute(select(Room).where(Room.name == "Room B"))
    ).scalar_one()
    assert room_b.capacity == 100
    assert room_b.base_hourly_rate == Decimal("3500.00")
    assert len(room_b.services) == 3

    # Test idempotency
    await seed_data(db_session)
    rooms_count_after = (
        await db_session.execute(select(func.count()).select_from(Room))
    ).scalar_one()
    assert rooms_count_after == 3
