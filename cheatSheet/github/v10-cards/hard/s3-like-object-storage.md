# S3-like Object Storage

**Hard** · Vol 2 · Ch.10 · Erasure coding · Placement · Metadata · Multipart

Tags: `Erasure Coding`, `Consistent Hashing`, `Metadata Service`, `Multipart Upload`, `Replication`, `CRUSH`

**Flow:** PUT object → metadata service (assigns placement) → data nodes (erasure coded shards) → replicated across racks. GET: metadata lookup → fetch shards → reconstruct

---

<details open>
<summary><strong>Problem</strong></summary>

Design an object storage system like Amazon S3. The system must store exabytes of data durably (11 nines, 99.999999999% durability), serve millions of concurrent requests, and do so cost-effectively. The key engineering challenge is balancing durability, availability, and storage efficiency across commodity hardware that fails regularly.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Erasure coding vs replication** — 3-way replication: 3× storage overhead, simple recovery. Erasure coding (e.g., Reed-Solomon 6+3): 1.5× overhead, can lose any 3 of 9 shards and reconstruct. S3 uses erasure coding for cost efficiency at scale. Trade-off: erasure coding recovery requires reading 6 shards; replication reads 1.
- **Data placement with CRUSH algorithm** — CRUSH (Controlled Replication Under Scalable Hashing): deterministic placement of shards across nodes, racks, and availability zones based on a placement map. Given object_id + placement_map → compute exactly which nodes hold each shard. No central placement DB needed.
- **Metadata service** — Maps object_id → {bucket, key, size, etag, shards[{node_id, shard_id}]}. Separate from data nodes. Strongly consistent (Raft-based). The metadata service is the most critical component — losing it means losing access to all objects.
- **Multipart upload** — Large objects split into 5MB-5GB parts. Each part uploaded independently. Server assembles after all parts committed. Enables parallelism (10 parts × 10 Gbps = 100 Gbps effective upload) and resumption after failure.
- **Data node design** — Each data node is a commodity server with many HDDs (S3's design: 2000+ HDDs per rack). Objects stored as files on local disk with a local index (key → file offset). Data nodes report heartbeat to metadata service.
- **Replication across AZs** — Shards distributed across at least 3 availability zones. Single AZ failure cannot cause data loss. Erasure coding stripes across AZ boundaries.
- **Versioning** — Each PUT creates a new version (version_id). Metadata stores all versions. DELETE creates a delete marker (soft delete). Permanent delete removes version. Lifecycle policies auto-expire old versions.

> Erasure coding for storage efficiency. CRUSH for placement without central DB. Metadata service for the index. Multipart for large objects. These four together define object storage at scale.

</details>


<details>
<summary><strong>Scale</strong></summary>

The metadata service is the most critical scaling bottleneck. 1B objects = 1 TB of metadata. This must be consistent, durable, and serve millions of requests/second for lookups. Raft consensus at 1M req/sec requires careful batching and leader optimization.

The data plane bottleneck is erasure coding CPU: reconstructing a shard requires XOR operations over 6 × shard_size bytes of data. Modern CPUs with SIMD/AVX-512 handle this efficiently. Hardware erasure coding acceleration (ISA-L library) achieves 20+ GB/s reconstruction throughput per core.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Durability-first framing.
2. "S3-like object storage is fundamentally a durability problem. How do you store data on commodity hardware (which fails daily at scale) and achieve 11 nines of durability? Erasure coding plus geographic distribution."
3. "PUT flow: client uploads to API gateway → metadata service computes placement via CRUSH algorithm → object sharded and erasure-coded into 9 pieces (RS 6+3) → shards written to 9 data nodes across 3 AZs."
4. "GET flow: metadata lookup → identify which 6+ shards to read → parallel reads from data nodes → Reed-Solomon reconstruction → return object."
5. "Metadata service: Raft cluster, strongly consistent. Maps object_id to shard locations. This is the brain — losing it means losing access to everything."
6. "Large objects: multipart upload. Client splits into 5MB parts, uploads in parallel, server assembles."
7. "Key durability layer: continuous integrity checking — every shard checksummed weekly, silent corruption auto-repaired."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
PUT object:
  Client → API Gateway
    → Metadata Service (CRUSH placement)
    → Shard into 9 pieces (RS 6+3)
    AZ-1: shards 1,2,3
    AZ-2: shards 4,5,6
    AZ-3: shards 7,8,9

  GET object:
  Client → API Gateway
    → Metadata lookup (object→shards)
    → Read any 6 shards in parallel
    → Reed-Solomon reconstruct
    → Return to client

  DATA NODE layout:
  Node = commodity server (JBOD)
  Objects stored as files on local ext4
  Local index: shard_id → file + offset
  Heartbeat to metadata service every 1s

  DURABILITY LAYERS:
  RS(6,3) → survive 3 node failures
  3 AZs  → survive 1 AZ failure
  Checksums → detect silent bit rot
  Versioning → survive accidental delete
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-s3-storage)
