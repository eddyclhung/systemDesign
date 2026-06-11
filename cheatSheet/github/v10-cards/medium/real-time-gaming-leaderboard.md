# Real-time Gaming Leaderboard

**Medium** · Vol 2 · Ch.12 · Redis sorted set · Score aggregation · Top-K

Tags: `Redis Sorted Set`, `Top-K`, `Cassandra`, `Fan-out`, `Score Update`, `Pagination`

**Flow:** Player scores → Score service → Redis ZADD + Cassandra → Leaderboard API: ZREVRANGE top-N or ZREVRANK for individual rank

---

<details open>
<summary><strong>Problem</strong></summary>

Design a real-time leaderboard for a game with millions of players. The system must update scores in real time as players complete matches, return the global top-100 instantly, and show any player their own rank among millions of players. The challenge is making rank queries O(log N) rather than O(N) full scans.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Redis sorted set as the core** — ZADD leaderboard score player_id: O(log N). ZREVRANGE leaderboard 0 99: top-100 in O(100). ZREVRANK leaderboard player_id: rank of any player in O(log N). All operations fast regardless of total player count.
- **Score updates** — Player finishes match → ZADD leaderboard new_score player_id. Redis automatically repositions the player. If player_id already exists, score is updated. Atomic — no race conditions.
- **Cassandra as source of truth** — Redis sorted set is the serving layer. Cassandra stores: player_id → total_score, match history, score breakdown. On Redis failure: rebuild sorted set from Cassandra. Cassandra is the durable record.
- **Segmented leaderboards** — Global leaderboard (all players). Regional (US, EU, Asia). Friends leaderboard (intersect global rank with friend list). Seasonal (reset weekly/monthly). Each is a separate Redis sorted set, updated simultaneously on score change.
- **Top-K problem** — ZREVRANGE returns top K efficiently. For very large K (top 10M): Redis sorted set handles it but response size is large. Use pagination: ZREVRANGE 0 99, then 100 199, etc.
- **Rank around me** — Player wants to see their rank + 5 players above and below. ZREVRANK to get rank R, then ZREVRANGE R-5 R+5 to get surrounding players. Two O(log N) Redis operations.
- **Score aggregation for complex games** — Score = sum of many match scores. ZINCRBY instead of ZADD: atomically increment player's score by match_score. No read-modify-write race condition.

> Redis sorted set is purpose-built for this problem. ZADD/ZREVRANK/ZREVRANGE at O(log N) handle all leaderboard operations efficiently. Cassandra as durable source of truth for rebuild.

</details>


<details>
<summary><strong>Scale</strong></summary>

The elegant scaling property of Redis sorted set: at 100M players, ZREVRANK is still O(log 100M) ≈ 27 comparisons. At 1B players: O(log 1B) ≈ 30 comparisons. The rank query time barely changes as the leaderboard grows.

The real scaling question is write throughput: 167K ZINCRBY/sec. Redis single-threaded at 1M ops/sec handles this with 6× headroom. Redis 7.0 introduced threaded I/O, pushing this further. Redis is almost never the bottleneck for leaderboard systems.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Data structure first.
2. "Leaderboard is a solved problem once you choose the right data structure. Redis sorted set gives you exactly what you need: O(log N) for all operations — insert, update, rank lookup, and range query."
3. "Score update: ZINCRBY leaderboard match_score player_id. Atomic — no race condition possible. Player's score incremented, rank automatically adjusted."
4. "Top-100: ZREVRANGE leaderboard 0 99. Returned in O(100) regardless of total player count."
5. "Individual rank: ZREVRANK leaderboard player_id. O(log N). 100M players = 27 comparisons."
6. "Surrounding players: ZREVRANK to get rank R, then ZREVRANGE R-5 R+5."
7. "Durability: Cassandra stores all score history. Redis is the serving layer — rebuild from Cassandra on failure."
8. "Multiple leaderboards: global, regional, friends, seasonal — each a separate sorted set, all updated in one Redis pipeline per score update."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
Match ends → Score Service
         |
  Pipeline (atomic):
  ZINCRBY leaderboard:global     score  player_id
  ZINCRBY leaderboard:region:us  score  player_id
  ZINCRBY leaderboard:season_q2  score  player_id
         |
  Cassandra: INSERT match_result (player_id, score, ts)

  LEADERBOARD QUERIES:
  Top-100:
    ZREVRANGE leaderboard:global 0 99 WITHSCORES

  Player rank:
    ZREVRANK leaderboard:global player_id
    → rank = 15,432 (out of 100M)

  Players around me (rank 15,432):
    ZREVRANGE leaderboard:global 15427 15437 WITHSCORES
    → 11 players centered on rank 15,432

  Top-100 cache: Redis STRING, 1-second TTL
  Prevents stampede on tournament end
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-leaderboard)
