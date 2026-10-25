# Hotel Booking App · P03 (version 1)

Course: Advanced Software Design & Architecture

A small hotel takes bookings on its website and at the reception desk. This project is the first version of the app that handles those bookings: it is designed first (requirements and UML diagrams) and then written in Python. All data is kept in memory.

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

### The date rule: count nights, not dates
A booking for 12–14 November means the guest sleeps on the night of the 12th and the night of the 13th. On the 14th they check out, so a new guest can check in the same day. This is a half-open date range: the check-in day counts, the check-out day does not.

## Project structure

```
hotel-booking/
├── README.md              this file
├── hotel_booking.py       the program (all classes in one file)
└── docs/
    ├── requirements.md    requirements R1–R5 with examples and proof lines
    ├── design-notes.md    short answers from each step of the practice
    └── diagrams.drawio    5 pages: Use cases, Classes,
                           Sequence - book, Sequence - cancel, Activity - book
```

## How to run

Requirements: Python 3.10 or newer (checked with Python 3.14). No extra packages are needed.

```bash
cd hotel-booking
python hotel_booking.py            # the normal demo
python hotel_booking.py --race     # the race demo (two guests, one room)
```

On Windows you can also use `py hotel_booking.py`.

### Expected output of the normal demo

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

### Expected output of the race demo

```
Maya and Omar both book R7 for 12-14 Nov at the same moment...
Maya: Accepted R101
Omar: Accepted R102
Confirmed reservations for R7 on 12-14 Nov: 2
Double booking! Both requests checked before either one saved.
```

## How it works

The code follows the class diagram: each box is one class.

| Class | What it keeps | What it does |
|---|---|---|
| `DateRange` | check-in and check-out dates | `is_valid()` checks that check-out is after check-in; `overlaps(other)` says whether two stays share a night |
| `Guest` | name, email | plain data |
| `Room` | number, type | plain data (R7 Standard, R8 Deluxe) |
| `ReservationStatus` | Confirmed, Cancelled | the only two allowed statuses |
| `Reservation` | id, guest, room, stay, status | `blocks(room, stay)` says whether it blocks a room for given nights; `cancel()` changes its own status |
| `ReservationStore` | the list of all reservations | `has_overlap`, `save`, `find`, `count_confirmed` |
| `EmailSender` | a counter of confirmations | `send_confirmation` (simulated: sends nothing, only counts) |
| `BookingResult` | outcome and reservation id | what `reserve` returns: Accepted, Unavailable or InvalidDates |
| `BookingService` | the rooms, the store, the email sender | `find_free_rooms`, `reserve`, `cancel` run each request in order |

### What happens when a guest books a room (`reserve`)

1. Are the dates valid (check-out after check-in)? If not → **InvalidDates**, nothing is saved.
2. Does a Confirmed booking already have this room on one of these nights? If yes → **Unavailable**, nothing is saved.
3. Create the reservation (id R101, R102, …) with status Confirmed and save it in the store.
4. Send the confirmation email.
5. Answer **Accepted** with the reservation id.

### Cancelling
`cancel(id)` finds the reservation and changes its status to Cancelled. Nothing is deleted: the booking stays in the store as history, but a Cancelled booking no longer blocks the room.

## Requirements

| ID | Requirement | Proof (program output) |
|---|---|---|
| R1 · Search | List the rooms that are free for given dates | `Free rooms 12-14 Nov: R7, R8` |
| R2 · Book | Book a free room and get a reservation id | `Maya books R7 12-14 Nov: Accepted R101` |
| R3 · No clash | A room never has two Confirmed bookings on the same night; check-out must be after check-in | `Omar books R7 13-15 Nov: Unavailable`, `Omar books R8 15-15 Nov: InvalidDates` |
| R4 · Cancel | A cancelled booking is kept as Cancelled and no longer blocks the room | `Maya cancels R101: True` |
| R5 · View | Look up a booking by its id | `Maya cancels R101: True` (cancel finds R101 with `find`) |

Full details are in `docs/requirements.md`.

## Design documents

All diagrams are in `docs/diagrams.drawio` (open it at app.diagrams.net, File → Open from → Device).

| Page | What it shows |
|---|---|
| Use cases | Who uses the app (Guest, Receptionist) and for which goals |
| Classes | The 8 classes, their data and methods, and how they are linked |
| Sequence - book | The messages when Maya books R7 for 12–14 November |
| Sequence - cancel | The messages when Maya cancels R101 |
| Activity - book | The decisions of a booking request and the paths where it stops |

`docs/design-notes.md` contains the written answers: why we design before coding, where the methods live, the activity traces, the prediction and the race explanation.

## Known problem: the race condition

`reserve` first **checks** ("is the room free?") and then **saves**. If two requests arrive at almost the same moment, both can check before either one saves, so both see a free room and both are Accepted. The result is two Confirmed reservations for the same room and nights, which breaks requirement R3. Run `python hotel_booking.py --race` to see it.

This is not fixed in version 1. A lock in the code would only help while the app runs as one program on one computer. The proper fix (database locks and constraints) comes in P09.

## Limits of version 1

- Reservations are kept in memory and disappear when the program ends.
- No prices, payments, invoices, logins or housekeeping.
- Confirmation emails are simulated (only counted).
- The race condition described above is still present.

## What comes next

| Practice | What changes |
|---|---|
| P04 | SOLID: `BookingService` stops depending directly on `EmailSender` |
| P05 · P06 | Split the hotel into business areas and modules |
| P07 · P08 | HTTP API, PostgreSQL and a cache for search |
| P09 | Fix the race with database locks and constraints |
