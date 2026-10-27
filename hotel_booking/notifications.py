# hotel_booking/notifications.py
from __future__ import annotations

from typing import Protocol

from hotel_booking.domain import Reservation


class NotificationSender(Protocol):
    """What BookingService needs: "tell the guest". How the message travels is not its business."""

    def send_confirmation(self, reservation: Reservation) -> None: ...


class EmailNotificationSender:
    """Simulated: counts the emails it would send and needs no network."""

    def __init__(self) -> None:
        self.sent = 0

    def send_confirmation(self, reservation: Reservation) -> None:
        self.sent += 1


class SmsNotificationSender:
    """Added in Step 7 without changing BookingService. Simulated, like the email sender."""

    def __init__(self) -> None:
        self.sent = 0

    def send_confirmation(self, reservation: Reservation) -> None:
        self.sent += 1