# hotel_booking/domain.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from hotel_booking.rooms import Room


# The stay: check-in day included, check-out day excluded (half-open).
@dataclass(frozen=True)
class DateRange:
    check_in: date
    check_out: date

    def is_valid(self) -> bool:
        return self.check_out > self.check_in

    # Two stays overlap when they share at least one night.
    def overlaps(self, other: DateRange) -> bool:
        return self.check_in < other.check_out and other.check_in < self.check_out


@dataclass(frozen=True)
class Guest:
    name: str
    email: str


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