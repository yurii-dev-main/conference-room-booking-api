from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceSnapshotItem(BaseModel):
    id: int = Field(..., description="Service ID", examples=[1])
    name: str = Field(..., description="Service name", examples=["Projector"])
    price: Decimal = Field(
        ...,
        description="Frozen price of the service at time of booking",
        examples=[Decimal("500.00")],
    )

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    room_id: int = Field(..., description="Room ID to book", examples=[1])
    start_time: datetime = Field(
        ...,
        description="Booking start datetime in UTC",
        examples=["2026-10-15T10:00:00Z"],
    )
    end_time: datetime = Field(
        ...,
        description="Booking end datetime in UTC",
        examples=["2026-10-15T12:00:00Z"],
    )
    selected_service_ids: list[int] = Field(
        default_factory=list,
        description="Optional list of service IDs to include in the booking",
        examples=[[1, 2]],
    )

    @model_validator(mode="after")
    def validate_interval(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class BookingResponse(BaseModel):
    id: int = Field(..., description="Unique booking ID", examples=[101])
    room_id: int = Field(..., description="Booked room ID", examples=[1])
    start_time: datetime = Field(
        ...,
        description="Booking start time",
        examples=["2026-10-15T10:00:00Z"],
    )
    end_time: datetime = Field(
        ...,
        description="Booking end time",
        examples=["2026-10-15T12:00:00Z"],
    )
    room_cost: Decimal = Field(
        ...,
        description="Room rental cost calculated by Pricing Engine",
        examples=[Decimal("4000.00")],
    )
    services_cost: Decimal = Field(
        ...,
        description="Total cost of selected services",
        examples=[Decimal("500.00")],
    )
    total_price: Decimal = Field(
        ...,
        description="Final total price (room cost + services cost)",
        examples=[Decimal("4500.00")],
    )
    status: str = Field(
        ...,
        description="Booking status (confirmed, cancelled)",
        examples=["confirmed"],
    )
    services_snapshot: list[ServiceSnapshotItem] = Field(
        default_factory=list,
        description=(
            "Historical snapshot of services and prices preserved at booking creation"
        ),
    )

    model_config = ConfigDict(from_attributes=True)
