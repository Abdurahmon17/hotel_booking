# Hotel Booking App · P07 (HTTP API and PostgreSQL)

Course: Advanced Software Design & Architecture

A small hotel takes bookings on its website and at the reception desk. This project is the hotel booking app. It was designed and written as one Python file (P03), refactored behind interfaces (P04), described in four business contexts (P05) and split into four modules with architecture checks (P06). In P07 it became a **web app** on `http://localhost:5080`, and its reservations moved into **PostgreSQL**.

**The one rule of the whole course:** one room, one night, at most one guest.

## What the app does

| Job | HTTP | Example |
|---|---|---|
| Search free rooms | `GET /rooms/availability?checkIn=...&checkOut=...` | 12–14 Nov → R7, R8 |
| Book a room | `POST /reservations` | Maya books R7 for 12–14 Nov → `201`, id R101 |
| Refuse a clash | `POST /reservations` | Omar asks for R7 on 13–15 Nov → `409 Unavailable` |
| Refuse bad dates | `POST /reservations` | Omar asks for R8 on 15–15 Nov → `400 InvalidDates` |
| Cancel a booking | `DELETE /reservations/{id}` | R101 → `204`; again → `404 NotFound` |
| Survive a failed message | | The confirmation cannot be sent → the booking stays saved and Accepted, and `notificationFailed` is true (R6) |

The API contract is `docs/openapi.yaml`; the running app serves it at `http://localhost:5080/openapi.yaml`.

### The date rule: count nights, not dates
A booking for 12–14 November means the guest sleeps on the night of the 12th and the night of the 13th. On the 14th they check out, so a new guest can check in the same day. This is a half-open date range: the check-in day counts, the check-out day does not.

## Project structure

```
hotel-booking/
├── README.md
├── .gitignore
├── main.py                       wiring and demos: the only app file that names internal code
├── docker-compose.yml            PostgreSQL 18 (Docker or Podman)
├── pyproject.toml                the 3 architecture checks (import-linter)
├── requirements.txt              fastapi, uvicorn, sqlalchemy, psycopg, httpx, import-linter
├── test_booking_service.py       8 behaviour tests (list store)
├── test_api.py                   4 API tests (list store, no server, no database)
├── db/
│   └── init.sql                  the rooms and reservations tables, with R7 and R8
├── hotel_booking/
│   ├── __init__.py
│   ├── api.py                    the three endpoints (outside the four modules)
│   ├── rooms/                    catalog.py (Room, RoomCatalog), internal.py (list and PostgreSQL catalogs)
│   ├── reservations/             domain.py, booking.py (BookingService), internal.py (list and PostgreSQL stores)
│   ├── payments/                 PaymentStatus, PaymentService, simulated payment (not called yet)
│   └── notifications/            Confirmation, NotificationSender, email and SMS senders (simulated)
├── docs/
│   ├── requirements.md           requirements R1–R6
│   ├── design-notes.md           written answers from P03 to P07
│   ├── quality-scenarios.md      stakeholders and quality scenarios S1–S6
│   ├── contexts.md               four business contexts: words, rules, owners, borders
│   ├── adr-001-modular-monolith.md
│   ├── capacity.md               capacity estimate for the app
│   ├── openapi.yaml              the API contract
│   ├── api-check.md              seven requests against PostgreSQL and the restart check
│   ├── requests/                 request bodies for curl (maya-r7, omar-r7, omar-r8)
│   └── draw_io_diagrams/         8 draw.io diagrams
└── old/
    └── hotel_booking.py          the P03 version in one file, kept for comparison
```

## How to run

Requirements: Python 3.10 or newer, and Docker or Podman for PostgreSQL.

### 1. Install the packages (once)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 2. Start PostgreSQL

```bash
docker compose up -d               # with Podman: podman-compose up -d
docker compose ps                  # the service db is Up
```

`db/init.sql` runs once, when the database is first created. To start again from an empty database: `docker compose down -v`, then `up -d`. Stop it with `docker compose down` (without `-v` the data is kept).

If port 5432 is taken on your laptop, change the port in `docker-compose.yml` (for example `"5433:5432"`) and start the app with `HOTEL_DB_PORT=5433 python main.py`.

### 3. Run

```bash
python main.py                     # the API on http://localhost:5080 (PostgreSQL)
python main.py --demo              # the console demo, data in lists
python main.py --race              # two guests book the same room at the same moment
```

### 4. Check

```bash
python -m unittest -v              # 12 tests: 8 behaviour + 4 API
lint-imports                       # 3 architecture contracts
```

Expected: `Ran 12 tests ... OK` and `Contracts: 3 kept, 0 broken.` (15 green checks).

### Try the API with curl

```bash
curl -s -w "\n%{http_code}\n" "http://localhost:5080/rooms/availability?checkIn=2026-11-12&checkOut=2026-11-14"
curl -s -w "\n%{http_code}\n" -X POST -H "Content-Type: application/json" --data "@docs/requests/maya-r7.json" http://localhost:5080/reservations
curl -s -w "\n%{http_code}\n" -X DELETE http://localhost:5080/reservations/R101
```

All seven requests with their expected answers are in `docs/api-check.md`. Run `python main.py` from the project folder: the app reads `docs/openapi.yaml` with a relative path.

### Expected output of `--demo`

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

### Expected output of `--race`

```
Maya and Omar both book R7 for 12-14 Nov at the same moment...
Maya: Accepted R101
Omar: Accepted R102
Confirmed reservations for R7 on 12-14 Nov: 2
Double booking! Both requests checked before either one saved.
```

## The API

| Operation | Success | Errors |
|---|---|---|
| `GET /rooms/availability?checkIn&checkOut[&limit&after]` | `200` with the free rooms and `next` | `400 InvalidDates`, `400 InvalidRequest` |
| `POST /reservations` | `201 {"id":"R101","status":"Confirmed","notificationFailed":false}` | `409 Unavailable`, `400 InvalidDates`, `400 UnknownRoom`, `400 InvalidRequest` |
| `DELETE /reservations/{id}` | `204`, no body | `404 NotFound` |

Errors are problem details (RFC 9457, `application/problem+json`) with `title`, `status` and `detail`. A client compares the `title`; `detail` is a sentence for people. Free rooms come in text order of the room number (R10 before R7), and `after` is compared as text too.

## The four modules

Each module is a package with a **public contract** that other modules may use and **internal code** (`internal.py`) that only the module itself, `main.py` and the tests may use.

| Module | Job | Public contract | Internal code |
|---|---|---|---|
| `rooms` | Knows which rooms the hotel sells | `Room`, `RoomCatalog` | `InMemoryRoomCatalog`, `PostgresRoomCatalog` |
| `reservations` | Owns the booking rule | `BookingService`, `BookingResult`, `DateRange`, `Guest`, `Reservation`, `ReservationStatus`, `ReservationStore` | `InMemoryReservationStore`, `PostgresReservationStore` |
| `payments` | Takes deposits and records whether they were paid | `PaymentStatus`, `PaymentService` | `SimulatedPaymentService` |
| `notifications` | Tells guests what happened | `Confirmation`, `NotificationSender` | `EmailNotificationSender`, `SmsNotificationSender` |

`api.py` is outside the four modules and uses only their public contracts. `main.py` is the wiring: it picks the PostgreSQL stores for the web app and the list stores for `--demo`, `--race` and the tests. `BookingService` did not change when PostgreSQL arrived: that is what the interfaces from P04 are for.

### Architecture checks

Three rules run as `import-linter` contracts (`pyproject.toml`): Reservations uses only the public contracts of other modules; Rooms depends on no other module; Payments and Notifications do not depend on Reservations. They read import lines, so run them next to the tests.

### One request through the app

`DELETE /reservations/R101`: the endpoint asks the unit of work for a `BookingService`; `Cancel` finds R101 through `PostgresReservationStore` (a `SELECT`); the reservation changes its own status; at the end of the request the store writes the change with one `UPDATE`.

## Requirements

| ID | Requirement | Proof |
|---|---|---|
| R1 · Search | List the rooms that are free for given dates | `GET /rooms/availability` → R7, R8 |
| R2 · Book | Book a free room and get a reservation id | `POST /reservations` → `201 R101` |
| R3 · No clash | A room never has two Confirmed bookings on the same night; check-out must be after check-in | `409 Unavailable`, `400 InvalidDates` |
| R4 · Cancel | A cancelled booking is kept as Cancelled and no longer blocks the room | `DELETE /reservations/R101` → `204` |
| R5 · View | Look up a booking by its id | the cancel path finds R101 by id |
| R6 · Failed message | If the confirmation cannot be sent, the booking stays saved and Accepted, and the failure is reported | `test_a_failed_confirmation_keeps_the_booking` |

Details are in `docs/requirements.md`.

## Design documents

- `docs/draw_io_diagrams/`: use cases, classes, sequence (book, cancel), activity, classes after P04, the context map and the modules diagram.
- `docs/capacity.md`: the estimate (3.33 searches a second at the peak = 200 a minute; 133 database queries a second; 4.38 MB a year).
- `docs/openapi.yaml`: the API contract; open it in the Swagger editor (editor.swagger.io).
- `docs/design-notes.md`: written answers from every practice, including the API decisions and API tests of P07.
- `docs/adr-001-modular-monolith.md`: why the app starts as one app with four modules.

## Known problem: the race condition

`reserve` first **checks** ("is the room free?") and then **saves**. If two requests arrive at almost the same moment, both can check before either one saves, so both are Accepted. The result is two Confirmed reservations for the same room and nights, which breaks requirement R3 and scenario S2. Run `python main.py --race` to see it.

PostgreSQL does not fix this by itself: the primary key stops a second `R101`, but nothing stops two different reservations of the same room and nights. P09 fixes it in the database.

## Limits of this version

- The race condition above is still present.
- The database password (`hotel`) is for a laptop only.
- No prices, payments, invoices or logins; Payments is a contract with a simulated class that nothing calls yet.
- Email and SMS confirmations are simulated.
- Every search asks PostgreSQL once per room (40 questions per search at the peak): P08 measures it and adds a cache.
- The API tests use the list store; the PostgreSQL stores are checked with the requests in `docs/api-check.md`.

## What comes next

| Practice | What changes |
|---|---|
| P08 | Measure 1,000 searches, add a Redis cache for the search, measure again and see the stale-cache risk |
| L05 | Transactions, locks and isolation: why two requests at the same moment can still both book R7 |
| P09 | Reproduce the double booking with two HTTP calls and fix it in PostgreSQL |
| P17 | The booking saga: hold the room, take the deposit (Payments), confirm, or undo |