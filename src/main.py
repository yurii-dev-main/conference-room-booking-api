from fastapi import FastAPI

from src.api.v1.bookings import router as bookings_router
from src.api.v1.rooms import router as rooms_router
from src.api.v1.services import router as services_router
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)

app.include_router(rooms_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
