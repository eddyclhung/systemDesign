# Email Service

**Medium** · Vol 2 · Ch.9 · SMTP · MIME · Spam filtering · Storage · Search

Tags: `SMTP`, `IMAP`, `Kafka`, `Elasticsearch`, `Anti-spam`, `MIME`, `Cassandra`

**Flow:** Send: client → SMTP gateway → spam check → queue → SMTP relay → recipient MX. Receive: inbound SMTP → spam filter → object store → index in Elasticsearch

---

<details open>
<summary><strong>Problem</strong></summary>

Design an email service like Gmail. The system must handle sending billions of emails per day across the internet (SMTP), storing petabytes of user email with fast search, and filtering spam. Two distinct problems: being a good email citizen on the internet (deliverability, spam reputation) and building the storage/search/sync system for mailboxes.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **SMTP for sending** — Simple Mail Transfer Protocol. Outbound path: client → SMTP gateway → DNS MX lookup for recipient domain → deliver to recipient's SMTP server. TLS required. SPF/DKIM/DMARC for authentication and anti-spoofing.
- **IMAP/POP3 for reading** — IMAP: server-side mailbox, multiple device sync, partial fetch of headers. POP3: download and delete. IMAP is the modern standard. Gmail also exposes a proprietary API.
- **Email storage** — Emails stored as raw MIME in object storage (S3). Metadata (from, to, subject, date, labels) in Cassandra. Email body indexed in Elasticsearch for full-text search. Never store email body in relational DB.
- **Spam filtering pipeline** — Multi-layer: IP reputation → SPF/DKIM/DMARC validation → content analysis (Bayesian classifier + ML) → URL/attachment scanning → user feedback signals (mark as spam). Runs in parallel to minimize latency.
- **Deliverability** — IP warm-up: don't send millions of emails from a new IP immediately. Start low, ramp up over weeks. Sending reputation tracked by receiving ISPs. Bounce rate, spam complaint rate, authentication pass rate all affect reputation.
- **Thread grouping** — Emails grouped into threads by In-Reply-To and References headers. Thread metadata stored separately. Thread view is a UI concern but requires server-side grouping for fast rendering.
- **Search** — Elasticsearch indexes: from, to, subject, body (tokenized). User searches 'project proposal from alice' → ES query with filters. ES updated async after email stored — 1-5s index lag acceptable.

> SMTP/DKIM for internet delivery. Object storage for raw MIME. Cassandra for metadata. Elasticsearch for search. Kafka-based spam pipeline. Deliverability management is an ongoing operational concern, not just a design choice.

</details>


<details>
<summary><strong>Scale</strong></summary>

The 15 EB storage figure sounds extreme, but it's primarily driven by attachments (photos, documents). Gmail applies aggressive compression and deduplication: identical attachments across users share one copy (content-addressed storage). Photos compressed. This reduces effective storage 3-5×.

The search scaling challenge: 10 TB Elasticsearch index for metadata + subjects. Body search index: 100 TB+. Elasticsearch cluster of 100+ nodes. User-level index sharding: route all queries for user X to the same shard, so user-specific searches never scatter-gather across all nodes.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Two-system framing: internet-facing vs user-facing.
2. "Email service is really two systems: an internet-facing SMTP system (sending and receiving email from/to the world) and a user-facing storage/search/sync system."
3. "Internet-facing: SMTP gateway for inbound. SMTP relay for outbound. SPF/DKIM/DMARC authentication on every outbound email — non-negotiable for deliverability. Spam filter pipeline running async."
4. "User-facing: MIME stored in S3. Metadata (from/to/subject/date/labels) in Cassandra. Full-text search via Elasticsearch. IMAP + proprietary API for client sync."
5. "Critical operational concern: sending reputation. New IPs need warm-up. Monitor bounce rate, spam complaint rate. Route to clean IPs if reputation degrades."
6. "Search: Elasticsearch updated async after store. 5-second lag acceptable. Fallback to metadata-only search (Cassandra) if ES lags."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
SEND FLOW:
  Client → SMTP Gateway
    → SPF/DKIM sign
    → Spam check (Kafka pipeline)
    → DNS MX lookup (recipient domain)
    → SMTP relay → recipient server

  RECEIVE FLOW:
  Inbound SMTP ← sender's server
    → IP reputation check
    → SPF/DKIM/DMARC validate
    → Spam filter (Bayesian + ML)
    → Store MIME in S3
    → Write metadata to Cassandra
    → Index in Elasticsearch (async)
    → IMAP IDLE push to connected clients

  STORAGE:
  S3:          raw MIME files (body + attachments)
  Cassandra:   metadata (from, to, subject, date, labels)
               partition: (user_id, folder)
               cluster: (received_date DESC)
  Elasticsearch: full-text search index
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-email)
