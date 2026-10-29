# Hotel contexts

## Words

| Word | Meaning here | Name in our code |
|---|---|---|
| Stay | Check-in to check-out, half-open: 12–14 Nov = the nights of the 12th and 13th | DateRange |
| Reservation | Guest + room + stay + status, with an id such as R101 | Reservation |
| Confirmed | The room is promised to this guest for these nights | ReservationStatus.CONFIRMED |
| Guest | The person who stays in the hotel and is named on the reservation, for example Maya | Guest |
| Room | One bookable room of the hotel, with a number, for example R7 | Room |
| Room type | The kind of a room, for example Standard (R7) or Deluxe (R8) | Room.type |
| Nightly price | The price of one night in a room; a Deluxe room costs more than a Standard one | not in code yet |
| Out of service | A room that cannot be booked for a period, for example R8 during repairs | not in code yet |
| Cancelled | The reservation was cancelled; it is kept as history and no longer blocks the room | ReservationStatus.CANCELLED |
| Book | Ask for a free room for a stay and get a reservation id, for example Maya books R7 for 12–14 Nov | BookingService.reserve |
| Cancel | Cancel a reservation by its id, for example Maya cancels R101 | BookingService.cancel |
| Free rooms | The rooms that no Confirmed reservation blocks for the nights of a stay | BookingService.find_free_rooms |
| Deposit | 30% of the stay's price, taken when the guest books | not in code yet |
| Paid | The payment for a deposit or a stay was received | not in code yet |
| Declined | The payment was refused, for example the card was rejected | not in code yet |
| Confirmation message | The message that tells the guest the booking is Accepted, by email or SMS | NotificationSender.send_confirmation |
| Sent | The confirmation message was handed to the email or SMS provider | not in code yet (today only a counter: EmailNotificationSender.sent) |
| Failed | The confirmation message could not be sent; the booking stays saved and the failure is reported (R6) | BookingResult.notification_failed |

## Rooms

Job: knows which rooms the hotel sells.

| Word | Meaning here |
|---|---|
| Room | One bookable room of the hotel, with a number, for example R7 |
| Room type | The kind of a room, for example Standard (R7) or Deluxe (R8) |
| Nightly price | The price of one night in a room; a Deluxe room costs more than a Standard one |
| Out of service | A room that cannot be booked for a period, for example R8 during repairs |

Rules this context owns:
- A room that is out of service is not offered to guests.
- The nightly price depends on the room type (Deluxe costs more than Standard).

Needs from other contexts: nothing.
Tells other contexts: the list of rooms, when Reservations asks which rooms exist (Reservations).

## Reservations

Job: decides whether a guest gets a room for some nights, and keeps every reservation.

| Word | Meaning here |
|---|---|
| Stay | Check-in to check-out, half-open: 12–14 Nov = the nights of the 12th and 13th |
| Reservation | Guest + room number + stay + status, with an id such as R101 |
| Confirmed | The room is promised to this guest for these nights |
| Cancelled | The promise is withdrawn; the nights are free again |
| Guest | The person who stays in the hotel and is named on the reservation, for example Maya |
| Book | Ask for a free room for a stay and get a reservation id, for example Maya books R7 for 12–14 Nov |
| Cancel | Cancel a reservation by its id, for example Maya cancels R101 |
| Free rooms | The rooms that no Confirmed reservation blocks for the nights of a stay |

Rules this context owns:
- A room never has two Confirmed reservations that share a night.
- Check-out must be after check-in.
- Cancelling a reservation frees its nights for new bookings.

Needs from other contexts: the list of rooms (Rooms); from P17, the answer Paid or Declined to a deposit request (Payments).
Tells other contexts: ReservationConfirmed (Notifications); from P17, the request to take a deposit (Payments).

## Payments

Job: takes deposits and records whether they were paid.

| Word | Meaning here |
|---|---|
| Deposit | 30% of the stay's price, taken when the guest books |
| Paid | The payment for a deposit or a stay was received |
| Declined | The payment was refused, for example the card was rejected |

Rules this context owns:
- The deposit is 30% of the stay’s price.
- Only a Paid deposit can be refunded.

Needs from other contexts: the reservation id and the amount, when Reservations asks to take a deposit (from P17) (Reservations).
Tells other contexts: Paid or Declined, as the answer to that request (Reservations).

## Notifications

Job: tells guests what happened, by email or SMS.

| Word | Meaning here |
|---|---|
| Confirmation message | The message that tells the guest the booking is Accepted, by email or SMS |
| Sent | The confirmation message was handed to the email or SMS provider |
| Failed | The confirmation message could not be sent; the booking stays saved and the failure is reported (R6) |

Rules this context owns:
- A failed message is recorded as Failed and never changes the reservation.

Needs from other contexts: ReservationConfirmed (Reservations).
Tells other contexts: nothing.

## Same word, different meaning

| Word | Rooms | Reservations | Payments | Notifications |
|---|---|---|---|---|
| Status | In service / out of service | Confirmed / Cancelled | Paid / Declined | Sent / Failed |
| Room | A real room with its own data: R8 is Deluxe, has a nightly price and may be out of service | Only the room number on a reservation, for example R8 | Not used | Just text inside the message, for example "Room R8" |
| Cancel | Take a room off sale | Withdraw a reservation; its nights are free again | Refund a deposit | Not used |

If Notifications could change a reservation's status to Failed, a failed email or SMS could overwrite Confirmed, and Maya would lose R7 only because a message did not arrive. That breaks rule R6: a failed message must never undo or hide a saved booking.

## Rule owners

| Card | Rule | Owner | Why this owner |
|---|---|---|---|
| 1 | A room never has two Confirmed reservations that share a night. | Reservations | It keeps every reservation of the room, so it can check them all together. |
| 2 | Check-out must be after check-in. | Reservations | The stay (check-in and check-out) belongs to the reservation, so Reservations has all the data the rule reads. |
| 3 | Cancelling a reservation frees its nights for new bookings. | Reservations | Cancelling changes the reservation's own status, and Reservations is the one that decides which reservations block a room. |
| 4 | A room that is out of service is not offered to guests. | Rooms | Rooms keeps the out-of-service flag of each room, so it decides which rooms can be sold; Reservations only uses the list. |
| 5 | The nightly price depends on the room type (Deluxe costs more than Standard). | Rooms | Rooms keeps the room type and the nightly price together. |
| 6 | The deposit is 30% of the stay’s price. | Payments | Money rules belong to Payments; it asks Rooms for the nightly price. |
| 7 | Only a Paid deposit can be refunded. | Payments | The deposit and its status (Paid / Declined) are kept in Payments. |
| 8 | A failed message is recorded as Failed and never changes the reservation. | Notifications | Notifications keeps every message and whether it arrived; the reservation status is not its data (R6). |

## Between contexts

### Reservations → Notifications: ReservationConfirmed (event)

Sent when: a reservation is saved as Confirmed.

Fields:
- reservationId: R101
- guestEmail: maya@example.com
- roomNumber: R7
- checkIn: 2026-11-12
- checkOut: 2026-11-14

Reservations does not wait for an answer. A failed message never changes R101 (rule R6).

Never crosses: Reservations’ list of reservations. Notifications never reads it.

### Reservations → Rooms: which rooms exist? (question)

Sent when: a guest searches for free rooms or books, and Reservations needs the rooms the hotel sells.

What Reservations sends: only the question. It carries no fields.

The answer and its fields: one entry for each room that is on sale.
- roomNumber: R7
- roomType: Standard
- (and R8, Deluxe)

Reservations waits for the answer. Rooms leaves out rooms that are out of service (rule card 4), so Reservations never sees them.

Never crosses: Rooms’ nightly prices and repair data. Reservations only gets the number and the type. Rooms never reads the list of reservations.

### Reservations → Payments: take a deposit (question, from P17)

Sent when: a new booking needs its deposit (from P17; today the app takes no deposit).

What Reservations sends:
- reservationId: R101
- amount: the deposit amount in money

The answer and its fields:
- result: Paid or Declined

Reservations waits for the answer and decides what it means for the booking. Payments never changes a reservation’s status.

Never crosses: the guest’s stay dates, the guest’s email and Reservations’ list of reservations. Payments knows only the id and the amount.