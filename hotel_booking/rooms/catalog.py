# hotel_booking/rooms/catalog.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Room:
    number: str
    type: str


class RoomCatalog(Protocol):
    """Rooms' public contract: which rooms the hotel sells. From P07 they come from a database."""

    def all(self) -> list[Room]: ...