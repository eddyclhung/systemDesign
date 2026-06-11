# Stock Exchange

**Hard** · Vol 2 · Ch.8 · Order book · Matching engine · Low latency · CQRS

Tags: `Order Book`, `Matching Engine`, `Sequencer`, `LMAX`, `Event Sourcing`, `Market Data`, `FIX`

**Flow:** Order → FIX gateway → Sequencer (assigns sequence ID) → Matching engine (in-memory order book) → Trade execution → Market data publisher → Client notification

---

<details open>
<summary><strong>Problem</strong></summary>

Design a stock exchange order matching system. The core requirements are extreme: sub-millisecond order matching latency, strict price-time priority (FIFO within same price), guaranteed no duplicate order processing, and an immutable audit trail of every order and trade. This is one of the most latency-sensitive systems in existence.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Order book** — Per-symbol sorted data structure: bid side (descending price), ask side (ascending price). Implemented as a sorted map (price → queue of orders). Best bid = highest buy order. Best ask = lowest sell order. Match when best bid >= best ask.
- **Matching engine (single-threaded)** — The matching engine is intentionally single-threaded to avoid locking. All orders for a symbol processed sequentially. LMAX Disruptor pattern: lock-free ring buffer for inter-thread communication. Achieves millions of orders/sec on commodity hardware.
- **Sequencer** — Single point of truth for order sequencing. Every order receives a monotonically increasing sequence ID before reaching the matching engine. Guarantees deterministic replay — given same sequence of inputs, always produces same output. Critical for disaster recovery.
- **Price-time priority (FIFO)** — Within the same price level, orders are matched in arrival order (time priority). Order with lower sequence ID matched first. This is the regulatory requirement for most exchanges.
- **Event sourcing** — Every order, trade, and cancellation stored as an immutable event. Current state = replay of all events. Enables audit trail, replay for bug fixes, and disaster recovery. Events stored in a write-ahead log.
- **Market data publisher** — After each match, publish trade data and order book changes to subscribers. Two feeds: full depth (all price levels) and top-of-book (best bid/ask only). Published via multicast UDP for lowest latency.
- **FIX protocol** — Industry standard Financial Information eXchange protocol for order entry and market data. Brokers connect via FIX gateways. Binary FIX (FAST/SBE) for low latency; text FIX for compatibility.

> Single-threaded matching engine eliminates locking. Sequencer guarantees deterministic ordering. Event sourcing enables replay and audit. These three together define exchange architecture.

</details>


<details>
<summary><strong>Scale</strong></summary>

The scaling axis for an exchange is latency, not throughput. 500K orders/sec is achievable on a single server. Sub-100 microsecond matching requires bypassing the Linux kernel's network stack entirely.

Kernel bypass networking (DPDK): process network packets directly in userspace, avoiding 50-100 microsecond kernel overhead. CPU pinning: matching engine thread pinned to a dedicated CPU core, never preempted. NUMA-aware allocation: order book data allocated on same NUMA node as CPU. These three techniques together achieve 5-50 microsecond matching latency.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Latency-first framing.
2. "Stock exchange is the most latency-sensitive system you'll design. The engineering challenge is not throughput — 500K orders/sec is trivial. The challenge is sub-100 microsecond matching latency."
3. "Core component: matching engine. Single-threaded (no locking), in-memory order book (per symbol), LMAX Disruptor ring buffer for lock-free inter-thread communication."
4. "Order flow: FIX gateway → sequencer (assigns monotonic sequence ID) → matching engine (price-time priority matching) → WAL (async durability) → market data publisher."
5. "Sequencer is the key correctness guarantee: every order gets a unique sequence ID before matching. Given the same sequence of events, the matching engine always produces the same output. Enables deterministic replay for disaster recovery."
6. "Fault tolerance: WAL + periodic order book snapshots. On crash: restore from latest snapshot + replay WAL tail. Recovery in < 1 minute."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
Broker (FIX protocol)
         |
  FIX Gateway (TCP)
         |
  Sequencer ─── assigns monotonic seq_id
         |
  Matching Engine (single-threaded)
  ┌────────────────────────────────┐
  │  Order Book (per symbol)       │
  │  BID:  105.00  [100, 200]      │
  │        104.50  [500]           │
  │  ASK:  105.50  [150]           │
  │        106.00  [300, 100]      │
  │                                │
  │  Match: bid >= ask → TRADE     │
  └──────────────┬─────────────────┘
                 |
  ┌──────────────┼──────────────────┐
  |              |                  |
  WAL         Trade             Market Data
  (async)     Execution         Publisher
  NVMe SSD    (position update)  (UDP multicast)
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-stock-exchange)
