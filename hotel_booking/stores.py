# hotel_booking/stores.py
from __future__ import annotations

from typing import Protocol

from hotel_booking.domain import DateRange, Reservation, Room


class ReservationStore(Protocol):
    """What BookingService needs from storage. Today a list in memory; from P07 a database."""

    def count(self) -> int: ...
    def has_overlap(self, room: Room, stay: DateRange) -> bool: ...
    def save(self, reservation: Reservation) -> None: ...
    def find(self, reservation_id: str) -> Reservation | None: ...
    def count_confirmed(self, room: Room, stay: DateRange) -> int: ...


class InMemoryReservationStore:
    """Keeps reservations in a list. P07 adds a PostgreSQL store with the same methods."""

    def __init__(self) -> None:
        self._rows: list[Reservation] = []

    def count(self) -> int:
        return len(self._rows)

    def has_overlap(self, room: Room, stay: DateRange) -> bool:
        return any(row.blocks(room, stay) for row in self._rows)

    def save(self, reservation: Reservation) -> None:
        self._rows.append(reservation)

    def find(self, reservation_id: str) -> Reservation | None:
        return next((row for row in self._rows if row.id == reservation_id), None)

    def count_confirmed(self, room: Room, stay: DateRange) -> int:
        return sum(1 for row in self._rows if row.blocks(room, stay))