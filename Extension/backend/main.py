"""Tube Snatcher Extension Backend entry point."""
import uvicorn

from core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if settings.DEBUG else "warning",
        reload=settings.DEBUG,
    )
