# Hotel Reservation System

**Medium** · Vol 2 · Ch.6 · Optimistic locking · Inventory model · Double-booking prevention

Tags: `MySQL`, `Redis`, `Idempotency`, `Pessimistic Lock`, `Overbooking`, `Saga`

**Flow:** Search (dates+location) → Availability cache (Redis) → DB → Book: SELECT FOR UPDATE → reserve → charge PSP → confirm

---

<details open>
<summary><strong>Problem</strong></summary>

Design a hotel reservation system like Booking.com or Marriott.com. The central challenge is preventing double-booking: two users simultaneously trying to book the last available room on the same date. Every design decision flows from this concurrency problem.

The system also needs to handle search (finding available rooms across thousands of hotels), inventory management (tracking room availability by date), and payment — all with ACID guarantees on the booking transaction.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Inventory model** — Core table: room_inventory(hotel_id, room_type, date, total_rooms, reserved_rooms). Available = total - reserved. One row per room-type per date. Simple, queryable, lockable.
- **SELECT FOR UPDATE (pessimistic lock)** — On booking: SELECT ... FOR UPDATE on the inventory row. Holds a row-level lock until transaction commits. Second concurrent booking for the same room/date blocks until first completes. Prevents double-booking.
- **Idempotency key** — Client sends idempotency_key with every booking request. Server deduplicates: same key = return same result. Prevents double-charge on network retry.
- **Availability cache** — Redis bitmap or hash per hotel: room_type:date → available_count. Search reads from cache. Booking writes through cache after DB commit. Cache miss falls back to DB.
- **Overbooking allowance** — Airlines and hotels intentionally overbook by 5-10%. reserved_rooms can exceed total_rooms by a configured buffer. Business decision, not a bug.
- **Date range query** — Searching for availability across a date range means checking every date in the range. Precompute availability windows. Index on (hotel_id, room_type, date).
- **Saga for booking flow** — Booking involves multiple steps: reserve inventory → charge card → send confirmation. Use Saga pattern: each step has a compensating transaction (release reservation if payment fails).

> SELECT FOR UPDATE prevents double-booking. Idempotency key prevents double-charging. Saga handles partial failures across reserve → pay → confirm. These three together make a correct booking system.

</details>


<details>
<summary><strong>Scale</strong></summary>

Hotel reservation is a correctness problem masquerading as a scale problem. The real engineering challenge is not throughput — 167 bookings/sec is trivial for MySQL. The challenge is the SELECT FOR UPDATE contention on popular dates.

Contention peaks when: (1) a flash sale starts and thousands of users race for limited inventory, (2) a popular date has one room left. The queue of blocked SELECT FOR UPDATE transactions can grow large. Mitigation: connection pool limits, request timeout with graceful 'sold out' message, queue-based booking for extreme flash sales (serialize via Kafka, process one at a time).

</details>


<details>
<summary><strong>Script</strong></summary>

1. Correctness-first framing.
2. "Hotel reservation has one defining engineering challenge: preventing double-booking. Every design decision flows from that. I'll design around it."
3. "Inventory model: room_inventory table with (hotel_id, room_type, date, total_rooms, reserved_rooms). Available = total - reserved. One row per room-type per date."
4. "Booking transaction: SELECT reserved_rooms FROM room_inventory WHERE hotel_id=X AND room_type=Y AND date=Z FOR UPDATE. This acquires a row-level lock. Check available > 0. UPDATE reserved_rooms = reserved_rooms + 1. INSERT reservation record. COMMIT. Lock released. Second concurrent request for the same row blocks until this commits — double-booking impossible."
5. "Idempotency key on every booking: Redis SETNX before the transaction. Network retry with same key returns cached result — no double-charge."
6. "Search: Redis availability cache (hotel:room_type:date → count). 99% of traffic is search. Cache miss falls back to DB. Booking writes through cache after commit."
7. "Saga for the full flow: reserve (sync) → charge PSP (async via Kafka) → send confirmation (async). Reservation held for 10 minutes. If payment fails: auto-cancel reservation, restore inventory."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
SEARCH FLOW:
  User (dates, location) → Search Service
    → Redis availability cache (hotel:type:date → count)
    → cache miss → MySQL read replica
    → return available hotels + prices

  BOOKING FLOW:
  User selects room + enters payment
    → Reservation Service
    → BEGIN TRANSACTION
        SELECT * FROM room_inventory
        WHERE hotel_id=1 AND room_type='deluxe' AND date='2026-12-31'
        FOR UPDATE;          ← row-level lock acquired
        -- check available = total - reserved > 0
        UPDATE room_inventory SET reserved_rooms = reserved_rooms + 1;
        INSERT INTO reservations (user_id, hotel_id, ..., status='PENDING');
        COMMIT;              ← lock released
    → Kafka: booking.created event
    → Payment consumer: charge PSP
    → Notification consumer: send email
    → Update cache: decrement availability

  DOUBLE-BOOKING PREVENTION:
  User A ──► SELECT FOR UPDATE (acquires lock)
  User B ──► SELECT FOR UPDATE (BLOCKS until A commits)
  A commits (reserved_rooms = 1/1, available = 0)
  B unblocks → reads available = 0 → rejected "sold out"

  INVENTORY TABLE:
  hotel_id │ room_type │ date       │ total │ reserved
  ─────────┼───────────┼────────────┼───────┼─────────
  1        │ deluxe    │ 2026-12-31 │  10   │   10
  1        │ standard  │ 2026-12-31 │  20   │   15
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-hotel)
