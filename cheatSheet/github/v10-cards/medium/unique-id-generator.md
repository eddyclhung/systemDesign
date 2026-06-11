# Unique ID Generator

**Medium** · Vol 1 · Ch.7 · Snowflake · 64-bit · Time-ordered · No coordination

Tags: `Snowflake`, `UUID`, `64-bit`, `Distributed`, `Time-ordered`, `Clock Skew`

**Flow:** Service calls ID Generator → Snowflake: timestamp + datacenter + machine + sequence → 64-bit ID returned

---

<details open>
<summary><strong>Problem</strong></summary>

Generate globally unique, time-sortable IDs across thousands of machines without a central coordinator. The ID must be 64-bit (efficient for DB indexing), sortable by generation time (useful for pagination), and generated without network round-trips (low latency).

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Snowflake layout (64 bits)** — 1 sign bit (0) + 41 timestamp (ms since epoch, ~69 years) + 5 datacenter ID + 5 machine ID + 12 sequence (4096 IDs/ms/machine)
- **No coordination** — Machine ID is pre-assigned (from ZooKeeper or config). Sequence resets each millisecond. No network call to generate an ID — pure local computation.
- **Throughput** — 4096 IDs/ms/machine. 1024 machines × 4096 = 4.2M IDs/ms globally. More than any realistic write rate.
- **Time-ordered** — IDs increase monotonically within a millisecond window. Sorted by generation time. Efficient B-tree index inserts (no random page splits).
- **Clock skew risk** — If machine clock goes backward, generated IDs can collide with previous ones. Must detect and handle backward clock jumps.
- **UUID tradeoffs** — UUID v4: 128-bit, random, no coordination, no network call. But: not sortable, 2× the storage, poor B-tree performance (random inserts).
- **Custom epoch** — Set epoch to recent date (e.g. 2024-01-01) to maximize timestamp range. 41 bits from 2024 = usable until ~2093.

> Snowflake is the production default: 64-bit, no coordination, time-ordered, 4096 IDs/ms/machine. Main risk: clock skew. Main mitigation: refuse to generate IDs if clock goes backward, wait for clock to catch up.

</details>


<details>
<summary><strong>Scale</strong></summary>

Snowflake has essentially no scaling problems — it's entirely local computation. The only external dependency is ZooKeeper for machine ID assignment, which happens once at startup.

The edge case is an extremely write-heavy service generating >4096 IDs/ms/machine. Solution: provision more machines (each gets its own machine ID space). At 4096 IDs/ms/machine × 1024 machines = 4.2B IDs/ms globally — practically unlimited.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Requirements-first script.
2. "Clarifying questions: do IDs need to be globally unique across services, or per-service unique? And do they need to be sortable by creation time?"
3. "Global uniqueness, time-sortable — perfect for Snowflake. Here's the structure: 64 bits total. 1 sign bit always 0. 41 bits for timestamp in milliseconds since a custom epoch — gives us 69 years. 10 bits for machine identity (5 datacenter + 5 machine). 12 bits for sequence within a millisecond — 4096 IDs/ms/machine."
4. "No coordination needed on the hot path. Machine ID is pre-assigned from ZooKeeper at startup. After that, ID generation is pure local computation — just timestamp + counter."
5. "Main risk: clock skew. If NTP adjusts the clock backward, we could generate duplicate timestamps. Fix: track last generated timestamp, refuse to generate if current time goes backward, wait until clock catches up."
6. "Throughput: 4096 IDs/ms × 1024 machines = 4.2 billion IDs per millisecond globally. More than sufficient for any realistic write load."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌─────────────────────────────────────────────────────┐
  │             SNOWFLAKE 64-BIT ID LAYOUT               │
  │                                                      │
  │  bit  63   62────────────22  21──17  16──12  11────0 │
  │       [0] [  41-bit epoch ms ] [5-DC][5-mach][12-seq]│
  │        ▲          ▲               ▲      ▲       ▲   │
  │      sign    ms since epoch    DC ID  Mach    0–4095 │
  │       =0    custom epoch 2024   0–31   ID    per ms  │
  └─────────────────────────────────────────────────────┘

  STARTUP (one-time):
  ┌────────────┐    register    ┌──────────────────────┐
  │  Service   │──────────────►│   ZooKeeper           │
  │  Instance  │               │  sequential ephemeral │
  │            │◄──────────────│  node → machine ID    │
  └────────────┘  machine_id   └──────────────────────┘

  ID GENERATION (hot path — zero network calls):
  ┌─────────────────────────────────────────────────────┐
  │  now_ms  = current_time_ms()                        │
  │                                                     │
  │  if now_ms < last_ms:                               │
  │      wait until clock catches up  (clock skew)     │
  │                                                     │
  │  if now_ms == last_ms:                              │
  │      seq = (seq + 1) & 0xFFF   (12-bit mask)       │
  │      if seq == 0: spin to next ms                   │
  │  else:                                              │
  │      seq = 0                                        │
  │                                                     │
  │  last_ms = now_ms                                   │
  │                                                     │
  │  id = (now_ms - epoch) << 22                        │
  │      | (dc_id << 17)                               │
  │      | (machine_id << 12)                          │
  │      | seq                                          │
  └─────────────────────────────────────────────────────┘

  THROUGHPUT:  4096 IDs/ms × 1024 machines = 4.2B IDs/ms
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-idgen)
