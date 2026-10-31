# hotel_booking/notifications/internal.py
from __future__ import annotations

from hotel_booking.notifications import Confirmation


class EmailNotificationSender:
    """Simulated: counts the emails it would send and needs no network."""

    def __init__(self) -> None:
        self.sent = 0

    def send_confirmation(self, confirmation: Confirmation) -> None:
        self.sent += 1


class SmsNotificationSender:
    """Simulated, like the email sender."""

    def __init__(self) -> None:
        self.sent = 0

    def send_confirmation(self, confirmation: Confirmation) -> None:
        self.sent += 1