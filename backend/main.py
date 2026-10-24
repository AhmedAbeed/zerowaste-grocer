"""
main.py
FastAPI application entry point for ZeroWaste Grocer API.
Full REST API endpoints matching api_contract_v1.md.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import api_v1_router
from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.models  # Ensure all models are registered on Base
from app.services.reorder_service import warm_sigma_cache

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.notification_service import run_daily_markdown_job

def create_markdown_scheduler() -> BackgroundScheduler:
    """
    Constructs and configures the BackgroundScheduler for the daily markdown job.
    Uses machine local time and resilient SessionLocal lifecycle.
    """
    scheduler = BackgroundScheduler()

    def _job_wrapper():
        db = SessionLocal()
        try:
            run_daily_markdown_job(db)
        except Exception as e:
            print(f"[SCHEDULER ERROR] Daily markdown job execution failed: {e}")
        finally:
            db.close()

    scheduler.add_job(
        _job_wrapper,
        trigger=CronTrigger(hour=settings.MARKDOWN_JOB_HOUR, minute=settings.MARKDOWN_JOB_MINUTE),
        id="daily_markdown_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600
    )
    return scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure any new tables are created idempotently
    Base.metadata.create_all(bind=engine)

    # Application startup: warm rolling residual sigma cache for all products across all stores
    db = SessionLocal()
    try:
        from datetime import date, timedelta
        today = date.today()
        w1 = warm_sigma_cache(db, today)
        w2 = warm_sigma_cache(db, today + timedelta(days=1))
        print(f"[STARTUP] Warmed rolling sigma cache for {w1 + w2} items (today + tomorrow).")
    except Exception as e:
        print(f"[STARTUP WARNING] Failed to warm sigma cache: {e}")
    finally:
        db.close()

    scheduler = None
    if settings.SCHEDULER_ENABLED:
        try:
            scheduler = create_markdown_scheduler()
            scheduler.start()
            hh = f"{settings.MARKDOWN_JOB_HOUR:02d}"
            mm = f"{settings.MARKDOWN_JOB_MINUTE:02d}"
            print(f"[STARTUP] Markdown scheduler started: daily at {hh}:{mm}")
        except Exception as e:
            print(f"[STARTUP WARNING] Failed to start markdown scheduler: {e}")

    yield

    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass

app = FastAPI(
    title="ZeroWaste Grocer API",
    version="1.0.0",
    description="High-throughput, ML-driven demand forecasting, replenishment, and food waste reduction API.",
    lifespan=lifespan
)

# CORS middleware allowing open access for Flutter client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System health endpoint
@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "healthy",
        "service": "zerowaste-api"
    }

# Mount consolidated v1 API Router under /api/v1
app.include_router(api_v1_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
