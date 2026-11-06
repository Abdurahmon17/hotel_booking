# test_api.py
"""The four API tests: HTTP in, HTTP out, with the reservations in a list.

Run them with the other tests from the hotel-booking folder:  python -m unittest -v
"""
import unittest
from contextlib import contextmanager

from fastapi.testclient import TestClient

from hotel_booking.api import CountingReservationStore, Stats, create_app
from hotel_booking.api_cache import AvailabilityCache
from hotel_booking.notifications.internal import EmailNotificationSender
from hotel_booking.reservations import BookingService
from hotel_booking.reservations.internal import InMemoryReservationStore
from hotel_booking.rooms import Room

R7 = Room("R7", "Standard")
R8 = Room("R8", "Deluxe")
SEARCH = "/rooms/availability?checkIn=2026-11-12&checkOut=2026-11-14"
MAYA = {"guestName": "Maya", "guestEmail": "maya@example.com", "room": "R7", "checkIn": "2026-11-12", "checkOut": "2026-11-14"}
OMAR = {"guestName": "Omar", "guestEmail": "omar@example.com", "room": "R7", "checkIn": "2026-11-13", "checkOut": "2026-11-15"}

BOTH_FREE = ('{"checkIn":"2026-11-12","checkOut":"2026-11-14","rooms":[{"number":"R7","type":"Standard"},'
             '{"number":"R8","type":"Deluxe"}],"next":null}')
ONLY_R8 = '{"checkIn":"2026-11-12","checkOut":"2026-11-14","rooms":[{"number":"R8","type":"Deluxe"}],"next":null}'


class InMemoryKeyValueStore:
    """Redis's three commands on a dictionary. The tests run in a second, so the 30 s TTL never ends."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._values.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._values[key] = value

    def increment(self, key: str) -> None:
        self._values[key] = str(int(self._values.get(key, "0")) + 1)


def new_client() -> TestClient:
    """The web app with the in-memory store and cache; FastAPI's TestClient sends the requests without a network."""
    stats = Stats()
    service = BookingService([R7, R8], CountingReservationStore(InMemoryReservationStore(), stats), EmailNotificationSender())

    @contextmanager
    def unit_of_work():
        yield service  # a list in memory has nothing to save at the end of a request

    return TestClient(create_app([R7, R8], unit_of_work, stats, AvailabilityCache(InMemoryKeyValueStore())))


class ApiTests(unittest.TestCase):
    def test_search_answers_200_with_the_free_rooms(self):
        response = new_client().get(SEARCH)
        self.assertEqual(200, response.status_code)
        self.assertEqual('{"checkIn":"2026-11-12","checkOut":"2026-11-14","rooms":[{"number":"R7","type":"Standard"},'
                         '{"number":"R8","type":"Deluxe"}],"next":null}', response.text)

    def test_booking_answers_201_then_409_for_a_shared_night(self):
        client = new_client()
        first = client.post("/reservations", json=MAYA)
        self.assertEqual(201, first.status_code)
        self.assertEqual('{"id":"R101","status":"Confirmed","notificationFailed":false}', first.text)
        second = client.post("/reservations", json=OMAR)
        self.assertEqual(409, second.status_code)
        self.assertEqual("Unavailable", second.json()["title"])

    def test_wrong_dates_answer_400_with_problem_details(self):
        response = new_client().post("/reservations", json={**OMAR, "room": "R8", "checkIn": "2026-11-15", "checkOut": "2026-11-15"})
        self.assertEqual(400, response.status_code)
        self.assertEqual("application/problem+json", response.headers["content-type"])
        self.assertEqual('{"title":"InvalidDates","status":400,"detail":"checkOut must be after checkIn."}', response.text)

    def test_cancel_answers_204_then_404(self):
        client = new_client()
        client.post("/reservations", json=MAYA)
        self.assertEqual(204, client.delete("/reservations/R101").status_code)
        second = client.delete("/reservations/R101")
        self.assertEqual(404, second.status_code)
        self.assertEqual("NotFound", second.json()["title"])

    def test_the_second_search_is_answered_by_the_cache(self):
        client = new_client()
        first = client.get(SEARCH)
        second = client.get(SEARCH)
        self.assertEqual(first.text, second.text)
        self.assertEqual('{"searches":2,"databaseQueries":2,"cacheHits":1,"cacheMisses":1}', client.get("/stats").text)

    def test_a_booking_and_a_cancel_make_the_next_search_fresh(self):
        client = new_client()
        self.assertEqual(BOTH_FREE, client.get(SEARCH).text)
        self.assertEqual(201, client.post("/reservations", json=MAYA).status_code)
        self.assertEqual(ONLY_R8, client.get(SEARCH).text)
        self.assertEqual(204, client.delete("/reservations/R101").status_code)
        self.assertEqual(BOTH_FREE, client.get(SEARCH).text)


if __name__ == "__main__":
    unittest.main()