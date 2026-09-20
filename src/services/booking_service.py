import asyncio
from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException, status

from src.models import Booking, BookingStatus
from src.repositories.booking_repository import BookingRepository
from src.schemas.booking import (
    BookingCreate,
    BookingResponse,
    ServiceSnapshotItem,
)
from src.services.pricing import PricingEngine

# Application-level lock per room to serialize concurrent coroutines
_room_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


class BookingService:
    def __init__(self, repo: BookingRepository) -> None:
        self.repo = repo

    async def create_booking(self, data: BookingCreate) -> BookingResponse:
        lock = _room_locks[data.room_id]
        async with lock:
            # 1. Database row-level lock (SELECT ... FOR UPDATE)
            # for cross-process concurrency control
            room = await self.repo.lock_room(data.room_id)
            if not room or not room.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Room not found or inactive",
                )

            # 2. Check for overlapping bookings
            overlap = await self.repo.find_overlapping_booking(
                data.room_id, data.start_time, data.end_time
            )
            if overlap:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The room is already booked for the selected time slot",
                )

            # 3. Retrieve and validate services
            services = []
            if data.selected_service_ids:
                services = list(await self.repo.get_services(data.selected_service_ids))
                if len(services) != len(set(data.selected_service_ids)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more selected services do not exist",
                    )

            # 4. Create immutable service snapshot
            snapshot = [
                {"id": s.id, "name": s.name, "price": str(s.price)} for s in services
            ]

            # 5. Calculate cost via PricingEngine
            room_cost, services_cost, total_price = PricingEngine.calculate_total(
                data.start_time,
                data.end_time,
                room.base_hourly_rate,
                [s.price for s in services],
            )

            # 6. Save booking
            booking = Booking(
                room_id=data.room_id,
                start_time=data.start_time,
                end_time=data.end_time,
                total_price=total_price,
                status=BookingStatus.CONFIRMED,
                services_snapshot=snapshot,
            )
            await self.repo.create(booking)
            await self.repo.commit()
            await self.repo.refresh(booking)

            return BookingResponse(
                id=booking.id,
                room_id=booking.room_id,
                start_time=booking.start_time,
                end_time=booking.end_time,
                room_cost=room_cost,
                services_cost=services_cost,
                total_price=booking.total_price,
                status=booking.status.value
                if hasattr(booking.status, "value")
                else str(booking.status),
                services_snapshot=[
                    ServiceSnapshotItem(
                        id=int(str(s["id"])),
                        name=str(s["name"]),
                        price=Decimal(str(s["price"])),
                    )
                    for s in snapshot
                ],
            )
