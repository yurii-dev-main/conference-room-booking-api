from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.service import ServiceResponse


class RoomSearchRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    min_capacity: int = Field(default=1, gt=0)

    @model_validator(mode="after")
    def validate_interval(self) -> "RoomSearchRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class AvailableRoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    base_hourly_rate: Decimal
    calculated_rental_cost: Decimal
    services: list[ServiceResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
