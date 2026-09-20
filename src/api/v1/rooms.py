from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.room_repository import RoomRepository
from src.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from src.schemas.search import AvailableRoomResponse, RoomSearchRequest
from src.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def get_room_service(session: AsyncSession = Depends(get_db)) -> RoomService:
    repo = RoomRepository(session)
    return RoomService(repo)


@router.post(
    "/search",
    response_model=list[AvailableRoomResponse],
    status_code=status.HTTP_200_OK,
    summary="Search available conference rooms",
    description=(
        "Find active rooms satisfying capacity requirements without overlapping "
        "confirmed bookings, returning calculated rental cost according to dynamic "
        "tariffs."
    ),
)
async def search_available_rooms(
    request: RoomSearchRequest,
    service: RoomService = Depends(get_room_service),
) -> list[AvailableRoomResponse]:
    return await service.search_available_rooms(request)


@router.get(
    "",
    response_model=list[RoomResponse],
    status_code=status.HTTP_200_OK,
    summary="List all active conference rooms",
    description="Retrieve all active conference rooms with associated services.",
)
async def list_rooms(
    service: RoomService = Depends(get_room_service),
) -> list[RoomResponse]:
    rooms = await service.list_active_rooms()
    return [RoomResponse.model_validate(r) for r in rooms]


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conference room details",
    description="Retrieve configuration and services for a specific conference room.",
)
async def get_room(
    room_id: int,
    service: RoomService = Depends(get_room_service),
) -> RoomResponse:
    room = await service.get_room(room_id)
    return RoomResponse.model_validate(room)


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conference room",
    description=(
        "Register a new room with capacity, base rate, and linked service options."
    ),
)
async def create_room(
    data: RoomCreate,
    service: RoomService = Depends(get_room_service),
) -> RoomResponse:
    room = await service.create_room(data)
    return RoomResponse.model_validate(room)


@router.patch(
    "/{room_id}",
    response_model=RoomResponse,
    status_code=status.HTTP_200_OK,
    summary="Update conference room details",
    description="Modify room properties, capacity, base rate, or attached services.",
)
async def update_room(
    room_id: int,
    data: RoomUpdate,
    service: RoomService = Depends(get_room_service),
) -> RoomResponse:
    room = await service.update_room(room_id, data)
    return RoomResponse.model_validate(room)


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a conference room",
    description=(
        "Deactivate a conference room. Fails if active future bookings exist."
    ),
)
async def delete_room(
    room_id: int,
    service: RoomService = Depends(get_room_service),
) -> None:
    await service.delete_room(room_id)
