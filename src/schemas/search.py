from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.service import ServiceResponse


class RoomSearchRequest(BaseModel):
    start_time: datetime = Field(
        ...,
        description="Search interval start time in ISO 8601 UTC format",
        examples=["2026-10-01T10:00:00Z"],
    )
    end_time: datetime = Field(
        ...,
        description="Search interval end time in ISO 8601 UTC format",
        examples=["2026-10-01T12:00:00Z"],
    )
    min_capacity: int = Field(
        default=1,
        gt=0,
        description="Minimum room capacity filter",
        examples=[20],
    )

    @model_validator(mode="after")
    def validate_interval(self) -> "RoomSearchRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class AvailableRoomResponse(BaseModel):
    id: int = Field(..., description="Unique room identifier", examples=[1])
    name: str = Field(..., description="Room name", examples=["Emerald Hall"])
    capacity: int = Field(..., description="Room capacity", examples=[50])
    base_hourly_rate: Decimal = Field(
        ...,
        description="Base rate per hour",
        examples=[Decimal("2000.00")],
    )
    calculated_rental_cost: Decimal = Field(
        ...,
        description=(
            "Calculated rental cost according to dynamic tariff window multipliers"
        ),
        examples=[Decimal("4000.00")],
    )
    services: list[ServiceResponse] = Field(
        default_factory=list,
        description="Services available in this room",
    )

    model_config = ConfigDict(from_attributes=True)
