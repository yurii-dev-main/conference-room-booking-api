from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.service import ServiceResponse


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    capacity: int = Field(..., gt=0)
    base_hourly_rate: Decimal = Field(..., gt=0)


class RoomCreate(RoomBase):
    service_ids: list[int] = Field(default_factory=list)


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    capacity: int | None = Field(default=None, gt=0)
    base_hourly_rate: Decimal | None = Field(default=None, gt=0)
    service_ids: list[int] | None = None


class RoomResponse(RoomBase):
    id: int
    is_active: bool
    services: list[ServiceResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
