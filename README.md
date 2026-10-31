# Hotel Booking App · P06 (modular monolith)

Course: Advanced Software Design & Architecture

A small hotel takes bookings on its website and at the reception desk. This project is the hotel booking app. In P03 it was designed and written as one Python file. In P04 it was refactored behind interfaces. In P05 the hotel's four business areas were written down. In P06 those areas became **four modules** in the code, and architecture checks stop one module from reaching into another's internal code. All data is still kept in memory.

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
| Survive a failed message | The confirmation cannot be sent → the booking stays saved and Accepted, and the failure is reported (R6) |

### The date rule: count nights, not dates
A booking for 12–14 November means the guest sleeps on the night of the 12th and the night of the 13th. On the 14th they check out, so a new guest can check in the same day. This is a half-open date range: the check-in day counts, the check-out day does not.

## Project structure

```
hotel-booking/
├── README.md
├── .gitignore
├── main.py                       wiring and demos: the only app file that names internal code
├── pyproject.toml                the 3 architecture checks (import-linter)
├── test_booking_service.py       8 tests
├── hotel_booking/
│   ├── __init__.py
│   ├── rooms/
│   │   ├── __init__.py           public contract: Room, RoomCatalog
│   │   ├── catalog.py            Room and the RoomCatalog interface
│   │   └── internal.py           InMemoryRoomCatalog
│   ├── reservations/
│   │   ├── __init__.py           public contract: BookingService, BookingResult, DateRange,
│   │   │                         Guest, Reservation, ReservationStatus, ReservationStore
│   │   ├── domain.py             DateRange, Guest, ReservationStatus, Reservation
│   │   ├── booking.py            ReservationStore interface, BookingResult, BookingService
│   │   └── internal.py           InMemoryReservationStore
│   ├── payments/
│   │   ├── __init__.py           public contract: PaymentStatus, PaymentService
│   │   └── internal.py           SimulatedPaymentService
│   └── notifications/
│       ├── __init__.py           public contract: Confirmation, NotificationSender
│       └── internal.py           EmailNotificationSender, SmsNotificationSender
├── docs/
│   ├── requirements.md           requirements R1–R6 with examples and proof lines
│   ├── design-notes.md           written answers from P03, P04 and P06
│   ├── quality-scenarios.md      stakeholders and quality scenarios S1–S6
│   ├── contexts.md               four business contexts: words, rules, owners, borders
│   ├── adr-001-modular-monolith.md   the decision to start as a modular monolith
│   └── draw_io_diagrams/         8 draw.io diagrams (see "Design documents")
└── old/
    └── hotel_booking.py          the P03 version in one file, kept for comparison
```

## How to run

Requirements: Python 3.10 or newer (checked with Python 3.14). The app and the 8 tests need no extra packages. The architecture checks need `import-linter`.

```bash
python main.py              # the normal demo
python main.py --race       # the race demo (two guests, one room)
python -m unittest -v       # the 8 tests
```

On Windows you can also use `py` instead of `python`.

### Architecture checks (install once)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install import-linter
lint-imports                       # the 3 architecture checks
```

Expected result:

```
Reservations uses only the public contracts of other modules KEPT
Rooms does not depend on any other module KEPT
Payments and Notifications do not depend on Reservations KEPT

Contracts: 3 kept, 0 broken.
```

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

This is exactly the same output as in P03 and P04.

### Expected output of the race demo

```
Maya and Omar both book R7 for 12-14 Nov at the same moment...
Maya: Accepted R101
Omar: Accepted R102
Confirmed reservations for R7 on 12-14 Nov: 2
Double booking! Both requests checked before either one saved.
```

## The four modules

Each module is a package with a **public contract** (its `__init__.py`, or `catalog.py` for Rooms) that other modules may use, and **internal code** (`internal.py`) that only the module itself, `main.py` and the tests may use.

| Module | Job | Public contract | Internal code |
|---|---|---|---|
| `rooms` | Knows which rooms the hotel sells | `Room`, `RoomCatalog` | `InMemoryRoomCatalog` |
| `reservations` | Decides whether a guest gets a room for some nights; owns the booking rule | `BookingService`, `BookingResult`, `DateRange`, `Guest`, `Reservation`, `ReservationStatus`, `ReservationStore` | `InMemoryReservationStore` |
| `payments` | Takes deposits and records whether they were paid | `PaymentStatus`, `PaymentService` | `SimulatedPaymentService` |
| `notifications` | Tells guests what happened, by email or SMS | `Confirmation`, `NotificationSender` | `EmailNotificationSender`, `SmsNotificationSender` |

Payments has a contract and a simulated implementation, but nothing calls it yet. The booking saga uses it in P17.

### Dependencies between modules

```
reservations ──► rooms
reservations ──► notifications
payments         (not used yet)
```

`rooms` and `notifications` depend on no other module. Notifications has its own `Confirmation` message (reservation id, guest email, room number, check-in, check-out), so it never needs the `Reservation` class.

### Architecture checks

Three rules from the P05 design run as `import-linter` contracts (configured in `pyproject.toml`):

1. Reservations uses only the public contracts of other modules: it never imports another module's `internal` code.
2. Rooms does not depend on any other module.
3. Payments and Notifications do not depend on Reservations.

These checks read import lines, so they are separate from the unit tests: a forbidden import can pass all 8 tests and still fail `lint-imports`. Run both.

## How it works

### What happens when a guest books a room (`reserve`)

1. Are the dates valid (check-out after check-in)? If not → **InvalidDates**, nothing is saved.
2. Does a Confirmed booking already have this room on one of these nights? If yes → **Unavailable**, nothing is saved.
3. Create the reservation (id R101, R102, …) with status Confirmed and save it in the store.
4. Send a `Confirmation` through the notification sender. If sending fails, the booking stays saved and the result says `notification_failed` (R6).
5. Answer **Accepted** with the reservation id.

### Cancelling
`cancel(id)` finds the reservation and changes its status to Cancelled. Nothing is deleted: the booking stays in the store as history, but a Cancelled booking no longer blocks the room.

### The wiring
`main.py` is the only app file that chooses the real classes: the room catalog, the reservation store and the email sender. The tests may also name internal classes, because they build the app for one situation.

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
| `8-modules.drawio` | The P06 modules: Reservations uses the public contracts; the red arrow is the forbidden dependency |

Other documents in `docs/`:

- `design-notes.md`: written answers from every practice, including the P06 sections Before, Modules, Architecture rules, Broken on purpose and After.
- `quality-scenarios.md`: stakeholders and six measured quality scenarios (S1–S6).
- `contexts.md`: the hotel's words, the four contexts, the owner of each rule and what crosses each border.
- `adr-001-modular-monolith.md`: why the app starts as one app with four modules, and when to revisit the decision.

## Known problem: the race condition

`reserve` first **checks** ("is the room free?") and then **saves**. If two requests arrive at almost the same moment, both can check before either one saves, so both see a free room and both are Accepted. The result is two Confirmed reservations for the same room and nights, which breaks requirement R3 (and scenario S2). Run `python main.py --race` to see it.

Refactoring and splitting into modules do not fix bugs, so the problem is still there. A lock in the code would only help while the app runs as one program on one computer. The proper fix (database locks and constraints) comes in P09.

## Limits of this version

- Reservations are kept in memory and disappear when the program ends.
- No prices, payments, invoices, logins or housekeeping; Payments is a contract with a simulated class that nothing calls yet.
- Email and SMS confirmations are simulated (only counted).
- The architecture checks guard the module borders only while `lint-imports` runs (there is no automatic build yet).
- The race condition described above is still present.

## What comes next

| Practice | What changes |
|---|---|
| L04 | System design: how many requests, HTTP, a database, and when a cache helps |
| P07 | An HTTP API (`GET /rooms/availability`, `POST /reservations`, `DELETE /reservations/{id}`) with PostgreSQL; the new store plugs in through the wiring |
| P08 | A cache for the free-room search, with the gain measured |
| P09 | Fix the race with database locks and constraints |
| P17 | The booking saga: hold the room, take the deposit (Payments), confirm, or undo |