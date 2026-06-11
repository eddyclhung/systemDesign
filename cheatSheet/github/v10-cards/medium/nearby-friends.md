# Nearby Friends

**Medium** · Vol 2 · Ch.2 · WebSocket · Redis Geo · Location pub/sub · Privacy

Tags: `WebSocket`, `Redis GEO`, `Pub/Sub`, `Location`, `Privacy`, `Fan-out`

**Flow:** Client sends location every 30s → Location Service → Redis GEO + pub/sub → friends' servers → push update via WebSocket

---

<details open>
<summary><strong>Problem</strong></summary>

Design a Nearby Friends feature like Facebook's. Users opt in and can see which friends are physically nearby in real time. Unlike a proximity search (static data), every user's location changes constantly — the challenge is efficiently broadcasting location updates to the right subset of users (only mutual friends) at scale with minimal latency.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **WebSocket for bi-directional push** — Server needs to push location updates to clients without polling. WebSocket persistent connection per user. Each location server handles ~100K connections.
- **Location update pipeline** — Client sends GPS coordinates every 30s. Location service writes to Redis GEO (GEOADD user:{uid} lng lat). Publishes to a Redis pub/sub channel for that user.
- **Friend fan-out via pub/sub** — Each user's location server subscribes to pub/sub channels of all their friends. When friend A moves, A's server publishes. All servers with A's friends subscribed receive the update and push to those clients.
- **Redis GEO for distance queries** — GEORADIUS or GEOSEARCH: find all users within N km. But for Nearby Friends, we don't query all users — we query only friends. Store friend locations in per-user Redis sorted sets or use GEODIST between specific pairs.
- **Privacy opt-in** — Location sharing is opt-in. Store per-user preference. Never broadcast location of users who haven't opted in. Respect 'share with friends only' vs 'share with everyone' settings.
- **Location history** — Cassandra for time-series location history: (user_id, timestamp) → (lat, lng). Enables features like 'was near you 2 hours ago'.
- **Stale location handling** — If no update received for 5 minutes, mark user as location-unknown (may have turned off sharing). Remove from active GEO index.

> The key insight: don't fan-out to all users, only to friends. Redis pub/sub per-user channel makes this natural — each server subscribes to only the channels of users it's hosting.

</details>


<details>
<summary><strong>Scale</strong></summary>

The fan-out math is the critical scale check. 50M active users × 1 update/30s = 1.67M updates/sec. Each update fans out to ~10 online friends = 16.7M WebSocket pushes/sec. Distributed across 800 servers = ~21K pushes/sec/server — very manageable.

The number that hurts: a user with 5000 friends posting frequent updates. Their updates fan out to 5000 servers. Cap fan-out at 500 active friends to bound the worst case.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Two-flow framing: location publish vs location receive.
2. "Nearby Friends has two flows: how a user's location gets to their friends' screens, and how a user sees their friends' locations."
3. "Location publish: client sends GPS every 30s via WebSocket → location service writes to Redis GEO (GEOADD) and publishes to that user's pub/sub channel."
4. "Location receive: each location server subscribes to pub/sub channels for all users it's currently hosting. When a friend moves, the server receives the publish and pushes via WebSocket to the client."
5. "The fan-out is implicit in the pub/sub subscription graph — no explicit fan-out loop needed."
6. "Privacy: opt-in only. Never fan-out for users who haven't enabled sharing. Block list checked before each push."
7. "Scale: 800 WebSocket servers, Redis cluster for GEO + pub/sub, Cassandra for location history."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
Client (GPS every 30s)
         |
  Location Service
  GEOADD user:{uid} lng lat    → Redis GEO
  PUBLISH channel:{uid} {lat,lng}  → Redis Pub/Sub
                                        |
                    ┌───────────────────┤
                    |                   |
             Server A               Server B
         (hosts User B)         (hosts User C)
         subscribed to          subscribed to
         channel:{uid}          channel:{uid}
                    |                   |
          WebSocket push         WebSocket push
          to User B              to User C
          "Friend X is 0.8km away"

  FRIEND FILTER:
  Only fan-out to servers hosting
  active friends of the moving user.
  Check friends:{uid} SET in Redis.
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-nearby-friends)
