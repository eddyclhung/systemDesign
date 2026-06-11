# News Feed (Facebook/Twitter)

**Hard** · Vol 1 · Ch.11 · Fan-out on write · Fan-out on read · Hybrid

Tags: `Redis Sorted Set`, `Kafka`, `Fan-out`, `Graph DB`, `CDN`, `Pagination`

**Flow:** Post created → Fan-out service → Write post_id to follower feed caches → Read: Redis feed cache → hydrate from post/user cache

---

<details open>
<summary><strong>Problem</strong></summary>

Design a system where users see a personalized, chronologically-ordered feed of posts from accounts they follow. At scale, the fan-out problem (one post reaching millions of followers) and the feed freshness problem (celebrity accounts can't push to all followers in real-time) become the central challenges.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Fan-out on write (push model)** — When a post is created, immediately write post_id to every follower's feed cache. Fast reads. Expensive writes for high-follower accounts.
- **Fan-out on read (pull model)** — On feed request, fetch posts from all followees. Merge and sort. Flexible but slow for users following 1000+ accounts.
- **Hybrid approach (production)** — Push for regular users (<10K followers). Pull for celebrities. On feed request: merge pre-computed feed (from cache) with real-time pull from celebrities being followed.
- **Redis sorted set per user** — Each user's feed: ZADD feed:{user_id} timestamp post_id. ZREVRANGE for paginated feed. Only store post_ids — hydrate full content separately.
- **Feed cache size limit** — Store only most recent 1000 post_ids per user. Older posts loaded from DB directly. Most users never scroll past 1000 posts.
- **Graph DB for social graph** — Friend/follower relationships are graph traversal problems. Neo4j or purpose-built graph DB (Facebook TAO) for friend-of-friend queries.
- **Post hydration** — Feed contains only IDs. Hydrate post content and user profile from post cache and user cache separately. Parallelizable.

> Fan-out on write for regular users, pull for celebrities, merge on read. Redis sorted set per user. Hydrate content after getting IDs. That's the production model.

</details>


<details>
<summary><strong>Scale</strong></summary>

The celebrity problem is the defining scaling challenge. The top 1000 accounts (Kardashians, Musk, Obama) combined have followers in the hundreds of millions. A post from any of them triggers a fan-out that would take hours with naive push.

Hybrid solves this but introduces merge complexity. The merge operation at read time: ZREVRANGE the pre-computed feed + pull last N posts from each celebrity followee + merge + re-rank. This is O(celebrities_followed × N) — at 10 celebrities followed × 50 latest posts = 500 item merge. Fast.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Fan-out scale framing.
2. "News feed has one defining challenge at scale: the fan-out problem. When Beyoncé posts, we can't push to her 200M followers in real-time. So we need a hybrid model."
3. "Two flows: feed publishing and feed retrieval."
4. "Publishing: user posts → fan-out service → for regular users (<10K followers): write post_id to each follower's Redis sorted set immediately. For celebrities: skip the push."
5. "Retrieval: user requests feed → fetch pre-computed feed from Redis sorted set → merge with recent posts from celebrities they follow → hydrate post + user data from caches → return."
6. "Storage: Redis sorted set per user. score = timestamp, member = post_id. Store only IDs, hydrate content separately. Cap at 1000 recent posts."
7. "Deletion: don't purge feed cache. Just skip deleted/banned posts at hydration time."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
═══════════════ WRITE PATH (fan-out) ════════════════

  User creates post
         │
  ┌──────▼──────────┐
  │  Post Service   │──► Cassandra (durable post store)
  │  write post     │──► Redis (post content cache)
  └──────┬──────────┘
         │ publishes event
  ┌──────▼──────────┐
  │  Fan-out Service│
  │  (Kafka worker) │
  └──────┬──────────┘
         │
  ┌──────▼──────────────────────────────────────────┐
  │  Is poster a celebrity? (followers > 10K)       │
  │                                                 │
  │  NO (regular user):                             │
  │  → ZADD feed:{follower_id} ts post_id           │
  │    for each of N followers (in parallel)        │
  │                                                 │
  │  YES (celebrity):                               │
  │  → SKIP pre-push  (pull on read instead)        │
  └─────────────────────────────────────────────────┘

  ═══════════════ READ PATH (feed retrieval) ══════════

  User requests feed
         │
  ┌──────▼──────────────────────────────────────────┐
  │  Feed Service                                   │
  │                                                 │
  │  1. ZREVRANGE feed:{user_id} 0 49               │
  │     → pre-computed post_ids (regular users)     │
  │                                                 │
  │  2. Pull last 20 posts from each followed       │
  │     celebrity (direct Cassandra reads)          │
  │                                                 │
  │  3. Merge + sort by timestamp                   │
  │                                                 │
  │  4. Hydrate: post_ids → post content cache      │
  │             user_ids  → user profile cache      │
  └──────┬──────────────────────────────────────────┘
         │
  ┌──────▼──────────┐   ┌──────────────────────┐
  │  Redis Cluster  │   │  Cassandra            │
  │                 │   │                       │
  │  feed:{uid}     │   │  post store           │
  │  sorted set     │   │  (source of truth)    │
  │  (1000 post_ids)│   │                       │
  │  post cache     │   │  social graph         │
  │  user cache     │   │  (who follows whom)   │
  └─────────────────┘   └──────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-newsfeed)
