import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory
from src.models import Room, RoomService, Service

INITIAL_ROOMS = [
    {"name": "Room A", "capacity": 50, "base_hourly_rate": Decimal("2000.00")},
    {"name": "Room B", "capacity": 100, "base_hourly_rate": Decimal("3500.00")},
    {"name": "Room C", "capacity": 30, "base_hourly_rate": Decimal("1500.00")},
]

INITIAL_SERVICES = [
    {"name": "Projector", "price": Decimal("500.00")},
    {"name": "Wi-Fi", "price": Decimal("300.00")},
    {"name": "Sound", "price": Decimal("700.00")},
]


async def seed_data(session: AsyncSession) -> None:
    services_map: dict[str, Service] = {}
    for s_data in INITIAL_SERVICES:
        stmt = select(Service).where(Service.name == s_data["name"])
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if not existing:
            service = Service(name=s_data["name"], price=s_data["price"])
            session.add(service)
            await session.flush()
            services_map[s_data["name"]] = service
        else:
            services_map[s_data["name"]] = existing

    rooms_list: list[Room] = []
    for r_data in INITIAL_ROOMS:
        stmt = select(Room).where(Room.name == r_data["name"])
        existing_room = (await session.execute(stmt)).scalar_one_or_none()
        if not existing_room:
            room = Room(
                name=r_data["name"],
                capacity=r_data["capacity"],
                base_hourly_rate=r_data["base_hourly_rate"],
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
