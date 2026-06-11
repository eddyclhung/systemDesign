# Distributed Message Queue (Kafka)

**Hard** · Vol 2 · Ch.4 · Partitioned log · Consumer groups · Exactly-once

Tags: `Kafka`, `Partitioning`, `Consumer Groups`, `Offset`, `Exactly-once`, `Replication`

**Flow:** Producer → Kafka broker (leader partition) → Followers replicate → Consumer group pulls from partition → commits offset

---

<details open>
<summary><strong>Problem</strong></summary>

Design a distributed message queue that can handle millions of events per second with durability, ordering guarantees, and the ability for multiple independent consumer groups to read the same stream. The system must survive broker failures without data loss.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Partitioned log model** — Topic split into N partitions. Each partition is an ordered, append-only log. Messages in a partition are strictly ordered. Messages across partitions are not.
- **Consumer groups** — Each consumer group reads the topic independently. Within a group: each partition assigned to exactly one consumer. Multiple groups on same topic: no interference. Enables pub/sub (multiple consumers) and point-to-point (one consumer per message).
- **Offset management** — Consumer tracks its position (offset) per partition. Commit offset after processing. On failure/restart: resume from last committed offset. Enables at-least-once delivery.
- **Replication** — Each partition: 1 leader + N-1 followers. Leader handles reads/writes. Followers replicate asynchronously. On leader failure: a follower becomes leader (ISR — In-Sync Replica list).
- **Delivery semantics** — At-most-once: commit before processing (may lose). At-least-once: commit after processing (may duplicate). Exactly-once: idempotent producer + transactional consumer (strongest guarantee, most complex).
- **Retention policy** — Messages retained for N days regardless of consumption. Consumers can replay from any offset. This is Kafka's killer feature vs traditional queues.
- **Log compaction** — Alternative to TTL retention: keep only the latest value per key. Useful for change data capture (CDC) — compacted topic always has the current state of every entity.

> Partitioned log + consumer groups + offset management. Replayability is Kafka's defining feature vs RabbitMQ. At-least-once delivery is the production default; exactly-once is available but expensive.

</details>


<details>
<summary><strong>Scale</strong></summary>

The scaling lever is partition count. You cannot have more consumers in a group than partitions — adding consumer beyond that is wasted capacity. If you need 1000 consumers: you need 1000 partitions minimum.

Partition rebalancing is the operationally painful moment: adding consumers to a group, adding partitions, or broker failure all trigger rebalancing. During rebalance, all consumers pause (stop-the-world). New Kafka versions introduce incremental cooperative rebalancing to minimize this pause.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Three-concept framing.
2. "Distributed message queue has three core concepts: partitioning (for parallelism and ordering), consumer groups (for independent read streams), and offsets (for reliable delivery)."
3. "Partitioning: each topic split into N partitions. Messages with the same key always go to the same partition — ordering guaranteed per key. Different partitions consumed in parallel."
4. "Consumer groups: each group reads the topic independently. Within a group: each partition assigned to one consumer — no duplicate processing. Multiple groups = pub/sub."
5. "Offsets: consumer tracks its read position per partition. Commit after processing. On restart: resume from last committed offset. At-least-once delivery by default."
6. "Replication: each partition has 1 leader + 2 followers. acks=all: wait for all ISR before confirming write. No data loss on leader failure."
7. "Replayability: messages retained for 7 days. Any consumer group can replay from offset 0. This is Kafka's key advantage over RabbitMQ."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
═══════════════ KAFKA ARCHITECTURE ══════════════════

  Producers
  ┌─────┐ ┌─────┐ ┌─────┐
  │ P1  │ │ P2  │ │ P3  │   acks=all (wait for ISR)
  └──┬──┘ └──┬──┘ └──┬──┘
     └────────┼───────┘
              │
  ┌───────────▼──────────────────────────────────────┐
  │  Kafka Cluster  (3 brokers shown)                 │
  │                                                  │
  │  Topic: "user-events"  (partitioned)             │
  │                                                  │
  │  Partition 0  ──────────────────────────────►    │
  │  [msg0][msg3][msg6]  leader: Broker 1            │
  │                      replicas: Broker 2, 3       │
  │                                                  │
  │  Partition 1  ──────────────────────────────►    │
  │  [msg1][msg4][msg7]  leader: Broker 2            │
  │                      replicas: Broker 1, 3       │
  │                                                  │
  │  Partition 2  ──────────────────────────────►    │
  │  [msg2][msg5][msg8]  leader: Broker 3            │
  │                      replicas: Broker 1, 2       │
  └───────────┬──────────────────────────────────────┘
              │
  ┌───────────┴───────────────────────────────────────┐
  │             Consumer Groups (independent)          │
  │                                                   │
  │  Group A (Analytics)    Group B (Notification)    │
  │  C1 → P0                C4 → P0                  │
  │  C2 → P1                C5 → P1                  │
  │  C3 → P2                C6 → P2                  │
  │  offset: 847            offset: 1203             │
  │  (each group reads independently, no conflict)   │
  └───────────────────────────────────────────────────┘

  ═══════════════ WRITE PATH ═══════════════════════════

  Producer → partition selection:
    keyed msg:   hash(key) % N  → same key, same partition
    unkeyed msg: round-robin    → even distribution

  Leader writes to local log  →  followers replicate
  acks=all: leader waits for all ISR acknowledgment
  acks=1:   leader confirms, async replicate (faster)
  acks=0:   fire and forget (may lose on crash)

  ═══════════════ OFFSET & DELIVERY ═════════════════

  at-most-once:   commit offset BEFORE processing
  at-least-once:  commit offset AFTER processing   ← default
  exactly-once:   idempotent producer + transactions
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-msgqueue)
