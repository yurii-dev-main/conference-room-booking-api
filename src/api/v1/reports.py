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


@router.get("/occupancy", response_model=OccupancyReportResponse)
async def get_occupancy_report(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    service: ReportsService = Depends(get_reports_service),
) -> OccupancyReportResponse:
    return await service.get_occupancy_report(start_date, end_date)


@router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    service: ReportsService = Depends(get_reports_service),
) -> RevenueReportResponse:
    return await service.get_revenue_report(start_date, end_date)


@router.get("/popular-services", response_model=PopularServicesResponse)
async def get_popular_services(
    service: ReportsService = Depends(get_reports_service),
) -> PopularServicesResponse:
    return await service.get_popular_services_report()
