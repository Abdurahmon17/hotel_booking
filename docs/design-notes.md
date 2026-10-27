# P03 design notes

## Why design before code

Low-level design decides which classes the program has (for example Guest, Room and Reservation), what information each class keeps, which methods each class has, and which class calls which class. We write these decisions down as UML diagrams before coding. This way a rule such as "is the room already booked?" is written once, in one place (DateRange.Overlaps()), and both the website and the reception desk use it. When a rule changes, we change one method instead of finding several copies, and a new developer can understand the booking flow by reading one diagram.

## Where the methods live

Cancel() lives in Reservation, because cancelling changes the reservation's own status, and only the reservation knows and owns its status.

HasOverlap(room, stay) lives in ReservationStore, because only the store can see all the reservations, so only it can check whether any of them already has this room on these nights.

## Activity traces

### Omar, R7, 13–15 November (Maya has R7 for 12–14)
First diamond: is check-out after check-in? Yes (15 is after 13). Second diamond: does a Confirmed booking share a night? Yes, the night of the 13th. The request ends at "Unavailable · save nothing".

### Nora, R7, 14–16 November
First diamond: is check-out after check-in? Yes (16 is after 14). Second diamond: does a Confirmed booking share a night? No. Maya's booking covers the nights of the 12th and 13th, Nora needs the nights of the 14th and 15th, and Maya checks out on the 14th. The request continues: the reservation is saved as Confirmed, the confirmation email is sent, and the request ends at "Accepted + reservation id".

### Omar, R8, 15–15 November
First diamond: is check-out after check-in? No (15 is not after 15). The request ends at "InvalidDates · save nothing". The second diamond is never reached, because the request stops at the first one.

## Prediction

I expect Nora's request (R7, 14–16 November) to be Accepted with id R102. Maya's booking R101 covers the nights of the 12th and 13th, and Nora needs the nights of the 14th and 15th. They share no night, because Maya checks out on the 14th. Omar's request was Unavailable, so it was not saved, and the next id is R102.

Result: the program printed "Nora books R7 14-16 Nov: Accepted R102", so the prediction was correct.

## The race

Prediction: when Maya and Omar book R7 for 12–14 November at the same moment, I expect R7 to have 1 Confirmed reservation, because the second request should see Maya's booking and answer Unavailable.

Result: the race demo printed "Maya: Accepted R101", "Omar: Accepted R102" and "Confirmed reservations for R7 on 12-14 Nov: 2", so my prediction was wrong.

What happened: Maya and Omar both got "Accepted", so R7 ended with 2 Confirmed reservations for the same nights, and requirement R3 was broken. Omar's request checked the store 0.1 s after Maya's, before Maya's booking was saved, so it saw an empty store and went ahead.

Where the problem appears: between the call HasOverlap(room, stay) and the call Save(reservation) inside Reserve. The answer from HasOverlap was already out of date when Save ran, because the other request saved in the gap. We do not fix it today; P09 fixes it in the database.



# P04 design notes

## Refactoring

Refactoring changes how the code is organised (names, files, interfaces) but not what the program does: every request must give exactly the same result as before.

Must stay the same:
- The tests from Step 2: all 6 still pass after every move.
- The demo output: the same nine lines as in P03.
- The race demo: still prints "Double booking!", because refactoring does not fix bugs.


## What our code breaks

- BookingService asks for exactly ReservationStore (D: dependency inversion).
  In P07 we would have to edit BookingService just to use a database.

- BookingService asks for exactly EmailSender (D and O: dependency inversion and open/closed).
  To add SMS confirmations we would have to edit BookingService, its constructor and Reserve(), even though the booking rules did not change. A new feature should be new code, not a change to working code.



## Proof

- Tests: 6 tests ran and all 6 passed (python -m unittest -v). No test body changed, only the import and new_service().
- Demo: the output is the same as in P03, all nine lines match, line by line.
- Race: it still double-books (Confirmed reservations for R7 on 12-14 Nov: 2, "Double booking!"), because refactoring changes the structure and not the behaviour. P09 fixes it.