"""Endpoints for bookings."""

from fastapi import APIRouter, Depends, status

from roomie.auth import get_current_user, require_admin
from roomie.dependencies import get_booking_service
from roomie.models import Booking, BookingCreate, User
from roomie.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=Booking, status_code=status.HTTP_201_CREATED)
def create_booking(
    request: BookingCreate,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    return service.create_booking(request, user)


@router.get("/mine", response_model=list[Booking])
def list_my_bookings(
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[Booking]:
    return service.repository.list_bookings_for_owner(user.user_id)


@router.get("/{booking_id}", response_model=Booking)
def get_booking(
    booking_id: str,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    return service.get_booking(booking_id, user)


@router.post("/{booking_id}/cancel", response_model=Booking)
def cancel_booking(
    booking_id: str,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    # Cancelling is a POST instead of DELETE, because bookings are never
    # deleted (ADR-0005).
    return service.cancel_booking(booking_id, user)


@router.post("/{booking_id}/check-in", response_model=Booking)
def check_in(
    booking_id: str,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Booking:
    return service.check_in(booking_id, user)


@router.post("/release-no-shows", response_model=list[Booking])
def release_no_shows(
    admin: User = Depends(require_admin),
    service: BookingService = Depends(get_booking_service),
) -> list[Booking]:
    """Manually triggers the no-show release job. Only for facility admins."""
    return service.release_no_shows()
