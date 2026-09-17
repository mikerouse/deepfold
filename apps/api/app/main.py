from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import drafts, jobs, meta, outlets
from app.seed import seed_if_empty

logger = logging.getLogger(__name__)


async def _demo_worker_loop() -> None:
    from app.services.demo_worker import run_demo_tick

    delay = max(float(settings.demo_grok_worker_delay_seconds), 0.5)
    logger.warning(
        "DEMO_GROK_WORKER is on — simulating Grok Bot with stub/seed copy every %.1fs. Not an LLM call.",
        delay,
    )
    while True:
        try:
            await asyncio.to_thread(run_demo_tick)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Demo Grok worker tick failed")
        await asyncio.sleep(0.75)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_if_empty()
    worker_task = None
    if settings.demo_grok_worker:
        worker_task = asyncio.create_task(_demo_worker_loop())
    try:
        yield
    finally:
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="Deepfold Approvals Desk API",
    description="Human-in-the-loop newsroom control panel for a multi-title publisher (titles, not a single masthead).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(drafts.router)
app.include_router(outlets.router)
app.include_router(jobs.router)
