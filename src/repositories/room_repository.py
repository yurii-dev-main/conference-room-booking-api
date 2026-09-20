from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Booking, BookingStatus, Room, Service


class RoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, room_id: int) -> Room | None:
        stmt = (
            select(Room).options(selectinload(Room.services)).where(Room.id == room_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_name(self, name: str) -> Room | None:
        stmt = select(Room).where(Room.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_active(self) -> Sequence[Room]:
        stmt = (
            select(Room)
            .options(selectinload(Room.services))
            .where(Room.is_active.is_(True))
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def get_services_by_ids(self, service_ids: list[int]) -> Sequence[Service]:
        if not service_ids:
            return []
        stmt = select(Service).where(Service.id.in_(service_ids))
        return (await self.session.execute(stmt)).scalars().all()

    async def has_active_future_bookings(
        self, room_id: int, current_time: datetime
    ) -> bool:
        stmt = (
            select(Booking)
            .where(
                Booking.room_id == room_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.end_time > current_time,
            )
            .limit(1)
        )
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        return result is not None

    async def create(self, room: Room) -> Room:
        self.session.add(room)
        await self.session.flush()
        return room

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, room: Room) -> None:
        await self.session.refresh(room)
