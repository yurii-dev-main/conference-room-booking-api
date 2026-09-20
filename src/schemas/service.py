from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0)


class ServiceResponse(BaseModel):
    id: int
    name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)
