# Hotel Booking App · P08 (measured search with a Redis cache)

Course: Advanced Software Design & Architecture

A small hotel takes bookings on its website and at the reception desk. This project is the hotel booking app. It was designed and written as one Python file (P03), refactored behind interfaces (P04), described in four business contexts (P05), split into four modules with architecture checks (P06), and put behind an HTTP API with PostgreSQL (P07). In P08 the free-room search was **measured**, **cached in Redis**, and measured again.

**The one rule of the whole course:** one room, one night, at most one guest.

## What the app does

| Job | HTTP | Example |
|---|---|---|
| Search free rooms | `GET /rooms/availability?checkIn=...&checkOut=...` | 12–14 Nov → R7, R8 |
| Book a room | `POST /reservations` | Maya books R7 for 12–14 Nov → `201`, id R101 |
| Refuse a clash | `POST /reservations` | Omar asks for R7 on 13–15 Nov → `409 Unavailable` |
| Refuse bad dates | `POST /reservations` | Omar asks for R8 on 15–15 Nov → `400 InvalidDates` |
| Cancel a booking | `DELETE /reservations/{id}` | R101 → `204`; again → `404 NotFound` |
| Count what searches cost | `GET /stats` | `{"searches":1000,"databaseQueries":2,"cacheHits":999,"cacheMisses":1}` |
| Survive a failed message | | The confirmation cannot be sent → the booking stays saved and Accepted, and `notificationFailed` is true (R6) |

The API contract is `docs/openapi.yaml` (version 1.1.0); the running app serves it at `http://localhost:5080/openapi.yaml`.

### The date rule: count nights, not dates
A booking for 12–14 November means the guest sleeps on the night of the 12th and the night of the 13th. On the 14th they check out, so a new guest can check in the same day. This is a half-open date range: the check-in day counts, the check-out day does not.

## Project structure

```
hotel-booking/
├── README.md
├── .gitignore
├── main.py                       wiring and demos: the only app file that names internal code
├── docker-compose.yml            PostgreSQL 18 and Redis 8 (Docker or Podman)
├── pyproject.toml                the 3 architecture checks (import-linter)
├── requirements.txt              fastapi, uvicorn, sqlalchemy, psycopg, httpx, redis, import-linter
├── test_booking_service.py       8 behaviour tests (list store)
├── test_api.py                   6 API tests (list store and a dictionary cache; no server, no database, no Redis)
├── db/
│   └── init.sql                  the rooms and reservations tables, with R7 and R8
├── hotel_booking/
│   ├── __init__.py
│   ├── api.py                    the endpoints, GET /stats, the counters, cache use and invalidation
│   ├── api_cache.py              the Redis cache: key, TTL 30 s, version
│   ├── rooms/                    catalog.py (Room, RoomCatalog), internal.py (list and PostgreSQL catalogs)
│   ├── reservations/             domain.py, booking.py (BookingService), internal.py (list and PostgreSQL stores)
│   ├── payments/                 PaymentStatus, PaymentService, simulated payment (not called yet)
│   └── notifications/            Confirmation, NotificationSender, email and SMS senders (simulated)
├── tools/
│   └── measure.py                1,000 searches: average, p95, total and the GET /stats difference
├── docs/
│   ├── requirements.md           requirements R1–R6
│   ├── design-notes.md           written answers from P03 to P08
│   ├── quality-scenarios.md      stakeholders and quality scenarios S1–S6
│   ├── contexts.md               four business contexts: words, rules, owners, borders
│   ├── adr-001-modular-monolith.md
│   ├── adr-002-cache-availability.md   the cache decision
│   ├── capacity.md               capacity estimate for the app
│   ├── cache-experiment.md       measurements, stale result, invalidation, hot key
│   ├── openapi.yaml              the API contract
│   ├── api-check.md              seven requests against PostgreSQL and the restart check
│   ├── requests/                 request bodies for curl (maya-r7, omar-r7, omar-r8)
│   └── draw_io_diagrams/         8 draw.io diagrams
└── old/
    └── hotel_booking.py          the P03 version in one file, kept for comparison
```

## How to run

Requirements: Python 3.10 or newer, and Docker or Podman for PostgreSQL and Redis.

### 1. Install the packages (once)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 2. Start PostgreSQL and Redis

```bash
docker compose up -d               # with Podman: podman-compose up -d
docker compose ps                  # db and cache are Up
docker compose exec cache redis-cli ping    # PONG
```

`db/init.sql` runs once, when the database is first created. To start again from an empty database: `docker compose down -v`, then `up -d`. Stop everything with `docker compose down` (without `-v` the data is kept).

If port 5432 or 6379 is taken on your laptop, change the port in `docker-compose.yml` and start the app with `HOTEL_DB_PORT=5433` or `HOTEL_REDIS_PORT=6380` in front of `python main.py`.

### 3. Run

```bash
python main.py                     # the API on http://localhost:5080 (PostgreSQL and Redis)
python main.py --demo              # the console demo, data in lists
python main.py --race              # two guests book the same room at the same moment
python tools/measure.py            # in a second terminal: 1,000 searches against the running app
python tools/measure.py 2026-12-31 2027-01-02    # other dates
```

### 4. Check

```bash
python -m unittest -v              # 14 tests: 8 behaviour + 6 API
lint-imports                       # 3 architecture contracts
```

Expected: `Ran 14 tests ... OK` and `Contracts: 3 kept, 0 broken.` (17 green checks).

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
| `GET /stats` | `200` with `searches`, `databaseQueries`, `cacheHits`, `cacheMisses` | |

Errors are problem details (RFC 9457, `application/problem+json`) with `title`, `status` and `detail`. A client compares the `title`; `detail` is a sentence for people.

## The cache (P08)

The search looks in Redis first and asks PostgreSQL only on a miss (cache-aside).

| Decision | Value |
|---|---|
| Key | `availability:v{version}:{checkIn}:{checkOut}` |
| Value | the free room numbers, such as `R7,R8` |
| TTL | 30 seconds |
| Invalidation | a successful `POST` or `DELETE` raises `availability:version`, so every older copy is never read again |
| What is cached | only the search; booking and cancelling always read PostgreSQL, the source of truth |

1,000 searches for the same stay cost 2 database queries instead of 2,000. A copy can show a booked room for a moment only if an invalidation is missed, and then for at most 30 seconds. While Redis is down, searches fail, and a booking or cancel is saved but answers with an error, because the version cannot be raised (no fallback yet). The measurements, the stale result and the hot key are in `docs/cache-experiment.md`; the reasons are in `docs/adr-002-cache-availability.md`.

## The four modules

Each module is a package with a **public contract** that other modules may use and **internal code** (`internal.py`) that only the module itself, `main.py` and the tests may use.

| Module | Job | Public contract | Internal code |
|---|---|---|---|
| `rooms` | Knows which rooms the hotel sells | `Room`, `RoomCatalog` | `InMemoryRoomCatalog`, `PostgresRoomCatalog` |
| `reservations` | Owns the booking rule | `BookingService`, `BookingResult`, `DateRange`, `Guest`, `Reservation`, `ReservationStatus`, `ReservationStore` | `InMemoryReservationStore`, `PostgresReservationStore` |
| `payments` | Takes deposits and records whether they were paid | `PaymentStatus`, `PaymentService` | `SimulatedPaymentService` |
| `notifications` | Tells guests what happened | `Confirmation`, `NotificationSender` | `EmailNotificationSender`, `SmsNotificationSender` |

`api.py` and `api_cache.py` are outside the four modules and use only their public contracts. `main.py` is the wiring: it picks the PostgreSQL stores and Redis for the web app and the list stores for `--demo`, `--race` and the tests. Three rules run as `import-linter` contracts (`pyproject.toml`): Reservations uses only the public contracts of other modules; Rooms depends on no other module; Payments and Notifications do not depend on Reservations.

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
- `docs/cache-experiment.md`: the measurements without and with the cache, the stale result, invalidation and the hot key.
- `docs/openapi.yaml`: the API contract; open it in the Swagger editor (editor.swagger.io).
- `docs/design-notes.md`: written answers from every practice.
- `docs/adr-001-modular-monolith.md` and `docs/adr-002-cache-availability.md`: the architecture decisions.

## Known problem: the race condition

`reserve` first **checks** ("is the room free?") and then **saves**. If two requests arrive at almost the same moment, both can check before either one saves, so both are Accepted. The result is two Confirmed reservations for the same room and nights, which breaks requirement R3 and scenario S2. Run `python main.py --race` to see it.

Neither PostgreSQL nor the cache fixes this: the primary key stops a second `R101`, but nothing stops two different reservations of the same room and nights. Searches no longer load the database; bookings now decide its limit. P09 fixes the race in PostgreSQL.

## Limits of this version

- The race condition above is still present.
- Redis is one more program: while it is down, searches fail and a booking or cancel is saved but answers with an error.
- Every booking empties every cached search, so a busy sale lowers the hit rate.
- The database password (`hotel`) is for a laptop only.
- No prices, payments, invoices or logins; Payments is a contract with a simulated class that nothing calls yet.
- Email and SMS confirmations are simulated.
- The API tests use the list store and a dictionary cache; the PostgreSQL and Redis parts are checked with the requests in `docs/api-check.md` and with `tools/measure.py`.

## What comes next

| Practice | What changes |
|---|---|
| L05 | Transactions, locks and isolation levels: why two bookings at the same moment can both pass the check |
| P09 | Reproduce the double booking with concurrent HTTP calls and fix it in PostgreSQL |
| P10 | The confirmation email moves out of the request into a background worker |
| P17 | The booking saga: hold the room, take the deposit (Payments), confirm, or undo |