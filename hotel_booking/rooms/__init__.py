# hotel_booking/rooms/__init__.py
"""Rooms: which rooms the hotel sells. Public contract: Room and RoomCatalog."""
from hotel_booking.rooms.catalog import Room, RoomCatalog

__all__ = ["Room", "RoomCatalog"]