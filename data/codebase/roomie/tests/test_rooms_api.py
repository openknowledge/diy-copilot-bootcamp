from tests.conftest import ALICE, FIONA, at, booking_payload


def test_health_needs_no_auth(client):
    assert client.get("/health").json()["status"] == "ok"


def test_list_rooms(client):
    rooms = client.get("/api/v2/rooms", headers=ALICE).json()
    assert [room["room_id"] for room in rooms][:2] == ["A1-01", "A1-02"]


def test_search_returns_smallest_room_first(client):
    params = {"start": at(10, days=1).isoformat(), "end": at(11, days=1).isoformat(), "attendees": 3}
    rooms = client.get("/api/v2/rooms/search", params=params, headers=ALICE).json()
    assert rooms[0]["room_id"] == "A1-01"
    # The big room is excluded for only 3 attendees (big room policy)
    assert "A2-10" not in [room["room_id"] for room in rooms]


def test_availability_respects_bookings(client):
    client.post("/api/v2/bookings", json=booking_payload(start=at(10, days=1), end=at(11, days=1)), headers=ALICE)
    day = at(0, days=1).date().isoformat()
    slots = client.get("/api/v2/rooms/A1-02/availability", params={"day": day}, headers=ALICE).json()
    assert len(slots) == 2


def test_only_admins_can_change_rooms(client):
    room = {"room_id": "X", "name": "Lab", "capacity": 3, "floor": 0}
    assert client.put("/api/v2/rooms/C0-01", json=room, headers=ALICE).status_code == 403
    assert client.put("/api/v2/rooms/C0-01", json=room, headers=FIONA).json()["room_id"] == "C0-01"
