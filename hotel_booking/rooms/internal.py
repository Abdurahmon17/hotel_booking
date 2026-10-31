# hotel_booking/rooms/internal.py
from __future__ import annotations

from hotel_booking.rooms.catalog import Room


class InMemoryRoomCatalog:
    """Keeps the hotel's rooms in a list. Only main.py creates it."""

    def __init__(self, rooms: list[Room]) -> None:
        self._rooms = list(rooms)

    def all(self) -> list[Room]:
        return list(self._rooms)