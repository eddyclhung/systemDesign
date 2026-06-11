# Distributed Key-Value Store

**Hard** · Vol 1 · Ch.6 · CAP theorem · Quorum · Gossip · Bloom filter

Tags: `CAP Theorem`, `Quorum`, `Vector Clock`, `Gossip Protocol`, `Bloom Filter`, `LSM Tree`

**Flow:** Client → Any node (coordinator) → Consistent hash ring → W writes / R reads across N replicas

---

<details open>
<summary><strong>Problem</strong></summary>

Design a distributed KV store like DynamoDB or Cassandra. The core tension is the CAP theorem — you cannot simultaneously guarantee consistency, availability, and partition tolerance.

Every design decision (replication factor, quorum size, conflict resolution strategy) is a point on the CAP spectrum.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **CAP theorem** — Choose 2 of 3: Consistency (all nodes see same data), Availability (always responds), Partition Tolerance (works during network splits). In practice: partition tolerance is non-negotiable in distributed systems, so you choose between CP and AP.
- **Quorum (W + R > N)** — N=3, W=2, R=2: any write is confirmed by 2 nodes, any read checks 2 nodes. Since W+R > N, at least 1 node is shared — guarantees you read the latest write.
- **Vector clocks** — Each write increments [server, version] pair. Multiple conflicting versions can exist. Client resolves conflicts on read (last-write-wins or application merge).
- **Gossip protocol** — Each node maintains a heartbeat table. Periodically gossips to random neighbors. Node marked down if heartbeat stale for T seconds. O(log N) propagation time.
- **Sloppy quorum + hinted handoff** — If target replica is down, write to next healthy node with a hint. When downed node recovers, hint is delivered. Improves availability at cost of potential staleness.
- **Write path (LSM tree)** — Write to commit log (durability) → MemTable (in-memory) → flush to SSTable (disk). Reads check MemTable first, then Bloom filter → SSTable.
- **Bloom filter** — Probabilistic data structure: false positives possible, false negatives impossible. Tells you 'key definitely not in this SSTable' — avoids unnecessary disk reads.

> W+R > N is the core formula. Gossip for failure detection. Vector clocks for conflict tracking. Bloom filters for read optimization. Know the read path and write path cold.

</details>


<details>
<summary><strong>Scale</strong></summary>

The hardest scaling problem is compaction — LSM trees accumulate SSTables on disk. Compaction merges SSTables and removes tombstones. During compaction, CPU and disk IO spike. In the worst case, compaction can't keep up with write rate, SSTables pile up, and read latency explodes (must check more files).

Mitigation: tiered compaction (Cassandra) minimizes write amplification. Size-tiered compaction works better for write-heavy, leveled compaction for read-heavy. Monitor SSTable count per node — should stay in single digits. Alert when compaction lag grows.

</details>


<details>
<summary><strong>Script</strong></summary>

1. CAP-first framing.
2. "A distributed KV store forces you to confront the CAP theorem immediately. Partition tolerance is non-negotiable — networks will split. So the question is: do we prioritize consistency or availability during a partition?"
3. "I'd default to AP with tunable consistency — like Cassandra's model. For most use cases, stale reads for a few seconds are acceptable. You can tighten to QUORUM when the application needs it."
4. "Data distribution: consistent hashing with virtual nodes. N=3 replicas. W=2, R=2 for QUORUM reads and writes."
5. "Write path: client → coordinator → commit log + MemTable → async flush to SSTable. Bloom filter on each SSTable to avoid unnecessary disk reads."
6. "Failure detection: gossip protocol — each node gossips heartbeat state to random neighbors. Node marked down if heartbeat stale for 10 seconds."
7. "Conflict resolution: vector clocks track concurrent writes. Application resolves on read. Last-write-wins as fallback."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌──────────┐         ┌──────────────────────────────────┐
  │  Client  │────────►│  Any Node = Coordinator           │
  └──────────┘         │  (routes to replicas via ring)    │
                       └─────────────┬────────────────────┘
                                     │
           ┌──────────────┬──────────┴──────────┐
           ▼              ▼                      ▼
     ┌──────────┐   ┌──────────┐          ┌──────────┐
     │  Node A  │   │  Node B  │          │  Node C  │
     │ (replica)│   │ (replica)│          │ (replica)│
     └────┬─────┘   └────┬─────┘          └────┬─────┘
          │              │                      │
          ▼              ▼                      ▼
     ┌──────────────────────────────────────────────┐
     │              WRITE PATH (per node)            │
     │                                               │
     │  1. Commit Log  (durability, append-only)     │
     │        ↓                                      │
     │  2. MemTable    (in-memory sorted tree)       │
     │        ↓  (threshold reached)                 │
     │  3. SSTable     (immutable, on-disk)          │
     │        ↓  (compaction)                        │
     │  4. Merged SSTables (fewer, larger files)     │
     └───────────────────────────────────────────────┘

     ┌──────────────────────────────────────────────┐
     │              READ PATH (per node)             │
     │                                               │
     │  1. MemTable           (fastest, in-memory)   │
     │  2. Bloom Filter       (is key in SSTable N?) │
     │  3. SSTable index      (find block offset)    │
     │  4. SSTable block      (fetch from disk)      │
     └───────────────────────────────────────────────┘

     QUORUM  W=2, R=2, N=3:
     ┌──────────────────────────────────────────────┐
     │  W + R > N  →  at least 1 node is shared     │
     │  →  reads always see the latest write        │
     │                                               │
     │  Gossip: each node gossips heartbeat to 3    │
     │  random peers every 1s.  Dead if stale >10s  │
     └───────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-kvstore)
