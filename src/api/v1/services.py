from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.service_repository import ServiceRepository
from src.schemas.service import ServiceCreate, ServiceResponse
from src.services.service_service import ServiceService

router = APIRouter(prefix="/services", tags=["Services"])


def get_service_service(session: AsyncSession = Depends(get_db)) -> ServiceService:
    repo = ServiceRepository(session)
    return ServiceService(repo)


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create supplementary service",
    description="Add supplementary equipment or service with fixed price to catalog.",
)
async def create_service(
    data: ServiceCreate,
    service: ServiceService = Depends(get_service_service),
) -> ServiceResponse:
    item = await service.create_service(data)
    return ServiceResponse.model_validate(item)


@router.get(
    "",
    response_model=list[ServiceResponse],
    status_code=status.HTTP_200_OK,
    summary="List available services",
    description="Retrieve all registered equipment and service options for booking.",
)
async def list_services(
    service: ServiceService = Depends(get_service_service),
) -> list[ServiceResponse]:
    items = await service.list_services()
    return [ServiceResponse.model_validate(item) for item in items]
