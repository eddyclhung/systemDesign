# Notification System

**Medium** · Vol 1 · Ch.10 · Push · SMS · Email · Fan-out · Deduplication

Tags: `APNs`, `FCM`, `Kafka`, `Deduplication`, `Fan-out`, `Rate limiting`

**Flow:** API server → Kafka → Channel workers (APNs/FCM/SMS/Email) → Third-party providers → Devices

---

<details open>
<summary><strong>Problem</strong></summary>

Build a system that sends millions of notifications per day across multiple channels (iOS push, Android push, SMS, email) with delivery guarantees, deduplication on retries, and user preference management.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Multi-channel routing** — iOS → APNs. Android → FCM. SMS → Twilio/Nexmo. Email → SendGrid/Mailchimp. Each channel has its own worker pool and rate limits.
- **Message queue per channel** — Decouple notification service from channel workers. One Kafka topic per channel type. Workers can scale independently.
- **Deduplication** — At-least-once delivery means the same notification might be dispatched twice on retry. Redis set with event_id + TTL prevents duplicate sends.
- **Device token management** — APNs/FCM tokens expire and change. On delivery failure, detect invalid token, remove from DB, don't retry. Token refresh on app open.
- **User preferences** — Check opt-out before enqueuing. Per-channel, per-category opt-outs. Cache preferences in Redis.
- **Retry with backoff** — Third-party provider failures are transient. Retry with exponential backoff + jitter. Dead-letter queue for permanently failed deliveries.
- **Rate limiting** — Don't spam users. Max N notifications/user/hour. Configurable per notification category.

> The three reliability guarantees: deduplication (event_id in Redis), retry (exponential backoff + DLQ), and preference checking (before enqueue, not after). Always check preferences before publishing to queue.

</details>


<details>
<summary><strong>Scale</strong></summary>

The fan-out problem is the main scaling challenge: one viral event → 10M notifications. The bottleneck is not Kafka (handles millions/sec) — it's the third-party providers (APNs, FCM). APNs rate limits per certificate. FCM has token-level rate limits.

Mitigation: stagger the fan-out. Don't enqueue all 10M at once — batch enqueue over 60 seconds. Monitor third-party error rates and back off when limits are hit. For SMS and email, the cost per message also makes staggering economically necessary.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Three-channel framing.
2. "Notification system has three hard problems: multi-channel routing, delivery guarantees, and scale spikes from viral events. I'll address each."
3. "Architecture: API service → Kafka (one topic per channel type) → channel workers → APNs/FCM/Twilio/SendGrid."
4. "Delivery guarantee: at-least-once delivery from Kafka. Deduplication in workers: Redis SETNX on event_id with 24h TTL — prevent duplicate sends on retry."
5. "User preferences checked before enqueuing — never waste queue capacity on opted-out users. Preferences cached in Redis."
6. "Scale spikes: Kafka absorbs bursts. Worker autoscaling based on consumer lag. Third-party rate limit monitoring with exponential backoff."
7. "Device token invalidation: APNs/FCM errors on invalid tokens → immediate token removal from DB."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌───────────────────────────────────────────────────────┐
  │                  API / Trigger Layer                   │
  │  Marketing   Transactional   System   Scheduled       │
  │  campaign    (order conf.)   alert    (reminders)     │
  └──────────────────────────┬────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    Notification Service      │
              │                             │
              │  1. Check user prefs (Redis) │
              │  2. Deduplicate (event_id)   │
              │  3. Per-user rate limit      │
              │  4. Route by channel type   │
              └──────┬──────────────────────┘
                     │
       ┌─────────────┼───────────────┬──────────────┐
       │             │               │              │
  ┌────▼────┐ ┌──────▼─────┐ ┌──────▼───┐ ┌────────▼────┐
  │  Kafka  │ │   Kafka    │ │  Kafka   │ │   Kafka     │
  │ ios-push│ │android-push│ │   sms    │ │   email     │
  └────┬────┘ └──────┬─────┘ └──────┬───┘ └────────┬────┘
       │             │               │              │
  ┌────▼────┐ ┌──────▼─────┐ ┌──────▼───┐ ┌────────▼────┐
  │  iOS    │ │ Android    │ │  SMS     │ │   Email     │
  │ Workers │ │  Workers   │ │ Workers  │ │  Workers    │
  └────┬────┘ └──────┬─────┘ └──────┬───┘ └────────┬────┘
       │             │               │              │
       ▼             ▼               ▼              ▼
     APNs           FCM           Twilio        SendGrid
       │             │               │              │
       └─────────────┴───────────────┴──────────────┘
                             │
                       Devices / Inboxes

  ┌───────────────────────────────────────────────────────┐
  │                 RELIABILITY LAYER                      │
  │                                                       │
  │  Deduplication:  Redis SETNX event_id (24h TTL)       │
  │  Retry:          exponential backoff + DLQ            │
  │  Preferences:    Redis cache (opt-out per channel)    │
  │  Invalid tokens: remove on APNs/FCM error response   │
  └───────────────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-notification)
