from tests.conftest import ALICE, BOB, FIONA, at, booking_payload


def test_requires_api_key(client):
    response = client.get("/api/v2/rooms")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "ROOM-401-AUTH"


def test_create_and_get_booking(client, notifier):
    response = client.post("/api/v2/bookings", json=booking_payload(), headers=ALICE)
    assert response.status_code == 201
    booking = response.json()
    assert booking["booking_id"].startswith("bk_")
    assert booking["status"] == "confirmed"
    assert any("Booking confirmed" in message for message in notifier.sent)

    response = client.get(f"/api/v2/bookings/{booking['booking_id']}", headers=ALICE)
    assert response.status_code == 200


def test_other_users_cannot_see_booking(client):
    booking = client.post("/api/v2/bookings", json=booking_payload(), headers=ALICE).json()
    response = client.get(f"/api/v2/bookings/{booking['booking_id']}", headers=BOB)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROOM-404-BOOKING"


def test_overlapping_booking_is_rejected(client):
    client.post("/api/v2/bookings", json=booking_payload(), headers=ALICE)
    response = client.post(
        "/api/v2/bookings", json=booking_payload(start=at(14, 30, days=1), end=at(15, 30, days=1)), headers=BOB
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ROOM-409-OVERLAP"


def test_cancel_before_deadline(client):
    booking = client.post("/api/v2/bookings", json=booking_payload(), headers=ALICE).json()
    response = client.post(f"/api/v2/bookings/{booking['booking_id']}/cancel", headers=ALICE)
    assert response.json()["status"] == "cancelled"


def test_late_cancellation_only_for_admins(client, clock):
    booking = client.post("/api/v2/bookings", json=booking_payload(start=at(10), end=at(11)), headers=ALICE).json()
    clock.advance(minutes=30)  # 09:30, start is at 10:00
    response = client.post(f"/api/v2/bookings/{booking['booking_id']}/cancel", headers=ALICE)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ROOM-403-LATE-CANCEL"

    response = client.post(f"/api/v2/bookings/{booking['booking_id']}/cancel", headers=FIONA)
    assert response.json()["status"] == "cancelled"


def test_no_show_is_released(client, clock, notifier):
    booking = client.post("/api/v2/bookings", json=booking_payload(start=at(10), end=at(11)), headers=ALICE).json()
    clock.advance(hours=1, minutes=11)  # 10:11, grace period of 10 minutes is over
    released = client.post("/api/v2/bookings/release-no-shows", headers=FIONA).json()
    assert [b["booking_id"] for b in released] == [booking["booking_id"]]
    assert any("#facility-roomie" in message for message in notifier.sent)

    response = client.post(f"/api/v2/bookings/{booking['booking_id']}/check-in", headers=ALICE)
    assert response.status_code == 410


def test_check_in_within_grace_period(client, clock):
    booking = client.post("/api/v2/bookings", json=booking_payload(start=at(10), end=at(11)), headers=ALICE).json()
    clock.advance(hours=1, minutes=5)
    response = client.post(f"/api/v2/bookings/{booking['booking_id']}/check-in", headers=ALICE)
    assert response.json()["status"] == "checked_in"
