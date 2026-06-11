# Consistent Hashing

**Medium** · Vol 1 · Ch.5 · Hash ring · Virtual nodes · Minimal redistribution

Tags: `Hash Ring`, `Virtual Nodes`, `Distributed Cache`, `Partitioning`, `Replication`

**Flow:** Key → hash(key) → position on ring → clockwise walk → first server node

---

<details open>
<summary><strong>Problem</strong></summary>

When you have N cache servers and use hash(key) % N to route requests, adding or removing one server remaps almost every key — causing a massive cache miss storm.

Consistent hashing ensures only k/N keys need to be remapped when a node is added or removed. It's the foundational primitive for any distributed data system.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Hash ring** — Servers and keys are both mapped onto a circular ring (0 to 2^32 or 2^160). Key is stored on the first server clockwise from its hash position.
- **Adding a server** — Only keys between the new server and its predecessor need redistribution. ~k/N keys total.
- **Removing a server** — Only keys that mapped to the removed server migrate — to its clockwise successor. ~k/N keys.
- **Virtual nodes** — Each physical server gets V positions on the ring. More positions = more uniform key distribution. V=150 is common in Cassandra.
- **Replication** — Walk clockwise from key position; store on first N unique physical servers. For N=3: replicas on 3 distinct nodes.
- **Hotspot caveat** — Consistent hashing distributes keys uniformly — but NOT traffic. Celebrity keys get 100× more reads regardless of which node they land on.
- **Real-world use** — Cassandra, DynamoDB, Chord, Akamai CDN, Discord all use consistent hashing for data distribution.

> Hash ring + virtual nodes solves uniform distribution. k/N redistribution on topology change is the key property. Traffic hotspots require separate mitigation (read replicas, key salting).

</details>


<details>
<summary><strong>Scale</strong></summary>

The scaling pain is the rebalance operation. Adding a node to a 1TB cluster means migrating ~100GB. During this migration, some keys are in-flight between nodes — you need to handle reads that return stale or missing data.

The solution is a "pending" state: new node is added to the ring but not yet serving traffic. Keys are migrated in the background. Once migration completes, new node flips to active. Reads during migration: check both old and new owner, return whichever responds faster (scatter-gather).

</details>


<details>
<summary><strong>Script</strong></summary>

1. Problem-first framing.
2. "Consistent hashing solves a specific problem: when you add or remove a server in a distributed cache, modulo hashing remaps almost every key — causing a mass cache miss storm. Consistent hashing remaps only k/N keys."
3. "The mechanism: map both servers and keys onto a circular ring using the same hash function. A key is stored on the first server clockwise from its hash position."
4. "Adding a server: it claims the keys between itself and its predecessor. Removing a server: its keys migrate to its successor. Either way, only ~k/N keys move."
5. "Virtual nodes: each physical server gets V positions on the ring. This gives near-uniform distribution even with heterogeneous server sizes."
6. "For replication: walk clockwise from the key, replicate to the first N unique physical servers."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
HASH RING  (0 ──────────────────────────── 2^160)

          0
          │   S0-vn1    S0-vn2
     S2-vn3  *────────────*
       *        ↑             *
      *     K5→ hops to S0-vn2 *
     *                          *
  S2-vn2                    S1-vn1
     *      K3 *     * K1      *
     *          ↓              *
      *     S2 is K3's         *
       *    server          S1-vn2
        *────────────────────*
          S2-vn1    S0-vn3 ──► K2 served by S0

  ┌────────────────────────────────────────────────────┐
  │  VIRTUAL NODES (V=3 shown, production V=150)        │
  │                                                     │
  │  Server 0:  positions [14, 67, 121]                 │
  │  Server 1:  positions [33, 89, 145]                 │
  │  Server 2:  positions [51, 102, 167]                │
  │                                                     │
  │  Key K → hash(K) → walk clockwise → first server   │
  └────────────────────────────────────────────────────┘

  REPLICATION (N=3):
  ┌─────────────────────────────────────────────────────┐
  │  Key → hash → primary node                          │
  │            → 2nd unique physical node (clockwise)   │
  │            → 3rd unique physical node (clockwise)   │
  │                                                     │
  │  "Unique physical" = skip virtual nodes of same box │
  └─────────────────────────────────────────────────────┘

  NODE ADD/REMOVE:
  Add Server 3:  only keys between S3 and its predecessor migrate
  Remove Server: its keys migrate to clockwise successor
  Either case:   ~k/N keys move  (vs (N-1)/N with modulo)
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-consistent-hashing)
