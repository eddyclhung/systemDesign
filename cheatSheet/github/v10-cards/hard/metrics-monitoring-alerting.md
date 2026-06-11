# Metrics Monitoring & Alerting

**Hard** · Vol 2 · Ch.5 · Time-series DB · Pull vs push · Downsampling · Alerting

Tags: `Prometheus`, `Kafka`, `InfluxDB`, `Time-series`, `Downsampling`, `AlertManager`, `Grafana`

**Flow:** Services expose metrics → Collector (pull/push) → Kafka → Time-series DB → Query layer (Grafana) + Alert evaluator → PagerDuty/Slack

---

<details open>
<summary><strong>Problem</strong></summary>

Design a metrics monitoring and alerting system like Datadog or Prometheus. The system must ingest millions of metrics per second from thousands of services, store them efficiently for long-term retention, support fast queries for dashboards, and fire alerts within seconds of a threshold being breached.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Pull vs push collection** — Pull (Prometheus model): collector scrapes /metrics endpoints on a schedule. Easier to detect dead services (no scrape = alert). Push (StatsD/DataDog model): services push metrics to collector. Works behind firewalls, better for short-lived jobs. Production systems often support both.
- **Time-series data model** — Metric = {name, labels, timestamp, value}. Labels enable filtering/grouping: http_requests_total{method='GET', status='200'}. Cardinality explosion: too many unique label combinations → storage and query cost explodes. Cap label cardinality.
- **Kafka as ingest buffer** — Metrics producers → Kafka → time-series DB. Kafka decouples ingest spikes from storage. Allows multiple consumers (storage, alerting, anomaly detection) from one stream.
- **Time-series DB (TSDB)** — Specialized for append-only time-indexed data. Columnar storage, aggressive compression (delta-of-delta + XOR encoding). Prometheus TSDB, InfluxDB, VictoriaMetrics. 10-50× more compact than relational DB for time-series.
- **Downsampling & retention** — Raw data (1s resolution) retained 7 days. Downsampled to 1-min averages retained 30 days. 1-hour averages retained 1 year. Reduces storage 99% for long-term trends.
- **Alert evaluation** — Alert rules evaluated every 30s against TSDB queries. Alert fires when condition true for N consecutive evaluations (prevents flapping). Alert routed to PagerDuty/Slack/email based on severity and team routing rules.
- **Query layer** — PromQL or InfluxQL for ad-hoc queries. Pre-computed rollups for dashboard queries. Query caching for repeated dashboard loads. Grafana as visualization layer.

> Pull collection for services, push for batch jobs. Kafka as ingest buffer. TSDB with delta encoding for storage. Downsampling for long-term retention. Alert evaluator with debounce prevents false pages.

</details>


<details>
<summary><strong>Scale</strong></summary>

At 100K metrics/sec ingest, a single VictoriaMetrics node handles this with room to spare. The scaling challenges are:

1. Cardinality: 1M unique time series × 100-byte label index = 100 GB RAM for the in-memory index. Cap cardinality aggressively.
2. Query fanout: a dashboard with 20 panels × 10 queries each = 200 TSDB queries on page load. Pre-compute panel data or rate-limit dashboard refreshes.
3. Alert evaluation: 10K alert rules × 30s evaluation = 333 rule evaluations/sec. Distribute rule evaluation across multiple alert evaluator nodes.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Three-component framing.
2. "Metrics system has three distinct concerns: collection, storage, and alerting. They have different reliability requirements."
3. "Collection: pull-based scraping from service /metrics endpoints every 10s. Push gateway for batch jobs. Kafka as ingest buffer — decouples scrape spikes from TSDB write throughput."
4. "Storage: time-series DB (Prometheus + VictoriaMetrics for long-term). Raw 1s data for 7 days. Downsample to 1-min for 30 days, 1-hour for 1 year. Delta encoding gives 10:1 compression."
5. "Alerting: rules evaluated every 30s via TSDB queries. Alert fires after N consecutive positive evaluations — prevents flapping. Severity-based routing to PagerDuty vs Slack. Inhibition rules to prevent alert storms."
6. "Critical design constraints: cap label cardinality (no user_id labels), pre-compute dashboard rollups, dead-man's switch to monitor the monitoring system."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
COLLECTION:
  Services → /metrics endpoint
  Scraper (every 10s) ────────────► Kafka
  Push Gateway (batch jobs) ───────► Kafka
                                        |
  STORAGE:                              ▼
                               Time-series DB
  Raw (1s, 7 days)  ◄──────── (VictoriaMetrics)
  1-min avg (30 days)            compression
  1-hour avg (1 year)            10:1 ratio

  ALERTING:
  Alert evaluator (every 30s)
  PromQL query → threshold check
  N consecutive fires → alert
       |
       ├── P1: PagerDuty (page now)
       ├── P2: Slack #alerts
       └── P3: Ticket

  DASHBOARD:
  Grafana → PromQL → TSDB
  Pre-computed rollups for fast load
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-metrics)
