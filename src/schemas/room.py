from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.service import ServiceResponse


class RoomBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the conference room",
        examples=["Emerald Hall"],
    )
    capacity: int = Field(
        ...,
        gt=0,
        description="Maximum attendee capacity",
        examples=[50],
    )
    base_hourly_rate: Decimal = Field(
        ...,
        gt=0,
        description="Base rental rate per hour during standard tariff windows",
        examples=[Decimal("2000.00")],
    )


class RoomCreate(RoomBase):
    service_ids: list[int] = Field(
        default_factory=list,
        description="List of service IDs available in this conference room",
        examples=[[1, 2, 3]],
    )


class RoomUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated name of the conference room",
        examples=["Emerald Executive Hall"],
    )
    capacity: int | None = Field(
        default=None,
        gt=0,
        description="Updated capacity",
        examples=[60],
    )
    base_hourly_rate: Decimal | None = Field(
        default=None,
        gt=0,
        description="Updated base hourly rate",
        examples=[Decimal("2200.00")],
    )
    service_ids: list[int] | None = Field(
        default=None,
        description="Updated list of associated service IDs",
        examples=[[1, 2]],
    )


class RoomResponse(RoomBase):
    id: int = Field(..., description="Unique room identifier", examples=[1])
    is_active: bool = Field(
        ..., description="Active availability status of the room", examples=[True]
    )
    services: list[ServiceResponse] = Field(
        default_factory=list,
        description="List of services linked to this conference room",
    )

    model_config = ConfigDict(from_attributes=True)
