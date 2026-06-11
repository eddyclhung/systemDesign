# Web Crawler

**Medium** · Vol 1 · Ch.9 · BFS URL frontier · Politeness · Deduplication · Bloom filter

Tags: `URL Frontier`, `Bloom Filter`, `BFS`, `Consistent Hashing`, `robots.txt`, `DNS Cache`

**Flow:** Seed URLs → URL Frontier (priority + politeness queues) → Downloader workers → Content parser → URL extractor → Dedup check → URL Frontier

---

<details open>
<summary><strong>Problem</strong></summary>

Build a distributed web crawler that can index billions of pages while respecting robots.txt, not overwhelming target servers, avoiding crawl loops, and handling duplicate content. The graph traversal, politeness, and deduplication problems all interact.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **BFS, not DFS** — DFS goes arbitrarily deep into one domain. BFS ensures breadth — important for broad web coverage. URL frontier is a priority queue implementing BFS.
- **URL frontier: two queues** — Priority queue (what to crawl next, scored by PageRank/freshness). Politeness queue (enforces ≥1s delay per domain). URLs must pass both.
- **Bloom filter for URL dedup** — Before adding a URL to the frontier, check Bloom filter. If definitely absent: add. If possibly present: discard. O(1) check, tiny memory. ~1% false positive rate is acceptable.
- **Content dedup** — Hash the downloaded page content. If hash already seen: skip indexing. Handles mirrors and syndicated content.
- **robots.txt** — Fetch and cache robots.txt per domain before crawling. Respect Disallow rules. Re-fetch robots.txt periodically (TTL ~24h).
- **DNS caching** — DNS resolution per URL without caching is a major bottleneck. Cache DNS results per domain (TTL ~1 min). Reduces DNS lookup from 100ms to 0.
- **Consistent hashing for workers** — Distribute URLs to downloader workers by consistent hashing on domain — ensures same domain always hits same worker, making per-domain rate limiting trivial.

> The two hard problems are politeness (don't hammer a single host) and dedup (don't re-crawl the same content twice). Bloom filter solves URL dedup. Politeness queue with domain rate limiting solves the server overload problem.

</details>


<details>
<summary><strong>Scale</strong></summary>

The two scaling bottlenecks are: (1) the URL frontier growing faster than it can be processed (queue depth explodes), and (2) DNS resolution becoming a bottleneck. URL frontier: use Kafka as the durable URL queue — handles millions of URLs/sec, partitioned by domain hash. DNS: dedicated DNS cache cluster shared across all workers, with pre-seeded common domains. Monitor: queue depth per domain (detect stalls), DNS cache hit rate (target >99%), per-domain crawl rate (ensure politeness compliance).

</details>


<details>
<summary><strong>Script</strong></summary>

1. Politeness-first framing.
2. "A web crawler has two hard problems: not being banned by target servers, and not re-crawling the same content. I'll design around those constraints."
3. "URL frontier: two-level queue. Priority queue determines what gets crawled first (PageRank-weighted). Politeness queue enforces ≥1s delay per domain. URLs pass through both before being dispatched to downloader workers."
4. "Workers distributed by consistent hashing on domain — same domain always goes to same worker, making per-domain rate limiting trivial."
5. "Deduplication: Bloom filter for URL dedup before adding to frontier. Content hash for exact duplicate detection after download. SimHash for near-duplicate detection."
6. "Robots.txt fetched and cached per domain. Respected before any crawl."
7. "DNS caching: per-worker in-memory DNS cache eliminates repeated DNS lookups for the same domain."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
┌─────────────────────────────────────────────────────┐
  │                  Seed URL Queue                      │
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │                  URL Frontier                        │
  │                                                     │
  │  ┌─────────────────────────────────────────────┐    │
  │  │  Priority Queue   (PageRank/freshness score) │    │
  │  └──────────────────────┬──────────────────────┘    │
  │                         ▼                           │
  │  ┌─────────────────────────────────────────────┐    │
  │  │  Politeness Queues  (one queue per domain)   │    │
  │  │  domain A: [url1, url2...]  delay ≥1s        │    │
  │  │  domain B: [url3, url4...]  delay ≥1s        │    │
  │  └──────────────────────┬──────────────────────┘    │
  └──────────────────────────┼─────────────────────────┘
                             │  (consistent hash by domain)
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │ Downloader  │   │ Downloader  │   │ Downloader  │
  │  Worker 1   │   │  Worker 2   │   │  Worker N   │
  │             │   │             │   │             │
  │ DNS cache   │   │ DNS cache   │   │ DNS cache   │
  │ robots.txt  │   │ robots.txt  │   │ robots.txt  │
  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
         └─────────────────┼──────────────────┘
                           │
              ┌────────────▼────────────┐
              │    Content Processor    │
              │                        │
              │  ┌─────────────────┐   │
              │  │  HTML Parser    │   │
              │  │  URL Extractor  │   │
              │  └────────┬────────┘   │
              │           │            │
              │  ┌────────▼────────┐   │
              │  │  Content Hash   │   │  ← exact dedup
              │  │  (SHA-256)      │   │
              │  └────────┬────────┘   │
              └───────────┼────────────┘
                          │
              ┌───────────▼────────────┐
              │    URL Dedup Check     │
              │                        │
              │  Bloom Filter          │  ← O(1), ~1% FPR
              │  (1B URLs → 1.25 GB)   │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐   NOT SEEN
              │  URL Frontier          │◄──────────── new URLs
              │  (loop back)           │
              └────────────────────────┘

  Storage:
  ┌────────────────────────────────────────────────────┐
  │  S3 / HDFS   ← raw HTML + parsed content           │
  │  Cassandra   ← crawl metadata (URL, status, ts)    │
  │  Elasticsearch ← inverted index for search          │
  └────────────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-webcrawler)
