from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.reports import (
    OccupancyReportResponse,
    PopularServicesResponse,
    RevenueReportResponse,
)
from src.services.reports_service import ReportsService

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_reports_service(session: AsyncSession = Depends(get_db)) -> ReportsService:
    return ReportsService(session)


@router.get(
    "/occupancy",
    response_model=OccupancyReportResponse,
    summary="Room occupancy report",
    description=(
        "Calculate percentage utilization for each room relative to operating hours "
        "(06:00 to 23:00, 17 hours/day) across the specified calendar date range."
    ),
)
async def get_occupancy_report(
    start_date: date = Query(
        ...,
        description="Inclusive start date (YYYY-MM-DD)",
        examples=["2026-11-01"],
    ),
    end_date: date = Query(
        ...,
        description="Inclusive end date (YYYY-MM-DD)",
        examples=["2026-11-07"],
    ),
    service: ReportsService = Depends(get_reports_service),
) -> OccupancyReportResponse:
    return await service.get_occupancy_report(start_date, end_date)


@router.get(
    "/revenue",
    response_model=RevenueReportResponse,
    summary="Financial revenue report",
    description=(
        "Aggregate cumulative financial performance within the date range, broken down "
        "into room rental revenue and supplementary services revenue."
    ),
)
async def get_revenue_report(
    start_date: date = Query(
        ...,
        description="Inclusive start date (YYYY-MM-DD)",
        examples=["2026-11-01"],
    ),
    end_date: date = Query(
        ...,
        description="Inclusive end date (YYYY-MM-DD)",
        examples=["2026-11-07"],
    ),
    service: ReportsService = Depends(get_reports_service),
) -> RevenueReportResponse:
    return await service.get_revenue_report(start_date, end_date)


@router.get(
    "/popular-services",
    response_model=PopularServicesResponse,
    summary="Popular services ranking",
    description=(
        "Rank all supplementary services and equipment by booking demand frequency "
        "and generated revenue."
    ),
)
async def get_popular_services(
    service: ReportsService = Depends(get_reports_service),
) -> PopularServicesResponse:
    return await service.get_popular_services_report()
