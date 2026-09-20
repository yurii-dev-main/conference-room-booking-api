from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.service import Service


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, service_id: int) -> Service | None:
        stmt = select(Service).where(Service.id == service_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_name(self, name: str) -> Service | None:
        stmt = select(Service).where(Service.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_all(self) -> Sequence[Service]:
        stmt = select(Service).order_by(Service.id)
        return (await self.session.execute(stmt)).scalars().all()

    async def create(self, service: Service) -> Service:
        self.session.add(service)
        await self.session.flush()
        return service

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, service: Service) -> None:
        await self.session.refresh(service)
