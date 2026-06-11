# Digital Wallet

**Hard** · Vol 2 · Ch.12 · Double-entry bookkeeping · idempotency · Saga pattern · reconciliation · immutable ledger

Tags: `Double-Entry`, `Ledger`, `Idempotency`, `Saga`, `Reconciliation`, `ACID`, `Financial`

**Flow:** Transfer request → idempotency check (Redis + DB) → Saga orchestrator: (1) verify source balance (SELECT FOR UPDATE or optimistic lock), (2) append debit ledger entry, (3) append credit ledger entry, (4) emit Kafka confirmation event. Balance = SUM(ledger entries per account) — never stored as a mutable counter. Reconciliation job hourly: compare ledger sum vs cached balance; alert on mismatch.

---

<details open>
<summary><strong>Problem</strong></summary>

Design a digital wallet (like Venmo, PayPal, or WeChat Pay) supporting fund transfers with consistency, auditability, and retry safety.

Hard parts: (1) Atomicity — debit and credit must both succeed or both fail; no money created or destroyed. (2) Double-charge prevention — network failures cause retries; must not debit sender twice. (3) Cross-shard transactions — sender and recipient may be in different DB shards.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Double-entry bookkeeping** — Every transaction creates two immutable ledger entries: DEBIT from source account, CREDIT to destination. Sum of all credits = sum of all debits = 0 always. Ledger is append-only: never UPDATE or DELETE entries. Balance = SUM(credit_entries) - SUM(debit_entries) per account. Any corruption immediately detectable.
- **Idempotency keys** — Client generates UUID transfer_request_id. Server checks idempotency table before executing. If found: return cached result (same transfer_result). If not found: execute transfer, cache result with TTL=24h. Prevents double-debit when client retries on network timeout. Unique constraint on (idempotency_key) in DB.
- **Saga for cross-shard transfers** — Sender and recipient may be in different DB shards. Saga: (1) lock source account (SELECT FOR UPDATE), verify balance, append DEBIT entry. (2) lock destination account, append CREDIT entry. Compensating transaction: if step 2 fails after step 1: append CREDIT entry back to source (reversal). Log all Saga steps to saga_executions table.
- **Balance derivation vs cached balance** — Balance derived from ledger: SELECT SUM(amount * direction) WHERE account_id = X. Correct but O(N) scans for large transaction history. Optimization: store cached_balance updated in same transaction as ledger entry. Cached_balance is a denormalization for performance. On discrepancy: recompute from ledger (ledger is source of truth).
- **Reconciliation** — Hourly batch job: for each account, compare SUM(ledger) with cached_balance. If mismatch: alert and auto-investigate. External reconciliation: compare with bank settlement files. Regulatory audit: immutable ledger provides complete audit trail. Never purge ledger entries.

> Financial correctness requires the highest guarantees. Double-entry bookkeeping makes corruption detectable. Idempotency prevents double-charge. Saga handles cross-shard transactions without 2PC. Immutable ledger provides complete audit trail. The ledger is the source of truth; cached balance is a performance optimization only.

</details>


<details>
<summary><strong>Scale</strong></summary>

Digital wallet correctness cannot be retrofitted. The double-entry ledger, idempotency key, and Saga pattern must be baked in from day one.

The scaling challenge is not throughput — even Venmo processes far fewer than 1000 transactions per second. The real challenge is the ledger query: computing a user's balance means summing potentially millions of ledger entries. Solution: periodic balance snapshots (monthly checkpoint) + sum only entries since the last snapshot. This bounds the query to at most 30 days of entries regardless of account age.

Fraud at scale: real-time fraud scoring via a parallel stream (Flink) on the transaction Kafka topic. ML model scores each transaction in <50ms. Suspicious transactions flagged for review before settlement.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Correctness-first framing.
2. "Digital wallet has one non-negotiable invariant: no money is created or destroyed. I'll design around that constraint using double-entry accounting."
3. "Every transfer: debit sender + credit recipient in one atomic DB transaction. Balance = SELECT SUM(amount) FROM ledger WHERE user_id=X — always computed, never stored as a field."
4. "Idempotency: every transfer request carries a UUID. Redis SETNX idempotency_key before the DB transaction. Duplicate request? Return cached result. No double-debit."
5. "Saga for external transfers: (1) debit internal wallet, (2) initiate ACH/bank transfer, (3) confirm. Compensation on failure: credit the wallet back."
6. "Daily reconciliation: sum all ledger entries, verify net = 0. Any discrepancy → alert for human review."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
Transfer: User A → User B ($50)
         |
  Payment Service
  ┌─────────────────────────────────┐
  │ 1. Redis SETNX idem_key (24h)  │
  │    → duplicate? return cached  │
  │ 2. BEGIN TRANSACTION            │
  │    INSERT ledger: DEBIT A $50   │
  │    INSERT ledger: CREDIT B $50  │
  │    COMMIT (atomic)              │
  └─────────────────────────────────┘
         |
  Kafka: transfer.completed
         |
  ┌──────┴──────┐
  Notification   Fraud Score
  (async)        (Flink stream)

  BALANCE QUERY:
  SELECT SUM(amount) FROM ledger
  WHERE user_id=A
  → never store balance as column
  → snapshot monthly for performance
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-digital-wallet)
