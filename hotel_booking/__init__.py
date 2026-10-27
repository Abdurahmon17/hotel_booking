# hotel_booking/__init__.py
"""Hotel booking app after P04: the P03 app split into modules, with its dependencies behind protocols."""
from hotel_booking.booking import BookingResult, BookingService
from hotel_booking.domain import DateRange, Guest, Reservation, ReservationStatus, Room
from hotel_booking.notifications import EmailNotificationSender, NotificationSender, SmsNotificationSender
from hotel_booking.stores import InMemoryReservationStore, ReservationStore

__all__ = [
    "BookingResult", "BookingService", "DateRange", "EmailNotificationSender", "Guest",
    "InMemoryReservationStore", "NotificationSender", "Reservation", "ReservationStatus",
    "ReservationStore", "Room", "SmsNotificationSender",
]