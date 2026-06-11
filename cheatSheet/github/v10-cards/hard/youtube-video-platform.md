# YouTube / Video Platform

**Hard** · Vol 1 · Ch.14 · Transcoding pipeline · ABR streaming · CDN

Tags: `S3`, `CDN`, `Kafka`, `HLS/DASH`, `Transcoding`, `Pre-signed URL`, `DAG`

**Flow:** Upload (TUS chunks → S3 raw) → Transcode queue → Parallel workers (per resolution) → HLS segments in S3 + CDN → Viewer streams from CDN edge

---

<details open>
<summary><strong>Problem</strong></summary>

Host and stream video at scale. Two completely different engineering challenges: the write side (ingest and transcode large video files) and the read side (stream to millions of concurrent viewers globally with minimal latency and adaptive quality).

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Pre-signed S3 upload URL** — Client gets a temporary S3 URL directly. Uploads multi-GB video to S3 — API server never handles video bytes. After upload: S3 triggers transcode event.
- **TUS resumable upload** — Chunked upload protocol. Client tracks which chunks succeeded. Resume from last committed chunk on network failure. Essential for mobile uploads and large files.
- **Parallel transcoding by resolution** — DAG pipeline: one worker per resolution (360p, 720p, 1080p, 4K) running simultaneously. Video available at 360p within minutes while 4K is still processing.
- **HLS/DASH adaptive bitrate** — Each resolution = HLS manifest listing 6-second segments. Master manifest lists all resolution variants. Client measures bandwidth, switches quality tier per segment automatically.
- **CDN for video delivery** — Video streamed directly from CDN edge — never from origin. CDN absorbs 99%+ of bandwidth. Popular videos pre-warmed at edge during processing.
- **Origin shielding** — CDN POPs (500+) don't all fetch from S3 on cache miss. A smaller set of 'shield' POPs fetch from S3. All other POPs fetch from shields. Reduces S3 request rate by 50×.
- **Metadata DB separate from blobs** — Video metadata (title, uploader, likes, view count) in PostgreSQL. Video binary data in S3. Never store blobs in relational DB.

> Pre-signed URL for upload (API never touches bytes). Parallel per-resolution transcoding. CDN-first streaming — always from edge, never from origin. ABR for adaptive quality. These four ideas define the architecture.

</details>


<details>
<summary><strong>Scale</strong></summary>

The 5.8 Tbps CDN bandwidth requirement is the most striking number. This is why multi-CDN is not optional at YouTube scale — no single CDN provider has enough capacity in every region. YouTube maintains relationships with Akamai, Google's own CDN infrastructure (GGC caches in ISP data centers), and CloudFlare, routing between them based on real-time latency probes.

The transcode queue is the second scaling concern: 60 TB/hr of incoming video needs to produce 450 TB/hr of transcoded output. GPU instances (Nvidia A100 class) can transcode 1 hour of 4K video in ~5 minutes. 30K upload-hours/hr ÷ 12 (5min transcodes per GPU-hour) = 2,500 GPU instances needed at peak.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Upload then stream framing.
2. "I'll design two flows: video upload and video playback. They have completely different requirements."
3. "Upload: creator gets a pre-signed S3 URL from our API. Client uploads directly to S3 — our servers never touch the video bytes. S3 triggers a transcode event via SQS/Kafka."
4. "Transcoding: DAG pipeline with one worker per resolution running in parallel. 360p available within 2 minutes. 4K finishes last. Output: HLS segments and manifests stored in S3, distributed to CDN."
5. "Playback: viewer requests video. API returns CDN URL for HLS master manifest. Client fetches manifest, measures bandwidth, streams the appropriate quality tier. Quality switches every 6 seconds based on current bandwidth."
6. "CDN is the critical infrastructure — absorbs 99%+ of all bandwidth. App servers handle only metadata APIs."
7. "Origin shielding: CDN POPs don't go to S3 on cache miss — they go to a regional shield POP. Reduces S3 load by 50×."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
═══════════════════ UPLOAD FLOW ══════════════════════

  Creator
     │  1. POST /videos → get upload session + videoId
     ▼
  ┌─────────────────────┐
  │    Video API         │──► Metadata DB (status=PENDING)
  │  (stateless servers) │
  └─────────────────────┘
     │  2. returns pre-signed S3 URL
     ▼
  Creator uploads directly to S3
  (TUS resumable: 10MB chunks, resume on failure)
     │
     ▼
  S3 Raw Bucket  ──► ObjectCreated event ──► SQS/Kafka
                                                │
                                                ▼
  ═══════════════ TRANSCODING PIPELINE ════════════════

  ┌──────────────────────────────────────────────────┐
  │  Processing Orchestrator  (DAG workflow)          │
  │                                                  │
  │    ┌─────────┐  ┌──────────┐  ┌──────────────┐  │
  │    │Splitter │  │Thumbnail │  │  Audio proc  │  │
  │    │(GOPs)   │  │generator │  │  (AAC/Opus)  │  │
  │    └────┬────┘  └──────────┘  └──────────────┘  │
  │         │  (parallel per resolution)             │
  │    ┌────▼────────────────────────────────────┐   │
  │    │  360p    720p    1080p    4K             │   │
  │    │  worker  worker  worker  worker          │   │
  │    │  (GPU spot instances)                   │   │
  │    └────┬────────────────────────────────────┘   │
  └─────────┼────────────────────────────────────────┘
            │  HLS segments (.ts files + .m3u8)
            ▼
  S3 Processed Bucket ──► CDN (push warm for popular)

  ═══════════════════ PLAYBACK FLOW ════════════════════

  Viewer
     │  GET /videos/{id}
     ▼
  ┌──────────────────┐   ┌──────────────────────────┐
  │  Video API        │──►│  Metadata DB + Cache     │
  └────────┬──────────┘   └──────────────────────────┘
           │  returns CDN URL for HLS master manifest
           ▼
  CDN Edge (nearest POP)
     │  serves: master.m3u8  →  lists quality variants
     │  serves: 1080p.m3u8   →  lists all 6s segments
     │  serves: seg001.ts, seg002.ts ...
     ▼
  Client (adaptive bitrate logic):
     bandwidth > 1.3× current → switch UP
     bandwidth < 0.8× current → switch DOWN
     buffer < 10s             → switch DOWN

  ┌────────────────────────────────────────────────────┐
  │  CDN ARCHITECTURE                                  │
  │                                                    │
  │  500+ Edge POPs  →  10-20 Shield POPs  →  S3      │
  │  (serve viewers)     (fetch from S3)    (origin)  │
  │                                                    │
  │  Origin shielding: 50× fewer S3 requests           │
  │  Multi-CDN: route to best-performing CDN/region    │
  └────────────────────────────────────────────────────┘
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-youtube)
