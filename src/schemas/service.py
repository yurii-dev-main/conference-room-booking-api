from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the supplementary service or equipment",
        examples=["Projector"],
    )
    price: Decimal = Field(
        ...,
        gt=0,
        description="Fixed price of the service per booking in currency units",
        examples=[Decimal("500.00")],
    )


class ServiceResponse(BaseModel):
    id: int = Field(..., description="Unique service identifier", examples=[1])
    name: str = Field(..., description="Name of the service", examples=["Projector"])
    price: Decimal = Field(
        ...,
        description="Fixed price of the service",
        examples=[Decimal("500.00")],
    )

    model_config = ConfigDict(from_attributes=True)
