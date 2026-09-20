from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RoomOccupancy(BaseModel):
    room_id: int
    room_name: str
    total_booked_hours: Decimal
    available_hours: Decimal
    occupancy_rate_pct: Decimal

    model_config = ConfigDict(from_attributes=True)


class OccupancyReportResponse(BaseModel):
    start_date: date
    end_date: date
    days_count: int
    rooms: list[RoomOccupancy]


class RevenueReportResponse(BaseModel):
    start_date: date
    end_date: date
    total_revenue: Decimal
    rooms_revenue: Decimal
    services_revenue: Decimal


class PopularServiceItem(BaseModel):
    service_id: int
    service_name: str
    order_count: int = Field(..., ge=0)
    total_revenue: Decimal

    model_config = ConfigDict(from_attributes=True)


class PopularServicesResponse(BaseModel):
    services: list[PopularServiceItem]
