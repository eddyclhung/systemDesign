# Scale From Zero to Millions

**Easy** · Vol 1 · Ch.1 · Progressive architecture · 8 scaling laws

Tags: `Load Balancer`, `CDN`, `Redis`, `DB Replication`, `Sharding`, `Stateless Web`

**Flow:** DNS → Load Balancer → Stateless Web Tier → Cache (Redis) → Master DB (writes) / Slave DBs (reads)

---

<details open>
<summary><strong>Problem</strong></summary>

The challenge is not building a system that works for 10 users — that's trivial. The challenge is building one that evolves gracefully from 10 users to 10 million without a full rewrite at each step.

Every architectural decision has a cost. The goal is to defer complexity until the scale actually demands it, and to know precisely which bottleneck to attack at each threshold.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Single server first** — Start with one box. Only split when you hit a real bottleneck — premature separation adds operational cost with no benefit.
- **Separate web and data tiers** — The moment you need to scale them independently, put the DB on its own host. This is almost always step two.
- **Load balancer + horizontal web** — Add a second web server and a load balancer. Now the web tier has no SPOF and can autoscale.
- **DB replication** — Master for writes, slaves for reads. Most apps are 10:1 read-heavy — replicas absorb that ratio.
- **Cache tier** — Redis in front of DB. Cache-aside pattern. Target >90% hit rate. Never use as primary store.
- **CDN for statics** — JS, CSS, images off your origin. 99% of static traffic served from edge. Massive latency reduction globally.
- **Stateless web** — Session state → Redis. Any server handles any request. Autoscaling becomes trivial.
- **Sharding** — When write QPS exceeds single master capacity, shard by a well-distributed key (e.g. hash(user_id)).

> The 8 laws: stateless web · redundancy everywhere · cache aggressively · multi-DC · CDN for statics · shard the DB · split tiers into services · monitor and automate.

</details>


<details>
<summary><strong>Scale</strong></summary>

The hardest part is not any single component — it's knowing which component is the actual bottleneck right now and resisting the temptation to solve tomorrow's problem today.

At small scale, complexity is the enemy. A junior engineer will add Kafka to a system that gets 50 QPS. A senior engineer will run a single Postgres instance until it actually hurts.

The scaling pain inflection points: (1) Single box → needs HA: add a second web server and LB. (2) Read-heavy DB: add replicas and cache. (3) Write-heavy DB: shard. (4) Global latency: multi-DC + CDN. (5) Monolith coupling: microservices.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Top-down framing.
2. "Before I design, a few quick questions: what's the target DAU? And is there a specific component you want me to focus on — web tier, data tier, caching strategy?"
3. "Great. I'll walk through the architecture in stages, adding components as scale demands them rather than front-loading complexity."
4. "Stage 1: single server. Works fine under 10K users. The next bottleneck is always the DB — so stage 2 is separating web and data tiers and adding a read replica."
5. "Stage 3: the web tier becomes the bottleneck. Add a load balancer and a second web server. Move session state to Redis so any server handles any request."
6. "Stage 4: cache tier. Redis in front of the DB. Cache-aside pattern. I'd set TTL based on how stale the data can tolerate being — usually 5 minutes for profile data, shorter for inventory."
7. "Stage 5: CDN for all static assets. This alone removes 99% of bandwidth from our origin servers."
8. "If we needed to go further: shard the DB when write QPS exceeds single master capacity, and add a second data center with GeoDNS routing for global HA."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌─────────────────────┐
                        │   GeoDNS / CDN       │
                        │  static assets edge  │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────▼────────────────────┐
              │             Load Balancer                │
              │          (health checks, TLS)            │
              └──────┬───────────────────────┬──────────┘
                     │                       │
           ┌─────────▼──────┐     ┌──────────▼─────────┐
           │  Web Server 1  │     │   Web Server 2      │
           │  (stateless)   │     │   (stateless)       │
           └────────┬───────┘     └────────┬────────────┘
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │     Redis Cache      │
                    │  (session + data)    │
                    └──────────┬──────────┘
                               │ cache miss
                    ┌──────────▼──────────┐
                    │    Master DB         │◄── all writes
                    │   (PostgreSQL)       │
                    └──────────┬──────────┘
                               │ async replication
              ┌────────────────┼─────────────────┐
              │                │                 │
   ┌──────────▼──────┐ ┌───────▼───────┐ ┌──────▼──────────┐
   │  Read Replica 1  │ │ Read Replica 2│ │  Read Replica 3  │
   └──────────────────┘ └───────────────┘ └──────────────────┘

SCALING STAGES:
  Stage 1: Single box
  Stage 2: Separate web + DB tier
  Stage 3: LB + stateless web + read replicas
  Stage 4: Redis cache (absorb 80%+ reads)
  Stage 5: CDN for statics, GeoDNS for global HA
  Stage 6: DB sharding when write QPS > 5K/sec
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-scale)
