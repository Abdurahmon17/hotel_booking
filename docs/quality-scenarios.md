# Quality scenarios

## Stakeholders

| Who | What they care about |
|---|---|
| Guest | Finds a free room quickly; never loses a booking |
| Receptionist | Never promises one room twice; can cancel at the desk |
| Hotel manager (domain expert) | Knows the rules; wants deposits and SMS soon |
| Development team | Can change one area without breaking the others |
| Email/SMS and payment providers | Outside systems that can be slow or down |

## S1 · Performance: many guests search at once

| Part | S1 |
|---|---|
| Source | 200 guests |
| Stimulus | They search free rooms for 12–14 Nov |
| Environment | Within one minute, during normal operation |
| Artifact | The free-room search in BookingService (FindFreeRooms) |
| Response | Every guest gets the correct list of free rooms |
| Measure | p95 response ≤ 1 second |
| Checked in | P08 (cache), P23 (load test) |

## S2 · Data integrity: two guests, one room

| Part | S2 |
|---|---|
| Source | 100 pairs of guests |
| Stimulus | Both guests of a pair book the same room and nights |
| Environment | At the same moment |
| Artifact | BookingService.Reserve and the reservation store (HasOverlap, Save) |
| Response | Exactly one of the two gets Confirmed; the other gets Unavailable |
| Measure | Exactly 1 Confirmed reservation per pair; 0 double bookings |
| Checked in | P09 |

## S3 · Availability: a failed message keeps the booking

| Part | S3 |
|---|---|
| Source | The email provider |
| Stimulus | It stops answering |
| Environment | For 10 minutes, during normal bookings |
| Artifact | BookingService.Reserve and the notification sender |
| Response | Every valid booking is still Accepted and saved; the failed message is reported |
| Measure | 0 lost bookings; every failed message is counted |
| Checked in | P04 (R6 test, done) and P10 |

## S4 · Security: nobody reads another guest's reservation

| Part | S4 |
|---|---|
| Source | A guest |
| Stimulus | They try to read another guest's reservation |
| Environment | 100 attempts, during normal operation |
| Artifact | Looking up a reservation by its id (Find) |
| Response | The app refuses and shows nothing |
| Measure | 0 of 100 attempts show a reservation to the wrong guest |
| Checked in | P21 |

## S5 · Modifiability: add SMS confirmations

| Part | S5 |
|---|---|
| Source | The hotel manager |
| Stimulus | Asks for SMS confirmations |
| Environment | During development, while the app keeps working |
| Artifact | BookingService and the notification senders |
| Response | A new sender class is added; BookingService is not edited |
| Measure | 0 edits in BookingService; at most 2 files change (not counting tests) |
| Checked in | P04 (SMS sender, done) |

## S6 · Sustainability: fewer watt-hours per search

| Part | S6 |
|---|---|
| Source | The development team |
| Stimulus | They run the same 1,000 searches before and after a change |
| Environment | Same machine, same data, same load |
| Artifact | The free-room search |
| Response | The same results with less energy used |
| Measure | At least 20% fewer watt-hours per 1,000 completed searches |
| Checked in | P08, P24 |