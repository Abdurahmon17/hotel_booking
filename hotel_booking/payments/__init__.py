# hotel_booking/payments/__init__.py
"""Payments: deposits and whether they were paid. Public contract: PaymentStatus and PaymentService."""
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Protocol


class PaymentStatus(Enum):
    PAID = "Paid"
    DECLINED = "Declined"


class PaymentService(Protocol):
    """Booking does not call it yet: the booking saga uses it in P17."""

    def take_deposit(self, reservation_id: str, amount: Decimal) -> PaymentStatus: ...