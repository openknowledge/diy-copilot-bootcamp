"""Background job that releases no-show bookings.

The job runs every RELEASE_INTERVAL_SECONDS inside the API process. In
production there is exactly one API replica that has
``ROOMIE_RUN_SCHEDULER=1`` set, so the job does not run twice.
"""

import asyncio
import logging
import os

from roomie.services.booking_service import BookingService

logger = logging.getLogger("roomie.scheduler")

RELEASE_INTERVAL_SECONDS = 60


def scheduler_enabled() -> bool:
    return os.getenv("ROOMIE_RUN_SCHEDULER", "0") == "1"


async def run_release_loop(service: BookingService) -> None:
    while True:
        released = service.release_no_shows()
        if released:
            logger.info("Released %d no-show booking(s)", len(released))
        await asyncio.sleep(RELEASE_INTERVAL_SECONDS)
