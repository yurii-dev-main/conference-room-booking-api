from collections.abc import Sequence

from fastapi import HTTPException, status

from src.models.service import Service
from src.repositories.service_repository import ServiceRepository
from src.schemas.service import ServiceCreate


class ServiceService:
    def __init__(self, repo: ServiceRepository) -> None:
        self.repo = repo

    async def create_service(self, data: ServiceCreate) -> Service:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service with name '{data.name}' already exists",
            )
        service = Service(name=data.name, price=data.price)
        await self.repo.create(service)
        await self.repo.commit()
        await self.repo.refresh(service)
        return service

    async def list_services(self) -> Sequence[Service]:
        return await self.repo.list_all()

    async def get_service(self, service_id: int) -> Service:
        service = await self.repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found",
            )
        return service
