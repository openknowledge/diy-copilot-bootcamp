"""Application factory of the Roomie service.

Run locally with:

    uvicorn roomie.main:app --reload
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from roomie import __version__
from roomie.config import API_PREFIX, SERVICE_NAME
from roomie.demo_data import demo_data_enabled, seed_demo_bookings
from roomie.errors import RoomieError, roomie_error_handler
from roomie.notifications import Notifier
from roomie.repository import Repository, seed_rooms
from roomie.routers import bookings, health, rooms
from roomie.scheduler import run_release_loop, scheduler_enabled
from roomie.services.availability_service import AvailabilityService
from roomie.services.booking_service import BookingService, utc_now

STATIC_DIR = Path(__file__).parent / "static"


def create_app(repository: Repository | None = None, notifier: Notifier | None = None, clock=utc_now) -> FastAPI:
    """Creates the FastAPI app. All collaborators can be injected for tests."""
    repository = repository or Repository()
    if not repository.list_rooms():
        seed_rooms(repository)
        if demo_data_enabled():
            seed_demo_bookings(repository, clock())
    notifier = notifier or Notifier()
    booking_service = BookingService(repository, notifier, clock=clock)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(run_release_loop(booking_service)) if scheduler_enabled() else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title=SERVICE_NAME, version=__version__, lifespan=lifespan)
    app.state.booking_service = booking_service
    app.state.availability_service = AvailabilityService(repository)

    app.add_exception_handler(RoomieError, roomie_error_handler)
    app.include_router(health.router)
    app.include_router(rooms.router, prefix=API_PREFIX)
    app.include_router(bookings.router, prefix=API_PREFIX)
    # The web UI (static HTML/JS) is served under "/". It is mounted last, so
    # that the API routes and /docs take precedence.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
    return app


logging.basicConfig(level=os.getenv("ROOMIE_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = create_app()
