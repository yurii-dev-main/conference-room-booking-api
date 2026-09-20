import asyncio
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory
from src.models import Room, RoomService, Service

INITIAL_ROOMS: list[dict[str, Any]] = [
    {"name": "Room A", "capacity": 50, "base_hourly_rate": Decimal("2000.00")},
    {"name": "Room B", "capacity": 100, "base_hourly_rate": Decimal("3500.00")},
    {"name": "Room C", "capacity": 30, "base_hourly_rate": Decimal("1500.00")},
]

INITIAL_SERVICES: list[dict[str, Any]] = [
    {"name": "Projector", "price": Decimal("500.00")},
    {"name": "Wi-Fi", "price": Decimal("300.00")},
    {"name": "Sound", "price": Decimal("700.00")},
]


async def seed_data(session: AsyncSession) -> None:
    services_map: dict[str, Service] = {}
    for s_data in INITIAL_SERVICES:
        service_name = str(s_data["name"])
        stmt = select(Service).where(Service.name == service_name)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if not existing:
            service = Service(name=service_name, price=Decimal(str(s_data["price"])))
            session.add(service)
            await session.flush()
            services_map[service_name] = service
        else:
            services_map[service_name] = existing

    rooms_list: list[Room] = []
    for r_data in INITIAL_ROOMS:
        room_name = str(r_data["name"])
        room_stmt = select(Room).where(Room.name == room_name)
        existing_room = (await session.execute(room_stmt)).scalar_one_or_none()
        if not existing_room:
            room = Room(
                name=room_name,
                capacity=int(r_data["capacity"]),
                base_hourly_rate=Decimal(str(r_data["base_hourly_rate"])),
                is_active=True,
            )
            session.add(room)
            await session.flush()
            rooms_list.append(room)
        else:
            rooms_list.append(existing_room)

    for room in rooms_list:
        for service in services_map.values():
            link_stmt = select(RoomService).where(
                RoomService.room_id == room.id,
                RoomService.service_id == service.id,
            )
            existing_link = (await session.execute(link_stmt)).scalar_one_or_none()
            if not existing_link:
                session.add(RoomService(room_id=room.id, service_id=service.id))

    await session.commit()


async def run_seed() -> None:
    async with async_session_factory() as session:
        await seed_data(session)


if __name__ == "__main__":
    asyncio.run(run_seed())
