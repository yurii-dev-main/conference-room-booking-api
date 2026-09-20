from fastapi import FastAPI

from src.api.v1.bookings import router as bookings_router
from src.api.v1.reports import router as reports_router
from src.api.v1.rooms import router as rooms_router
from src.api.v1.services import router as services_router
from src.core.config import settings

tags_metadata = [
    {
        "name": "Health",
        "description": "Service health checks and liveness verification.",
    },
    {
        "name": "Rooms",
        "description": (
            "Conference room lifecycle: creation, updates, listing, search, and "
            "soft deletion."
        ),
    },
    {
        "name": "Services",
        "description": (
            "Supplementary equipment and service options available for bookings."
        ),
    },
    {
        "name": "Bookings",
        "description": (
            "Reservation processing with dynamic window tariffing and row-level "
            "concurrency locking."
        ),
    },
    {
        "name": "Reports",
        "description": (
            "Business analytics: room occupancy rates, revenue metrics, and "
            "service popularity."
        ),
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Asynchronous REST API for conference room reservations, featuring dynamic "
        "hourly tariff window pricing, row-level transactional race condition "
        "protection, and SQL-optimized business reports."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
)

app.include_router(rooms_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns operational status of the service.",
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
