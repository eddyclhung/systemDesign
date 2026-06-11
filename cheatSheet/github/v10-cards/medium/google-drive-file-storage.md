# Google Drive / File Storage

**Medium** · Vol 1 · Ch.15 · Block-level storage · Delta sync · Deduplication

Tags: `S3`, `Block Storage`, `Delta Sync`, `Deduplication`, `Cassandra`, `Conflict Resolution`

**Flow:** Client → chunked upload → block hashes computed → only changed blocks uploaded to S3 → metadata updated → sync events to other devices

---

<details open>
<summary><strong>Problem</strong></summary>

Design a file storage and sync system. Users upload files, access them from multiple devices, and changes sync automatically. Core challenges: handling large files efficiently (don't re-upload unchanged content), concurrent edits, and offline support.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Block-level storage** — Files split into fixed blocks (4MB each). Each block identified by SHA-256(block_content). Only changed blocks need uploading. A 1GB file with a 1-line edit = only 1 block re-uploaded.
- **Content-addressed deduplication** — If SHA-256(block) already exists in the block store, don't upload — just reference the existing block. Multiple files sharing the same content don't duplicate storage.
- **Metadata DB vs block storage** — Metadata DB: file_id, path, owner, version, blocks[] array. Block store: S3, addressed by block hash. DB query returns block list; client fetches blocks from S3 in parallel.
- **Delta sync** — Client maintains local block map. On sync: compare local blocks with server blocks. Only upload/download changed blocks. Network usage proportional to change size, not file size.
- **Conflict resolution** — Two devices edit same file offline. Server receives two conflicting versions. Default: keep both (Dropbox creates 'Conflicted Copy'). Advanced: three-way merge for text files.
- **Sync notification** — Server sends change events to connected devices via WebSocket or long polling. Device receives event → downloads changed blocks.
- **Offline support** — Client queues changes locally while offline. On reconnect: replay local queue, detect conflicts, sync.

> Block-level storage + content-addressed deduplication is the core insight. Only changed blocks sync. Identical content across files shares storage. This is what makes Dropbox and Google Drive efficient.

</details>


<details>
<summary><strong>Scale</strong></summary>

The 500 PB raw storage number sounds daunting, but S3 handles it transparently. The real scaling challenge is the metadata layer at 50 TB — this is too large for a single MySQL instance.

Sharding strategy: shard metadata by user_id using consistent hashing. Each shard holds ~50 GB of metadata. 1000 shards = 50 TB covered. Cross-shard queries (e.g., "find all files with this content hash across all users") are expensive — avoid by designing APIs to always query by user_id first.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Three-store framing.
2. "Google Drive has three distinct storage concerns: file metadata (what files exist, their versions, their block lists), block content (the actual bytes), and sync state (which devices have which versions)."
3. "Block-level storage: files split into 4MB blocks, each identified by SHA-256(content). Only changed blocks sync — a 1GB file with a 1-line edit transfers only 4MB."
4. "Deduplication: if SHA-256(block) already exists in S3, don't upload — just reference it. Identical content across users and versions shares one copy of each block."
5. "Sync: on file change, client computes block diff vs last-synced state. Uploads only new/changed blocks. Server sends sync event to other devices via WebSocket. Devices download only changed blocks."
6. "Conflicts: optimistic locking with version number on file. Two concurrent edits → second write rejected with 409. Client creates a forked version (Dropbox-style conflicted copy). User resolves manually."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
═══════════════ UPLOAD / SYNC FLOW ═══════════════════

  Client (File changed)
     │
  ┌──▼──────────────────────────────────────────────┐
  │  Block Engine (client-side)                      │
  │                                                  │
  │  1. Split file into 4MB blocks                   │
  │  2. Compute SHA-256 per block                    │
  │  3. Compare with last-sync block map             │
  │  4. Identify NEW or CHANGED blocks only          │
  └──┬──────────────────────────────────────────────┘
     │  POST /sync  {file_id, version, blocks[]}
     ▼
  ┌─────────────────────────────────────────────────┐
  │  Sync Service                                    │
  │                                                  │
  │  Check: server_version == client_expected?       │
  │  NO → 409 Conflict (client re-fetches, merges)  │
  │  YES → continue                                 │
  └──┬──────────────────────────────────────────────┘
     │
     ├──► Check block store: does SHA-256 exist?
     │         YES → skip upload (dedup!)
     │         NO  → upload block to S3
     │
  ┌──▼──────────────────────────────────────────────┐
  │  Metadata DB  (Cassandra, shard by user_id)      │
  │                                                  │
  │  file_id → {path, owner, version, blocks[]}      │
  │  version atomically incremented                  │
  └──┬──────────────────────────────────────────────┘
     │
  ┌──▼──────────────────────────────────────────────┐
  │  Notification Queue (Kafka)                      │
  │  → sync events pushed to other devices          │
  └──┬──────────────────────────────────────────────┘
     │  WebSocket push to connected devices
     ▼
  Device B: download only changed blocks from S3

  ═══════════════ STORAGE LAYERS ═════════════════════

  ┌──────────────────────────────────────────────────┐
  │  Block Store    S3                               │
  │  key = SHA-256(block_content)                    │
  │  Same block used by multiple files/versions      │
  │  → content-addressed deduplication               │
  │                                                  │
  │  Metadata DB   Cassandra                         │
  │  file hierarchy, version history, block lists   │
  │                                                  │
  │  Cache          Redis                            │
  │  hot file metadata, recent block hashes          │
  └──────────────────────────────────────────────────┘

  CONFLICT RESOLUTION:
  ┌──────────────────────────────────────────────────┐
  │  Optimistic locking: every write includes        │
  │  expected_version. Mismatch → 409.               │
  │                                                  │
  │  Client forks: keep both versions                │
  │  (file.txt + file_conflict_2026.txt)             │
  │  User resolves manually                          │
  └──────────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-googledrive)
