from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.booking_repository import BookingRepository
from src.schemas.booking import BookingCreate, BookingResponse
from src.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_booking_service(session: AsyncSession = Depends(get_db)) -> BookingService:
    repo = BookingRepository(session)
    return BookingService(repo)


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    return await service.create_booking(data)
