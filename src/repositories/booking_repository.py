from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Booking, BookingStatus, Room, Service


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lock_room(self, room_id: int) -> Room | None:
        # Acquire row-level lock on Room to serialize bookings for the same room
        stmt = (
            select(Room)
            .options(selectinload(Room.services))
            .where(Room.id == room_id)
            .with_for_update()
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def find_overlapping_booking(
        self, room_id: int, start_time: datetime, end_time: datetime
    ) -> Booking | None:
        # Standard interval overlap check: start < other_end AND end > other_start
        stmt = (
            select(Booking)
            .where(
                Booking.room_id == room_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_services(self, service_ids: list[int]) -> Sequence[Service]:
        if not service_ids:
            return []
        stmt = select(Service).where(Service.id.in_(service_ids))
        return (await self.session.execute(stmt)).scalars().all()

    async def create(self, booking: Booking) -> Booking:
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def refresh(self, booking: Booking) -> None:
        await self.session.refresh(booking)
