# Search Autocomplete (Google Suggest)

**Medium** · Vol 1 · Ch.13 · Trie · Top-K caching · Batch aggregation

Tags: `Trie`, `Redis`, `Kafka`, `MapReduce`, `Top-K`, `CDN`

**Flow:** Keystroke → API → Redis trie cache → top-K suggestions returned within 50ms

---

<details open>
<summary><strong>Problem</strong></summary>

As a user types, return the top 10 relevant completions within 100ms. At Google scale: billions of queries/day, completions must reflect recent search trends, and the trie data structure must be small enough to serve from cache.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Trie with top-K at each node** — Prefix tree. Each node caches the top-K most frequent completions for that prefix. Query = traverse to prefix node, return cached top-K. No traversal of subtree needed.
- **Batch aggregation, not real-time trie updates** — Don't update the trie on every query. Aggregate query logs daily via MapReduce. Rebuild trie weekly. Hot trending terms can be refreshed more frequently.
- **Redis for trie serving** — Serialize trie into Redis. Key = prefix, value = JSON array of top-K suggestions with scores. HGETALL returns suggestions in <1ms. No tree traversal at query time.
- **CDN for common prefixes** — Top 100 prefixes (single characters, common 2-grams) are static. Cache their suggestions in CDN. Eliminates round-trip for the most common keystrokes.
- **Browser debounce** — Don't query on every keystroke. Query after 100-200ms of no typing. Reduces QPS by ~10× at the client side.
- **Trie sharding** — Shard by first character of prefix (or first 2 characters for finer sharding). 26 primary shards, each independently scalable.
- **Filter inappropriate completions** — Content filter removes hateful/inappropriate suggestions before storing in trie. Allowlist/blocklist maintained separately.

> Cache top-K at every trie node, batch-rebuild weekly from aggregated logs, serve from Redis or CDN. Browser debounce is an underrated optimization — cuts QPS 10× for free.

</details>


<details>
<summary><strong>Scale</strong></summary>

The surprising scaling insight: browser debounce is the most impactful optimization. 10× QPS reduction for free, before any infrastructure change. The second insight: CDN coverage of top 10K prefixes handles 90% of all traffic — the backend only sees the long tail. Together these two techniques mean the backend can be relatively modest even for Google-scale query volumes.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Two-component framing.
2. "Autocomplete has two components: the data pipeline that builds the suggestion index, and the query service that serves suggestions in real-time."
3. "Data pipeline: log all search queries. Aggregate daily via MapReduce to get frequency counts per prefix. Store top-10 completions per prefix in a trie. Serialize trie into Redis with prefix as key and suggestions array as value. Rebuild weekly."
4. "Query service: user types → browser debounces 100ms → API query → Redis HGET on prefix → return top-10 in <5ms. CDN caches results for top 10,000 common prefixes."
5. "For trending events: monitor query log in real-time. Viral term not in trie? Inject as temporary hot-term entry. Expires on next full rebuild."
6. "Trie shard by first character of prefix. 26 shards, each independently scalable."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
════════════════ QUERY PATH ══════════════════════

  User types "sta"
       │  (browser debounces 100-200ms)
       ▼
  ┌────────────────────────────────────────────────┐
  │  Browser / Client                               │
  │  Debounce: only send after 100ms pause          │
  │  (reduces QPS 10× vs per-keystroke)             │
  └──────────────────────┬─────────────────────────┘
                         │ GET /autocomplete?q=sta
  ┌──────────────────────▼─────────────────────────┐
  │  CDN  (top 10K prefixes cached, ~90% HIT rate) │
  └──────────────────────┬─────────────────────────┘
                         │ MISS (rare prefix)
  ┌──────────────────────▼─────────────────────────┐
  │  API Server  (stateless)                        │
  │  Shard routing: first char → shard 's'          │
  └──────────────────────┬─────────────────────────┘
                         │
  ┌──────────────────────▼─────────────────────────┐
  │  Redis   (serialized trie)                      │
  │  HGET trie:sta → ["starbucks","star","startup"] │
  │  with scores (frequency + freshness)            │
  └────────────────────────────────────────────────┘

  ════════════════ DATA PIPELINE ════════════════════

  ┌─────────────────────────────────────────────────┐
  │  Search Query Log  (Kafka stream)                │
  │  10B queries/day                                │
  └──────────────────────┬──────────────────────────┘
                         │
  ┌──────────────────────▼──────────────────────────┐
  │  MapReduce  (runs nightly)                       │
  │  Aggregate: query → frequency count              │
  │  Compute: top-K completions per prefix           │
  └──────────────────────┬──────────────────────────┘
                         │
  ┌──────────────────────▼──────────────────────────┐
  │  Trie Builder                                    │
  │  Build: prefix → [top-10 suggestions + scores]  │
  │  Serialize to Redis (shadow deploy)             │
  └──────────────────────┬──────────────────────────┘
                         │ atomic swap (blue-green)
  ┌──────────────────────▼──────────────────────────┐
  │  Redis  (live trie, 26 shards by first char)    │
  │  500 MB total  │  <1ms lookup latency            │
  └────────────────────────────────────────────────┘

  Hot-term injection: real-time spike detector
  → viral term not in trie → inject temp entry
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-autocomplete)
