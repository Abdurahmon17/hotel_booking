-- The hotel booking app's tables. PostgreSQL runs this file once, when the database is first created.
-- Rooms owns the rooms table and Reservations owns the reservations table, so there is no foreign key
-- between them: each module keeps its own data (L03).

CREATE TABLE rooms (
    number text PRIMARY KEY,
    type   text NOT NULL
);

CREATE TABLE reservations (
    id          text PRIMARY KEY,   -- R101, R102 ...: a second R101 is refused
    guest_name  text NOT NULL,
    guest_email text NOT NULL,
    room        text NOT NULL,
    check_in    date NOT NULL,
    check_out   date NOT NULL,
    status      text NOT NULL CHECK (status IN ('Confirmed', 'Cancelled')),
    CHECK (check_out > check_in)
);

INSERT INTO rooms (number, type) VALUES ('R7', 'Standard'), ('R8', 'Deluxe');