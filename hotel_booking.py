"""P03 - Hotel booking, first version: one file, everything kept in memory.

python hotel_booking.py          -> the normal demo
python hotel_booking.py --race   -> two guests book the same room at the same moment
"""
from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from datetime import date
from enum import Enum


# 7.1 · The stay: check-in day included, check-out day excluded (half-open).
@dataclass(frozen=True)
class DateRange:
    check_in: date
    check_out: date

    def is_valid(self) -> bool:
        return self.check_out > self.check_in

    # Two stays overlap when they share at least one night.
    def overlaps(self, other: DateRange) -> bool:
        return self.check_in < other.check_out and other.check_in < self.check_out


# 7.2 · Guest and Room: plain data
@dataclass(frozen=True)
class Guest:
    name: str
    email: str


@dataclass(frozen=True)
class Room:
    number: str
    type: str


# 7.3 · Reservation: knows its own status
class ReservationStatus(Enum):
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"


class Reservation:
    def __init__(self, reservation_id: str, guest: Guest, room: Room, stay: DateRange) -> None:
        self.id = reservation_id
        self.guest = guest
        self.room = room
        self.stay = stay
        self.status = ReservationStatus.CONFIRMED

    # A reservation blocks a request when it is still Confirmed for the same room and shares a night.
    def blocks(self, room: Room, stay: DateRange) -> bool:
        return self.status == ReservationStatus.CONFIRMED and self.room == room and self.stay.overlaps(stay)

    def cancel(self) -> bool:
        if self.status == ReservationStatus.CANCELLED:
            return False
        self.status = ReservationStatus.CANCELLED
        return True


# 7.4 · ReservationStore: keeps reservations in a list. A later practice replaces it with a database.
class ReservationStore:
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


# 7.5 · EmailSender (simulated: sends nothing, needs no network) and BookingResult
class EmailSender:
    def __init__(self) -> None:
        self.sent = 0

    def send_confirmation(self, reservation: Reservation) -> None:
        self.sent += 1


@dataclass(frozen=True)
class BookingResult:
    outcome: str
    reservation_id: str | None = None

    def __str__(self) -> str:
        return self.outcome if self.reservation_id is None else f"{self.outcome} {self.reservation_id}"


# 7.6 · BookingService: runs each request in order
class BookingService:
    def __init__(self, rooms: list[Room], store: ReservationStore, email: EmailSender, slow_step_seconds: float = 0) -> None:
        self.rooms = rooms
        self.store = store
        self.email = email
        self.slow_step_seconds = slow_step_seconds

    def find_free_rooms(self, stay: DateRange) -> list[Room]:
        return [room for room in self.rooms if not self.store.has_overlap(room, stay)]

    def reserve(self, guest: Guest, room: Room, stay: DateRange) -> BookingResult:
        if not stay.is_valid():
            return BookingResult("InvalidDates")
        if self.store.has_overlap(room, stay):
            return BookingResult("Unavailable")

        time.sleep(self.slow_step_seconds)  # 0 normally; the race demo makes this step slow

        reservation = Reservation(f"R{101 + self.store.count()}", guest, room, stay)
        self.store.save(reservation)
        self.email.send_confirmation(reservation)
        return BookingResult("Accepted", reservation.id)

    def cancel(self, reservation_id: str) -> bool:
        reservation = self.store.find(reservation_id)
        return reservation is not None and reservation.cancel()


# 7.7 · The demo: Maya, Omar and Nora
R7 = Room("R7", "Standard")
R8 = Room("R8", "Deluxe")
MAYA = Guest("Maya", "maya@example.com")
OMAR = Guest("Omar", "omar@example.com")
NORA = Guest("Nora", "nora@example.com")


def nov(check_in: int, check_out: int) -> DateRange:
    return DateRange(date(2026, 11, check_in), date(2026, 11, check_out))


def names(rooms: list[Room]) -> str:
    return ", ".join(room.number for room in rooms)


def run_demo() -> None:
    store = ReservationStore()
    email = EmailSender()
    service = BookingService([R7, R8], store, email)

    print(f"Free rooms 12-14 Nov: {names(service.find_free_rooms(nov(12, 14)))}")
    print(f"Maya books R7 12-14 Nov: {service.reserve(MAYA, R7, nov(12, 14))}")
    print(f"Omar books R7 13-15 Nov: {service.reserve(OMAR, R7, nov(13, 15))}")
    print(f"Nora books R7 14-16 Nov: {service.reserve(NORA, R7, nov(14, 16))}")
    print(f"Omar books R8 15-15 Nov: {service.reserve(OMAR, R8, nov(15, 15))}")
    print(f"Free rooms 12-14 Nov: {names(service.find_free_rooms(nov(12, 14)))}")
    print(f"Maya cancels R101: {service.cancel('R101')}")
    print(f"Free rooms 12-14 Nov: {names(service.find_free_rooms(nov(12, 14)))}")
    print(f"Confirmation emails sent: {email.sent}")


def run_race() -> None:
    store = ReservationStore()
    # Each request now spends half a second between checking and saving.
    service = BookingService([R7, R8], store, EmailSender(), slow_step_seconds=0.5)
    stay = nov(12, 14)
    results: dict[str, BookingResult] = {}

    print("Maya and Omar both book R7 for 12-14 Nov at the same moment...")
    maya_request = threading.Thread(target=lambda: results.update(Maya=service.reserve(MAYA, R7, stay)))
    omar_request = threading.Thread(target=lambda: results.update(Omar=service.reserve(OMAR, R7, stay)))
    maya_request.start()
    time.sleep(0.1)  # Omar clicks a moment after Maya
    omar_request.start()
    maya_request.join()
    omar_request.join()

    print(f"Maya: {results['Maya']}")
    print(f"Omar: {results['Omar']}")
    confirmed = store.count_confirmed(R7, stay)
    print(f"Confirmed reservations for R7 on 12-14 Nov: {confirmed}")
    print("Double booking! Both requests checked before either one saved."
          if confirmed > 1 else "Only one guest has R7.")


if __name__ == "__main__":
    run_race() if "--race" in sys.argv else run_demo()