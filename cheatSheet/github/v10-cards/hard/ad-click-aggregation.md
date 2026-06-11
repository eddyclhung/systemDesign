# Ad Click Aggregation

**Hard** · Vol 2 · Ch.7 · Exactly-once · Windowed aggregation · Lambda vs Kappa

Tags: `Kafka`, `Flink`, `ClickHouse`, `Exactly-once`, `Watermark`, `Lambda`, `CQRS`

**Flow:** Ad click event → Kafka → Flink (windowed aggregation, 1-min tumbling windows) → ClickHouse → Query API → Advertiser dashboard

---

<details open>
<summary><strong>Problem</strong></summary>

Design a system that counts ad clicks in real time and provides accurate aggregated reports to advertisers. The challenge: clicks must be counted exactly-once (duplicate events from retries must not double-count revenue), aggregations must be fast enough for real-time dashboards, and the system must handle late-arriving events (mobile users who go offline and reconnect).

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Exactly-once counting** — Click events arrive via Kafka. Idempotency key = click_id (UUID). Dedup within Flink using a stateful operator with 24h window. Flink's exactly-once mode (two-phase commit) ensures no duplicates across checkpoints.
- **Tumbling windows** — Count clicks in fixed non-overlapping 1-minute windows. Window closes at t+60s. Aggregate output: {ad_id, window_start, click_count, spend}. Windows give clean billing epochs.
- **Watermarks for late data** — Mobile clicks may arrive minutes late (offline device). Watermark = current_event_time - max_lateness (e.g., 2 min). Window doesn't close until watermark passes its end time. Late events after watermark: applied to a corrections batch.
- **Lambda vs Kappa architecture** — Lambda: batch layer (exact, slow) + speed layer (approximate, fast) + serving layer merges. Kappa: streaming only, replay Kafka for reprocessing. Kappa is simpler and works when Kafka retains data long enough to replay.
- **ClickHouse for serving** — Aggregated results written to ClickHouse (columnar OLAP). Advertiser queries: 'clicks for ad X in last 7 days by hour' run in milliseconds. MergeTree engine handles append-only aggregates efficiently.
- **Click fraud detection** — Statistical anomalies: same IP clicking same ad 100×/min, click rate 10× baseline. Real-time fraud score computed in Flink alongside aggregation. Fraudulent clicks filtered before counting.
- **Reconciliation** — End-of-day batch job reprocesses raw Kafka events with exact dedup. Compares to streaming aggregates. Discrepancies trigger correction records. Billing always uses reconciled batch numbers.

> Exactly-once + watermarks handles the correctness problems. ClickHouse handles the query performance. Reconciliation handles billing accuracy. Kappa architecture keeps it operationally simple.

</details>


<details>
<summary><strong>Scale</strong></summary>

The dedup state is the surprise scaling bottleneck. 50K unique clicks/sec × 86400 seconds × 24h TTL × 50 bytes/entry = 5 TB of Flink state. This must be RocksDB-backed (spills to disk) rather than in-memory. Checkpoint size and checkpoint interval drive operational cost: 5 TB checkpoint every 30s requires fast storage and network.

The practical solution: reduce TTL. Most duplicates arrive within seconds of the original (retry logic). A 5-minute dedup window catches 99.9% of duplicates with only 15 GB of state. End-of-day reconciliation catches the remaining 0.1% that arrive late.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Correctness-first framing.
2. "Ad click aggregation has one non-negotiable requirement: every click counted exactly once. Get this wrong and advertisers are overcharged or undercharged. I'll design around that constraint."
3. "Ingest: clicks published to Kafka with a click_id UUID. Flink consumes with a stateful dedup operator — if click_id seen before (RocksDB state, 24h TTL), skip. Otherwise count."
4. "Aggregation: tumbling 1-minute windows. Output: {ad_id, window_start, click_count, spend} written to ClickHouse. Real-time dashboard reads from ClickHouse."
5. "Late events: watermarks allow 2-minute grace period for late arrivals. Events later than 2 minutes → corrections queue → end-of-day reconciliation batch."
6. "Billing: always uses end-of-day batch reconciliation numbers, not real-time stream. Real-time is for monitoring. Batch is for money."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
Click event (with click_id UUID)
         |
  Kafka (30-day retention)
         |
  Flink Job
  ┌─────────────────────────────┐
  │ Dedup: check click_id       │
  │   (RocksDB state, 24h TTL)  │
  │ Window: 1-min tumbling      │
  │ Watermark: 2-min lateness   │
  │ Output: {ad_id, ts, count}  │
  └──────────────┬──────────────┘
                 |
  ClickHouse (aggregated, fast queries)
  ad_id | window_start | clicks | spend
  ───────────────────────────────────
  adX   | 14:00:00     | 1,847  | $18.47
         |
  Advertiser dashboard (real-time)

  RECONCILIATION (nightly):
  Kafka replay → exact count → compare
  → correction records → billing
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-adclick)
