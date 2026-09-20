from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.room_repository import RoomRepository
from src.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from src.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def get_room_service(session: AsyncSession = Depends(get_db)) -> RoomService:
    repo = RoomRepository(session)
    return RoomService(repo)


@router.get("", response_model=list[RoomResponse], status_code=status.HTTP_200_OK)
async def list_rooms(
    service: RoomService = Depends(get_room_service),
) -> list[RoomResponse]:
    rooms = await service.list_active_rooms()
    return [RoomResponse.model_validate(r) for r in rooms]


@router.get("/{room_id}", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def get_room(
    room_id: int,
    service: RoomService = Depends(get_room_service),
) -> RoomResponse:
    room = await service.get_room(room_id)
    return RoomResponse.model_validate(room)


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    service: RoomService = Depends(get_room_service),
) -> RoomResponse:
    room = await service.create_room(data)
    return RoomResponse.model_validate(room)


@router.patch("/{room_id}", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def update_room(
    room_id: int,
    data: RoomUpdate,
    service: RoomService = Depends(get_room_service),
) -> RoomResponse:
    room = await service.update_room(room_id, data)
    return RoomResponse.model_validate(room)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    service: RoomService = Depends(get_room_service),
) -> None:
    await service.delete_room(room_id)
