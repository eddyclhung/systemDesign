# Chat System (WhatsApp/Slack)

**Hard** · Vol 1 · Ch.12 · WebSocket · Message ordering · Presence · Group chat

Tags: `WebSocket`, `Cassandra`, `Redis Pub/Sub`, `Snowflake ID`, `HBase`, `Service Mesh`

**Flow:** Client A (WebSocket) → Chat Server A → Message service → Cassandra + Redis pub/sub → Chat Server B → Client B (WebSocket)

---

<details open>
<summary><strong>Problem</strong></summary>

Design a real-time chat system supporting 1-to-1 and group messaging. Core challenges: maintaining persistent WebSocket connections at scale, ensuring message ordering within a conversation, handling offline users, and managing online presence for millions of users.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **WebSocket for real-time** — HTTP is request-response. WebSocket is full-duplex — server can push without client polling. Essential for real-time messaging.
- **Message storage: Cassandra** — Write-heavy, append-only, query by (conversation_id, message_id). Wide column store is perfect. Row key = channel_id, clustering key = message_id (time-ordered). Not relational — no joins needed.
- **Message ordering** — Don't use DB auto-increment — it doesn't work across distributed systems. Use Snowflake IDs: monotonically increasing within a conversation ensures correct order.
- **Presence: heartbeat + Redis** — Client sends heartbeat every 5s. Presence service updates last_active_at in Redis. Threshold: if last_active_at > 30s ago → offline. Fan-out presence changes to friends via Redis pub/sub.
- **Redis pub/sub for routing** — Chat servers subscribe to channels for connected users. When message arrives for user B: publish to Redis channel for user B's connection. Chat server holding B's WebSocket receives it and pushes to B.
- **Group chat fan-out** — Message to group → look up all members → for each online member: publish to their Redis channel. For offline: store in their inbox. Cap group size (e.g., 500) to bound fan-out cost.
- **Offline delivery** — Offline user → store message in inbox table. On reconnect: client sends last_seen_message_id, server delivers all messages since then.

> WebSocket for real-time. Cassandra for message storage. Redis pub/sub for routing across chat servers. Snowflake IDs for ordering. Heartbeat + Redis for presence. These five components together handle 1B users.

</details>


<details>
<summary><strong>Scale</strong></summary>

The critical bottleneck is WebSocket connections — each consumes ~10KB RAM on the server. 500M DAU × 30% online at peak = 150M concurrent connections × 10KB = 1.5 TB RAM. At 64GB RAM per server: 24,000 chat servers. In practice: connections are idle most of the time, multiplexed, and servers can handle 500K connections each — 300 servers.

The second bottleneck is message fan-out for large groups. WhatsApp caps groups at 1024. Telegram caps at 200K (with delivery tradeoffs). Discord uses 50K per server. Choose your cap based on your fan-out budget.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Two-problem framing.
2. "Chat has two distinct hard problems: routing messages to online users in real-time, and reliably delivering messages to offline users. I'll address both."
3. "Real-time routing: WebSocket connections from clients to chat servers. When a message arrives: write to Cassandra (durability), then publish to Redis pub/sub on a channel keyed by recipient user_id. The chat server holding the recipient's connection subscribes to that channel and pushes to the client."
4. "Offline delivery: every message written to a per-conversation inbox in Cassandra. On reconnect: client sends last_seen_message_id. Server queries Cassandra for all messages since then. No gaps."
5. "Message ordering: Snowflake IDs. Monotonically increasing, no coordination, correct sort order within a conversation."
6. "Presence: client heartbeat every 5 seconds. Redis stores last_active_at. Stale > 30s = offline. Presence changes fanned out to friends via pub/sub."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
════════════════ MESSAGE FLOW ════════════════════

  Client A                              Client B
  ┌────────┐                            ┌────────┐
  │ App    │──── WebSocket ────────────►│ App    │
  └───┬────┘                            └────┬───┘
      │                                      │
  ┌───▼──────────────────────────────────────▼───┐
  │              Chat Server Pool                │
  │  (assigned via consistent hash on user_id)   │
  │                                              │
  │  Chat Server 1          Chat Server 2        │
  │  [Client A conn]        [Client B conn]       │
  └──────────────┬──────────────────┬────────────┘
                 │                  │
  ┌──────────────▼──────────────────▼────────────┐
  │              Message Service                  │
  │                                              │
  │  Step 1: Write to Cassandra (durability)     │
  │  Step 2: Publish to Redis pub/sub channel    │
  │          channel = user:{recipient_id}       │
  └──────────────┬──────────────────┬────────────┘
                 │                  │
  ┌──────────────▼──────┐  ┌────────▼────────────┐
  │  Cassandra           │  │  Redis Pub/Sub       │
  │                      │  │                     │
  │  PK: conv_id         │  │  channel per user   │
  │  CK: msg_id (snowfl) │  │  Chat server 2      │
  │  (conversation log)  │  │  subscribed to B's  │
  │                      │  │  channel → pushes   │
  │  Also: inbox table   │  │  to B's WebSocket   │
  │  for offline msgs    │  │                     │
  └──────────────────────┘  └─────────────────────┘

  ════════════════ PRESENCE ═════════════════════

  ┌────────────────────────────────────────────────┐
  │  Client heartbeat every 5s                     │
  │       │                                        │
  │  Presence Service                              │
  │       │                                        │
  │  Redis HSET presence:{uid} last_active now     │
  │                                                │
  │  Fan-out presence change to friends via        │
  │  Redis pub/sub (friends:{uid} channel)         │
  │                                                │
  │  Offline threshold: last_active > 30s ago      │
  └────────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-chat)
