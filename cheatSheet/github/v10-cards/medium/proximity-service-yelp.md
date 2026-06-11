# Proximity Service (Yelp)

**Medium** · Vol 2 · Ch.1 · Geohash · Quadtree · Find nearby businesses

Tags: `Geohash`, `Quadtree`, `Redis GEO`, `PostGIS`, `S2`, `Boundary Problem`

**Flow:** User (lat, lng, radius) → Search service → Geohash lookup → business IDs → Business service → results

---

<details open>
<summary><strong>Problem</strong></summary>

Return N nearest businesses within radius R from the user's current location. Must handle billions of queries per day with sub-100ms response. Unlike Nearby Friends, businesses don't move — this is a static spatial index problem.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Geohash** — Encode lat/lng as base32 string. Nearby locations share a prefix. Level 6 (~1.2km grid) suits most proximity searches. Query: target cell + 8 neighbors (prevents boundary edge cases).
- **Quadtree** — Recursively subdivide 2D space into 4 quadrants until ≤100 businesses per cell. In-memory tree. Fast reads. Complex updates.
- **Boundary problem** — A business just across the cell boundary won't appear in a single-cell query. Always query target cell + all 8 adjacent cells.
- **Redis GEORADIUS** — Redis supports native geo commands: GEOADD, GEORADIUS. Stored as sorted set with score = geohash. Convenient but less flexible than custom geohash approach for complex filters.
- **Read vs write ratio** — Location searches: extremely read-heavy. Business updates: infrequent. Use read replicas heavily. Cache popular city-category combinations.
- **Business service decoupled** — Location search returns business IDs only. Business detail (name, hours, rating) fetched from separate business service (cached in Redis).

> Geohash + 9-cell query solves the boundary problem. Business detail is separate from location lookup. Cache popular (city, category) queries. Read replicas for scale.

</details>


<details>
<summary><strong>Scale</strong></summary>

Read scaling is straightforward: add Redis read replicas, cache popular searches. The challenge is write consistency: business information (hours, address, status) changes frequently. Search index must stay fresh.

Solution: event-driven update pipeline. Business service publishes change events to Kafka. Geohash index consumer updates Redis. Cache invalidation consumer clears affected search caches. All async. Brief staleness (seconds) is acceptable for location search.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Two-service framing.
2. "Proximity service decomposes into two services: a location search service (geospatial index) and a business detail service (metadata). They scale independently."
3. "Location search: geohash-based index in Redis. User location → encode to level-6 geohash → query Redis for businesses in target cell + 8 adjacent cells → return list of business_ids within exact distance."
4. "Business detail: business_ids → fetch from Redis cache (populated from MySQL). Return name, category, rating, hours."
5. "Boundary problem: always query 9 cells. Apply exact Haversine distance filter after geohash lookup to remove false positives from adjacent cells."
6. "Scale: 6 GB geohash index in Redis. Cache popular (city, category) queries. 87K QPS easily handled."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
═══════════════ SEARCH REQUEST FLOW ══════════════════

  User  (lat=37.77, lng=-122.41, radius=5km, cat=food)
     │
  ┌──▼────────────────────────────────────────────────┐
  │  Location Search Service                           │
  │                                                   │
  │  Step 1: encode lat/lng to geohash level 6        │
  │          37.77,-122.41 → "9q8yy"                  │
  │                                                   │
  │  Step 2: find 9-cell neighborhood                 │
  │          target cell + 8 adjacent cells           │
  │          (prevents boundary miss)                 │
  │                                                   │
  │  Step 3: Redis GEORADIUS on all 9 cells           │
  │          → list of business_ids                  │
  │                                                   │
  │  Step 4: exact Haversine distance filter          │
  │          remove businesses > 5km actual dist      │
  │                                                   │
  │  Step 5: return business_ids (sorted by dist)     │
  └──┬────────────────────────────────────────────────┘
     │  business_ids
  ┌──▼────────────────────────────────────────────────┐
  │  Business Service                                  │
  │  Fetch: name, category, rating, hours, photos     │
  │  From:  Redis cache → MySQL (miss)                │
  └──┬────────────────────────────────────────────────┘
     │  enriched results
     ▼
  Return ranked list to user

  ═══════════════ DATA STORES ══════════════════════════

  ┌──────────────────────────────────────────────────┐
  │  Redis GEO  (location index)                     │
  │  GEOADD businesses {lng} {lat} {biz_id}          │
  │  6 GB for 200M businesses                        │
  │  Shard by geohash prefix                         │
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │  MySQL  (business metadata source of truth)      │
  │  id, name, category, lat, lng, hours, rating     │
  │  Sharded by business_id                          │
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │  Redis  (popular query cache)                    │
  │  key = {city}:{category}:{radius}                │
  │  value = top-20 results (serialized)             │
  │  TTL = 10 min  (business hours change daily)     │
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │  Update pipeline  (event-driven)                 │
  │  Business update → Kafka → geo index consumer   │
  │  → Redis GEOADD update + cache invalidation      │
  └──────────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-proximity)
