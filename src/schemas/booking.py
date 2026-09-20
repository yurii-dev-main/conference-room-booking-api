from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceSnapshotItem(BaseModel):
    id: int
    name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime
    selected_service_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_interval(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class BookingResponse(BaseModel):
    id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    room_cost: Decimal
    services_cost: Decimal
    total_price: Decimal
    status: str
    services_snapshot: list[ServiceSnapshotItem]

    model_config = ConfigDict(from_attributes=True)
