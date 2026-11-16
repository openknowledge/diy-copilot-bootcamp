"""Wiring of services for FastAPI's dependency injection.

The services are created once in ``create_app`` and stored on
``app.state``. Routers access them only through these functions, which
makes it easy to swap them in tests.
"""

from fastapi import Request

from roomie.services.availability_service import AvailabilityService
from roomie.services.booking_service import BookingService


def get_booking_service(request: Request) -> BookingService:
    return request.app.state.booking_service


def get_availability_service(request: Request) -> AvailabilityService:
    return request.app.state.availability_service
