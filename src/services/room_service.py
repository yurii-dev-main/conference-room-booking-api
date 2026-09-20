from datetime import datetime, timezone

from fastapi import HTTPException, status

from src.models import Room
from src.repositories.room_repository import RoomRepository
from src.schemas.room import RoomCreate, RoomUpdate


class RoomService:
    def __init__(self, repo: RoomRepository) -> None:
        self.repo = repo

    async def get_room(self, room_id: int) -> Room:
        room = await self.repo.get_by_id(room_id)
        if not room or not room.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )
        return room

    async def list_active_rooms(self) -> list[Room]:
        return list(await self.repo.list_active())

    async def create_room(self, data: RoomCreate) -> Room:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Room with name '{data.name}' already exists",
            )

        services = []
        if data.service_ids:
            services = list(await self.repo.get_services_by_ids(data.service_ids))
            if len(services) != len(set(data.service_ids)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more services not found",
                )

        room = Room(
            name=data.name,
            capacity=data.capacity,
            base_hourly_rate=data.base_hourly_rate,
            is_active=True,
            services=services,
        )
        await self.repo.create(room)
        await self.repo.commit()
        await self.repo.refresh(room)
        return room

    async def update_room(self, room_id: int, data: RoomUpdate) -> Room:
        room = await self.repo.get_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        if data.name is not None and data.name != room.name:
            existing = await self.repo.get_by_name(data.name)
            if existing and existing.id != room_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Room with name '{data.name}' already exists",
                )
            room.name = data.name

        if data.capacity is not None:
            room.capacity = data.capacity

        if data.base_hourly_rate is not None:
            room.base_hourly_rate = data.base_hourly_rate

        if data.service_ids is not None:
            services = list(await self.repo.get_services_by_ids(data.service_ids))
            if len(services) != len(set(data.service_ids)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more services not found",
                )
            room.services = services

        await self.repo.commit()
        await self.repo.refresh(room)
        return room

    async def delete_room(self, room_id: int) -> None:
        room = await self.repo.get_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        # Soft delete validation: prevent deletion if future confirmed bookings exist
        now = datetime.now(timezone.utc)
        has_future_bookings = await self.repo.has_active_future_bookings(room_id, now)
        if has_future_bookings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete room with active future bookings",
            )

        room.is_active = False
        await self.repo.commit()
