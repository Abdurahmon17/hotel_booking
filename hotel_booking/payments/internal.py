# hotel_booking/payments/internal.py
from __future__ import annotations

from decimal import Decimal

from hotel_booking.payments import PaymentStatus


class SimulatedPaymentService:
    """Simulated: no card and no network. A positive amount is Paid; anything else is Declined."""

    def take_deposit(self, reservation_id: str, amount: Decimal) -> PaymentStatus:
        return PaymentStatus.PAID if amount > 0 else PaymentStatus.DECLINED