# Hotel Booking App · P05 (business contexts)

Course: Advanced Software Design & Architecture

A small hotel takes bookings on its website and at the reception desk. This project is the hotel booking app. In P03 it was designed (requirements and UML diagrams) and written as one Python file. In P04 the same app was **refactored**: its behaviour did not change, but its design is now easy to change. In P05 the hotel's business areas were written down (no code changed). All data is still kept in memory.

**The one rule of the whole course:** one room, one night, at most one guest.

## What the app does

| Job | Example |
|---|---|
| Search free rooms | Which rooms are free from 12 to 14 November? → R7, R8 |
| Book a room | Maya books R7 for 12–14 November → Accepted R101 |
| Refuse a clash | Omar asks for R7 on 13–15 November → Unavailable |
| Refuse bad dates | Omar asks for R8 on 15–15 November → InvalidDates |
| Cancel a booking | Maya cancels R101 → R7 is free again for those nights |
| View a booking | Look up R101 → Maya, R7, 12–14 November, Confirmed |
| Survive a failed message | The confirmation cannot be sent → the booking stays saved and Accepted, and the failure is reported (R6, new in P04) |

### The date rule: count nights, not dates
A booking for 12–14 November means the guest sleeps on the night of the 12th and the night of the 13th. On the 14th they check out, so a new guest can check in the same day. This is a half-open date range: the check-in day counts, the check-out day does not.

## Project structure

```
hotel-booking/
├── README.md                  this file
├── .gitignore
├── main.py                    entry point: the demo and the race demo
├── test_booking_service.py    8 tests
├── hotel_booking/
│   ├── __init__.py            exports the public classes
│   ├── domain.py              DateRange, Guest, Room, ReservationStatus, Reservation
│   ├── stores.py              ReservationStore (interface) + InMemoryReservationStore
│   ├── notifications.py       NotificationSender (interface) + Email and SMS senders
│   └── booking.py             BookingService, BookingResult
├── docs/
│   ├── requirements.md        requirements R1–R6 with examples and proof lines
│   ├── design-notes.md        written answers from P03 and P04
│   ├── quality-scenarios.md   stakeholders and quality scenarios S1–S6 (P05)
│   ├── contexts.md            four business contexts, their words, rules and borders (P05)
│   └── draw_io_diagrams/      7 draw.io diagrams (see "Design documents")
└── old/
    └── hotel_booking.py       the P03 version in one file, kept for comparison
```

## How to run

Requirements: Python 3.10 or newer (checked with Python 3.14). No extra packages are needed.

```bash
python main.py              # the normal demo
python main.py --race       # the race demo (two guests, one room)
python -m unittest -v       # the 8 tests
```

On Windows you can also use `py` instead of `python`.

### Expected output of the demo

```
Free rooms 12-14 Nov: R7, R8
Maya books R7 12-14 Nov: Accepted R101
Omar books R7 13-15 Nov: Unavailable
Nora books R7 14-16 Nov: Accepted R102
Omar books R8 15-15 Nov: InvalidDates
Free rooms 12-14 Nov: R8
Maya cancels R101: True
Free rooms 12-14 Nov: R7, R8
Confirmation emails sent: 2
```

This is exactly the same output as the P03 version.

### Expected output of the race demo

```
Maya and Omar both book R7 for 12-14 Nov at the same moment...
Maya: Accepted R101
Omar: Accepted R102
Confirmed reservations for R7 on 12-14 Nov: 2
Double booking! Both requests checked before either one saved.
```

### Expected output of the tests

```
Ran 8 tests in 0.00Xs

OK
```

## How it works

### Classes

| Class | Where | What it keeps | What it does |
|---|---|---|---|
| `DateRange` | `domain.py` | check-in and check-out dates | `is_valid()` checks that check-out is after check-in; `overlaps(other)` says whether two stays share a night |
| `Guest` | `domain.py` | name, email | plain data |
| `Room` | `domain.py` | number, type | plain data (R7 Standard, R8 Deluxe) |
| `ReservationStatus` | `domain.py` | Confirmed, Cancelled | the only two allowed statuses |
| `Reservation` | `domain.py` | id, guest, room, stay, status | `blocks(room, stay)` says whether it blocks a room for given nights; `cancel()` changes its own status |
| `ReservationStore` | `stores.py` | (interface) | the promise: `count`, `has_overlap`, `save`, `find`, `count_confirmed` |
| `InMemoryReservationStore` | `stores.py` | a list of reservations | keeps the promise with a list in memory |
| `NotificationSender` | `notifications.py` | (interface) | the promise: `send_confirmation(reservation)` |
| `EmailNotificationSender` | `notifications.py` | a counter | simulated email: only counts confirmations |
| `SmsNotificationSender` | `notifications.py` | a counter | simulated SMS: only counts confirmations |
| `BookingResult` | `booking.py` | outcome, reservation id, `notification_failed` | what `reserve` returns: Accepted, Unavailable or InvalidDates |
| `BookingService` | `booking.py` | the rooms, a store, a sender | `find_free_rooms`, `reserve`, `cancel` run each request in order |

### What happens when a guest books a room (`reserve`)

1. Are the dates valid (check-out after check-in)? If not → **InvalidDates**, nothing is saved.
2. Does a Confirmed booking already have this room on one of these nights? If yes → **Unavailable**, nothing is saved.
3. Create the reservation (id R101, R102, …) with status Confirmed and save it in the store.
4. Send the confirmation through the notification sender. If sending fails, the booking stays saved and the result says `notification_failed` (R6).
5. Answer **Accepted** with the reservation id.

### Cancelling
`cancel(id)` finds the reservation and changes its status to Cancelled. Nothing is deleted: the booking stays in the store as history, but a Cancelled booking no longer blocks the room.

## What changed in P04 (refactoring)

Refactoring changes how the code is organised, not what it does.

| Before (P03) | After (P04) |
|---|---|
| `BookingService` asked for exactly `ReservationStore` and `EmailSender` | `BookingService` asks for two interfaces: `ReservationStore` and `NotificationSender` |
| `EmailSender` | renamed `EmailNotificationSender` |
| `ReservationStore` (a list) | renamed `InMemoryReservationStore`; the name `ReservationStore` now belongs to the interface |
| all classes in one file | one module per job: `domain`, `stores`, `notifications`, `booking` |
| `python hotel_booking.py` | `python main.py`, the only place that chooses the real store and sender |

In Python the interfaces are written with `typing.Protocol`: a class keeps the promise by having the right methods, no declaration is needed.

### What it makes easy (Step 7)

- **A fake sender in the tests:** `FakeNotificationSender` remembers which reservations it would confirm, and can fail on purpose.
- **A new rule, R6:** a failed confirmation must not lose a booking. The test was written first and failed, then `reserve` was changed.
- **SMS confirmations:** `SmsNotificationSender` is a new class. Adding it needed no change to `BookingService`.

## Requirements

| ID | Requirement | Proof |
|---|---|---|
| R1 · Search | List the rooms that are free for given dates | `Free rooms 12-14 Nov: R7, R8` |
| R2 · Book | Book a free room and get a reservation id | `Maya books R7 12-14 Nov: Accepted R101` |
| R3 · No clash | A room never has two Confirmed bookings on the same night; check-out must be after check-in | `Omar books R7 13-15 Nov: Unavailable`, `Omar books R8 15-15 Nov: InvalidDates` |
| R4 · Cancel | A cancelled booking is kept as Cancelled and no longer blocks the room | `Maya cancels R101: True` |
| R5 · View | Look up a booking by its id | `Maya cancels R101: True` (cancel finds R101 with `find`) |
| R6 · Failed message | If the confirmation cannot be sent, the booking stays saved and Accepted, and the failure is reported | `test_a_failed_confirmation_keeps_the_booking` passes |

Full details are in `docs/requirements.md`.

## Tests

`test_booking_service.py` has 8 tests:

| Test | What it checks |
|---|---|
| `test_maya_gets_r7_when_it_is_free` | a free room is accepted with id R101 |
| `test_omar_is_refused_when_a_night_is_shared` | a clash is Unavailable and nothing is saved |
| `test_nora_can_arrive_on_the_day_maya_leaves` | a stay that starts on the check-out day is accepted |
| `test_check_out_must_be_after_check_in` | 15–15 is InvalidDates and nothing is saved |
| `test_cancelling_frees_the_room_again` | after cancelling, the room is free again |
| `test_one_confirmation_per_accepted_booking` | the fake sender received exactly R101 and R102 |
| `test_a_failed_confirmation_keeps_the_booking` | R6: a failing sender does not lose the booking |
| `test_sms_confirmations_need_no_change_to_booking_service` | the SMS sender plugs in without changing `BookingService` |

## Design documents

The diagrams are in `docs/draw_io_diagrams/` (open them at app.diagrams.net, File → Open from → Device).

| File | What it shows |
|---|---|
| `1-use-cases.drawio` | Who uses the app (Guest, Receptionist) and for which goals |
| `2-classes.drawio` | The P03 classes, their data and methods, and how they are linked |
| `3-sequence-book.drawio` | The messages when Maya books R7 for 12–14 November |
| `4-sequence-cancel.drawio` | The messages when Maya cancels R101 |
| `5-activity-book.drawio` | The decisions of a booking request and the paths where it stops |
| `6-classes-after.drawio` | The P04 design: 2 interfaces, 5 classes, `uses` and `implements` |
| `7-context-map.drawio` | The P05 context map: 4 contexts and 3 arrows, all starting at Reservations |

`docs/design-notes.md` contains the written answers: why we design before coding, where the methods live, the activity traces, the race explanation (P03), and the refactoring rule, what our code broke and the proof that nothing changed (P04).

## Business contexts (P05)

P05 changed no code. It wrote down which business area owns what, so that P06 can turn each area into a module.

| Context | Job | Rules it owns |
|---|---|---|
| Rooms (Inventory) | Knows which rooms the hotel sells | out-of-service rooms are not offered; the nightly price depends on the room type |
| Reservations | Decides whether a guest gets a room for some nights, and keeps every reservation | no two Confirmed reservations share a night; check-out after check-in; cancelling frees the nights |
| Payments | Takes deposits and records whether they were paid | the deposit is 30% of the stay's price; only a Paid deposit can be refunded |
| Notifications | Tells guests what happened, by email or SMS | a failed message is recorded as Failed and never changes the reservation |

Arrows on the context map (all start at Reservations):

- Reservations → Rooms: question "which rooms exist?"
- Reservations → Payments: question "take a deposit" (from P17)
- Reservations → Notifications: event `ReservationConfirmed` (reservation id, guest email, room number, check-in, check-out)

`docs/quality-scenarios.md` lists the stakeholders and six measured quality scenarios (S1 performance, S2 data integrity, S3 availability, S4 security, S5 modifiability, S6 sustainability). `docs/contexts.md` holds the hotel's words, the contexts, the words that mean different things in different contexts, the owner of each of eight rules, and what crosses each border.

## Known problem: the race condition

`reserve` first **checks** ("is the room free?") and then **saves**. If two requests arrive at almost the same moment, both can check before either one saves, so both see a free room and both are Accepted. The result is two Confirmed reservations for the same room and nights, which breaks requirement R3. Run `python main.py --race` to see it.

Refactoring does not fix bugs, so the problem is still there. A lock in the code would only help while the app runs as one program on one computer. The proper fix (database locks and constraints) comes in P09.

## Limits of this version

- Reservations are kept in memory and disappear when the program ends.
- No prices, payments, invoices, logins or housekeeping.
- Email and SMS confirmations are simulated (only counted).
- The race condition described above is still present.

## What comes next

| Practice | What changes |
|---|---|
| P06 | Turn each context into a module with a public contract; Notifications gets its own `Confirmation` type; the same 8 tests and nine demo lines |
| L04 | System design: how many requests, HTTP, a database, and when a cache helps |
| P07 · P08 | A PostgreSQL store that keeps the `ReservationStore` promise, an HTTP API and a cache for search; `BookingService` does not change |
| P09 | Fix the race with database locks and constraints |