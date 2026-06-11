# Rate Limiter

**Medium** · Vol 1 · Ch.4 · Token bucket · Sliding window · Redis counter

Tags: `Redis`, `API Gateway`, `Token Bucket`, `Sliding Window`, `Distributed`

**Flow:** Client → API Gateway (rate check via Redis) → Backend Service — or → 429 Too Many Requests

---

<details open>
<summary><strong>Problem</strong></summary>

Rate limiting prevents a single client from overwhelming your system. Without it, a single buggy client, a DDoS, or a viral API integration can bring down your entire backend.

The challenge: enforce limits correctly under distributed traffic, where requests for the same user hit different servers, without adding significant latency to every API call.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Token bucket (default)** — Bucket holds N tokens. Tokens refill at rate R/s. Each request consumes 1. Burst-tolerant. Used by Amazon and Stripe.
- **Leaky bucket** — FIFO queue. Fixed outflow rate. Smooths bursts into steady stream. Used by Shopify.
- **Fixed window counter** — Count requests per fixed time window. Simple. Vulnerability: burst at window boundary doubles effective rate.
- **Sliding window log** — Store timestamp of each request. Accurate. High memory — stores every timestamp.
- **Sliding window counter** — Hybrid: weighted average of current + previous window. Best accuracy-to-memory tradeoff.
- **Redis as counter store** — INCR + EXPIRE on key = user_id:minute. Atomic. Shared across all API servers. ~1ms overhead.
- **Rate limit headers** — Always return X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After in 429 responses.
- **Multi-tier limits** — Per-IP, per-user, per-endpoint. Global limit as safety net. Different buckets for different API tiers.

> Token bucket for burst-tolerance, sliding window counter for accuracy. Redis for shared state. Always return Retry-After so clients back off intelligently.

</details>


<details>
<summary><strong>Scale</strong></summary>

The scaling pain in rate limiting is Redis becoming the bottleneck — every API request adds 2 Redis ops. At 500K QPS that's 1M Redis ops/sec.

Redis Cluster shards keys by hash slot. The rate limit key is user_id — naturally distributed. At 500K API QPS, a 6-node Redis cluster (each handling ~165K ops/sec, well within Redis's 500K ops/sec per node capacity) is sufficient with headroom.

The second pain is hot keys — a single high-traffic API key (enterprise customer making 50K req/min) creates a hot Redis key. Mitigation: local in-process token bucket for known high-volume keys, syncing with Redis every 100ms instead of every request.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Two-layer framing.
2. "Rate limiter has two concerns: the algorithm for counting, and the storage for sharing counts across servers. Let me address both."
3. "Algorithm: I'd use token bucket by default — burst-tolerant, memory-efficient, easy to explain to clients. Each user has a bucket of N tokens that refills at R/s. Request consumes one token. If empty: 429."
4. "Storage: Redis with INCR + EXPIRE. Key is user_id:window. This is atomic — no race conditions. Adds ~1ms per request, negligible against typical API latency."
5. "Placement: API gateway checks global per-user limits. Service middleware handles per-endpoint limits. Return X-RateLimit-Remaining and Retry-After so clients back off intelligently."
6. "For multi-DC: each DC enforces locally. Slight over-limit at boundaries is acceptable. For strict global limits, I'd sync counters with eventual consistency and accept rare over-limit edge cases."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌─────────────────────────────────────────────────────┐
  │                    Client Request                    │
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │                    API Gateway                       │
  │           (rate check middleware here)               │
  └───────────┬──────────────────────────┬──────────────┘
              │                          │
  ┌───────────▼──────────┐   ┌───────────▼──────────────┐
  │   Rate Limit Check    │   │   If ALLOWED: forward    │
  │                       │   │   to Backend Service     │
  │  INCR key             │   └──────────────────────────┘
  │  key = user:window    │
  │  GET count            │   ┌──────────────────────────┐
  │  count > limit?       │   │   If BLOCKED: return     │
  └───────────┬───────────┘   │   429 Too Many Requests  │
              │               │   + Retry-After header   │
  ┌───────────▼───────────┐   └──────────────────────────┘
  │    Redis Cluster       │
  │                        │
  │  user_id:minute → N    │  ← INCR (atomic)
  │  TTL = 60s             │  ← EXPIRE auto-resets
  │                        │
  │  Token bucket state:   │
  │  {tokens, last_refill} │
  └────────────────────────┘

  MULTI-TIER LIMITS:
  ┌──────────────────────────────────────────────────────┐
  │  IP limit       │ user limit   │  API key tier limit  │
  │  (DDoS guard)   │ (per-account)│  (free/pro/enterprise│
  └──────────────────────────────────────────────────────┘

  ALGORITHM (Token Bucket):
  bucket = {tokens: N, last_refill: ts}
  on request:
    refill = min(N, tokens + rate*(now-last_refill))
    if refill >= 1: allow, tokens = refill - 1
    else: reject 429
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-ratelimiter)
