# URL Shortener (TinyURL)

**Easy** · Vol 1 · Ch.8 · Base62 encoding · Cache-aside · 302 redirect

Tags: `Redis`, `PostgreSQL`, `Base62`, `Cache-aside`, `CDN`, `302 redirect`

**Flow:** POST /shorten → hash + Base62 encode → store in PG + Redis → GET /{code} → Redis lookup → 302 redirect

---

<details open>
<summary><strong>Problem</strong></summary>

Take a long URL, generate a short code, and redirect users when they visit the short link. Sounds simple, but the challenge is handling a read-to-write ratio of 100:1, generating unique codes at scale, and handling analytics without slowing down redirects.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Base62 encoding** — 62 chars (a-z, A-Z, 0-9). 62^7 = 3.5 trillion codes. 7 characters is sufficient for any realistic URL volume.
- **Counter vs hash** — Counter + Base62 guarantees uniqueness, no collision handling needed. Hash (MD5/SHA-1 truncated) is more distributed but requires collision retry logic.
- **302 vs 301** — 302 (temporary redirect): every click hits your server. Good for analytics. 301 (permanent): browser caches forever. Reduces load but you lose click tracking.
- **Cache-aside** — On redirect: check Redis first. Hit → return immediately. Miss → query PG → populate Redis → return. 99% of reads from cache at steady state.
- **Read-heavy optimization** — 100:1 read-to-write. Cache is the primary optimization. Separate read and write services to scale independently.
- **Expiration** — TTL in DB and cache must match. Short URLs can have optional expiration. Return 410 Gone for expired links.

> Counter + Base62 for uniqueness. Redis cache-aside for read scaling. 302 for analytics. That's the core design.

</details>


<details>
<summary><strong>Scale</strong></summary>

The redirect path is the hot path. Every millisecond counts. The optimization order: (1) in-process LRU for top 1000 links on each server — zero network hops. (2) Redis for the hot 20% — 1ms. (3) PG read replica for cache misses — 5-10ms. The write path (link creation) is cold by comparison and can tolerate DB round-trips.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Clean two-flow framing.
2. "I'll design two flows: URL creation and redirect. They have very different scale requirements — 100:1 read-to-write ratio means redirects are the optimization target."
3. "URL creation: POST /urls. Generate a short code using counter + Base62 (7 chars = 3.5T codes, no collision risk). Write to PG + populate Redis cache. Return short URL."
4. "Redirect: GET /{code}. Check Redis first. Hit: 302 to long URL immediately. Miss: query PG, populate Redis, then 302. I'd use 302 not 301 — preserves click analytics and lets us update destinations."
5. "Scale: 35K redirect QPS. Stateless redirect servers behind LB. Redis cache covers 80%+ of traffic. PG read replica for misses. Local in-process cache for viral links."
6. "Analytics: redirect service publishes to Kafka asynchronously — zero impact on redirect latency. Separate consumer aggregates into ClickHouse."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌──────────────────────────────────────────────────────┐
  │                   WRITE PATH                          │
  │                POST /shorten                          │
  └───────────────────────┬──────────────────────────────┘
                          │
               ┌──────────▼──────────┐
               │    Write Service     │
               │  1. counter INCR    │◄── Redis atomic counter
               │  2. Base62 encode   │    (pre-allocated range)
               │  3. write PG + Redis│
               └──────────┬──────────┘
               ┌───────────┴─────────┐
               ▼                     ▼
      ┌─────────────┐       ┌───────────────┐
      │ PostgreSQL  │       │  Redis Cache  │
      │ short→long  │       │ short→long    │
      │ expiry, meta│       │ TTL = expiry  │
      └─────────────┘       └───────────────┘

  ┌──────────────────────────────────────────────────────┐
  │                   READ PATH                           │
  │               GET /{shortCode}                        │
  └───────────────────────┬──────────────────────────────┘
                          │
               ┌──────────▼──────────┐
               │   Redirect Service   │
               │  (stateless, ×N)    │
               └──────────┬──────────┘
                          │
             ┌────────────┼──────────────┐
             ▼                           ▼
    ┌─────────────────┐       ┌─────────────────────┐
    │  Local LRU      │       │   Redis Cache        │
    │  (top 1000)     │       │   (hot 20% of URLs)  │
    │  0 network hops │       │   ~1ms               │
    └────────┬────────┘       └──────────┬───────────┘
             │ HIT                       │ MISS
             ▼                           ▼
          302 →                ┌──────────────────┐
        long URL               │  PostgreSQL       │
                               │  read replica     │
                               └────────┬──────────┘
                                        │
                                     302 →
                                   long URL

  Kafka ◄── click event (async, no redirect latency impact)
  ClickHouse ◄── Kafka consumer (analytics aggregation)
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-urlshortener)
