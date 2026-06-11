# Google Maps

**Hard** · Vol 2 · Ch.3 · Graph routing · Segment trees · Map tile CDN

Tags: `Dijkstra`, `A*`, `Geohash`, `CDN`, `Graph`, `ETA`, `Tile`, `S2`

**Flow:** User sets destination → Routing service (graph shortest path) → ETA service → Navigation: client follows route, server updates via GPS stream

---

<details open>
<summary><strong>Problem</strong></summary>

Design a mapping and navigation system like Google Maps. The core problems are: storing and querying a planet-scale road graph (billions of nodes/edges), computing shortest paths in real time (<500ms), serving map tiles efficiently to millions of concurrent users, and providing accurate ETAs that account for real-time traffic.

</details>


<details>
<summary><strong>Key points</strong></summary>

- **Road graph representation** — Nodes = intersections. Edges = road segments with weight = travel_time. Partitioned by geography into tiles. Each graph tile ~10MB, loaded on demand. Total planet graph: ~50 TB.
- **Dijkstra vs A*** — Dijkstra: finds exact shortest path. A* (heuristic): uses straight-line distance to guide search, 10-100× faster for point-to-point routing. Production systems use Contraction Hierarchies (CH) — precomputed shortcuts reduce query time to milliseconds.
- **Contraction Hierarchies** — Offline preprocessing: compute shortcuts between high-importance nodes (highways). Online query: search only the highway graph first, then expand to local roads. 1000× faster than raw Dijkstra. Used by OSRM, Mapbox, Valhalla.
- **Map tiles** — World divided into a quad-tree of tiles at zoom levels 0-20. Each tile = PNG or vector tile. Served from CDN. Client requests only visible tiles. Pre-generated and cached — no real-time rendering on request.
- **ETA calculation** — Base ETA = distance / speed_limit. Adjust for real-time traffic: compare current GPS speeds of anonymous users on each segment vs historical baseline. Traffic heatmap updated every 2 minutes.
- **S2 geometry library** — Google's S2 maps Earth onto a unit sphere, subdivides using a Hilbert space-filling curve. Nearby locations have similar S2 cell IDs. Used for spatial indexing, tile addressing, geofencing.
- **Location data pipeline** — Millions of active navigating users send GPS pings every 15s. Kafka ingests the stream. Stream processor aggregates speed per road segment. Traffic layer updated continuously.

> Contraction Hierarchies for fast routing, CDN-cached tiles for rendering, anonymous GPS stream for real-time traffic — these three components define the architecture.

</details>


<details>
<summary><strong>Scale</strong></summary>

The counterintuitive scaling insight: routing is NOT the bottleneck. 278 routing requests/second is trivial. The bottleneck is tile serving — 1.67M tile requests/second, which the CDN handles. And the data pipeline — 3.3M GPS pings/second into Kafka which requires significant cluster capacity.

The hardest engineering problem is map matching at scale: snapping 3.3M/sec GPS pings to the correct road segment in real time using HMM. This requires holding the full road graph in memory on stream processing nodes.

</details>


<details>
<summary><strong>Script</strong></summary>

1. Three-component framing.
2. "Google Maps has three distinct engineering challenges: tile serving (rendering), routing (graph algorithms), and real-time traffic (stream processing). Each has completely different requirements."
3. "Tile serving: world divided into a quad-tree of tiles at zoom levels 0-20. Pre-generated as vector tiles. Served from CDN. 99%+ cache hit rate. Client renders using WebGL."
4. "Routing: road graph = nodes (intersections) + edges (segments with travel time). Contraction Hierarchies preprocessing reduces cross-country query from seconds to <10ms. A* for local rerouting."
5. "ETA: base = distance/speed_limit. Adjusted by real-time traffic from GPS stream. 50M navigators send pings every 15s → Kafka → stream processor aggregates speed per segment every 2 minutes."
6. "Map matching: GPS pings snapped to road segments via Hidden Markov Model. Handles GPS drift in urban canyons."

</details>


<details>
<summary><strong>Whiteboard</strong></summary>

```
MAP TILE SERVING:
  Client viewport → request visible tile IDs
  CDN Edge (99% HIT) → vector tile bytes
  Client WebGL renderer → pixels on screen

  ROUTING:
  Origin + Destination
         |
  Contraction Hierarchies query
  (precomputed highway shortcuts)
         |
  Route: [segment1, segment2, ...]
         |
  ETA = Σ(length / blended_speed)
  blended = 0.7×realtime + 0.3×historical

  TRAFFIC PIPELINE:
  50M navigators → GPS ping every 15s
         |
  Kafka (3.3M pings/sec)
         |
  Stream processor
  Aggregate: avg speed per road segment
         |
  Traffic layer (updated every 2 min)
         |
  Routing ETA adjustment
```

</details>


---

[← Back to v10 cards index](index.md) · [Interactive version](../../SystemDesign_Complete_v10.html#card-google-maps)
