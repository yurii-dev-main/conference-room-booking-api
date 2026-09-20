from fastapi import FastAPI

from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
