# hotel_booking/notifications/__init__.py
"""Notifications: telling guests what happened. Public contract: Confirmation and NotificationSender."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class Confirmation:
    """Notifications' own message: it no longer needs the Reservation class."""
    reservation_id: str
    guest_email: str
    room_number: str
    check_in: date
    check_out: date


class NotificationSender(Protocol):
    def send_confirmation(self, confirmation: Confirmation) -> None: ...