# Staff+ Interview Prep (v15)

GitHub-friendly view of **v15**. Use the links below — GitHub renders Markdown natively. For search, tabs, and interview mode, open the [interactive HTML](../system_design_cheatsheet_v14.html).

## Delivery framework

1. **Requirements** (3–5 min) — functional + NFRs, draw out-of-scope line
2. **Estimation** — QPS, storage, bandwidth to justify decisions
3. **API design** — REST / WebSocket / gRPC, name routes explicitly
4. **Data model** — entities, SQL vs NoSQL with justification
5. **High-level design** — client → LB → services → DB/cache
6. **Deep dives** — 2–3 hardest problems, tradeoffs, failure modes

**Architecture framework** — skeleton → 2 questions → 5 archetypes (feed, transactional, real-time, marketplace, pipeline). Derive designs instead of memorizing them.

**Key numbers:** Redis ~100K–1M ops/s · Single DB ~10K–50K QPS · Kafka ~1M+ msgs/s · Cross-region ~100–200ms

[Full interactive cheatsheet](../system_design_cheatsheet_v14.html) includes DB chooser, cloud commands, and estimation worksheet.

---

## Easy (4)

- [Bitly — URL shortener](easy/bitly-url-shortener.md)
- [Dropbox — file storage](easy/dropbox-file-storage.md)
- [Local delivery (GoPuff)](easy/local-delivery-gopuff.md)
- [News aggregator (Google News)](easy/news-aggregator-google-news.md)

## Medium (18)

- [Ticketmaster — seat booking](medium/ticketmaster-seat-booking.md)
- [WhatsApp — messaging](medium/whatsapp-messaging.md)
- [FB News Feed](medium/fb-news-feed.md)
- [Tinder — dating app](medium/tinder-dating-app.md)
- [LeetCode — coding platform](medium/leetcode-coding-platform.md)
- [Distributed rate limiter](medium/distributed-rate-limiter.md)
- [FB Live Comments](medium/fb-live-comments.md)
- [FB Post Search](medium/fb-post-search.md)
- [Yelp — local search](medium/yelp-local-search.md)
- [Strava — activity tracking](medium/strava-activity-tracking.md)
- [Online auction (eBay)](medium/online-auction-ebay.md)
- [Price tracking (CamelCamelCamel)](medium/price-tracking-camelcamelcamel.md)
- [Notification system (APNs/FCM)](medium/notification-system-apns-fcm.md)
- [Search autocomplete (Google)](medium/search-autocomplete-google.md)
- [Unique ID generator (Snowflake)](medium/unique-id-generator-snowflake.md)
- [Hotel reservation (Booking.com)](medium/hotel-reservation-booking-com.md)
- [Gaming leaderboard](medium/gaming-leaderboard.md)
- [S3 object storage](medium/s3-object-storage.md)

## Hard (18)

- [Instagram — photo sharing](hard/instagram-photo-sharing.md)
- [YouTube Top K videos](hard/youtube-top-k-videos.md)
- [Uber — ride-sharing](hard/uber-ride-sharing.md)
- [Robinhood — stock trading](hard/robinhood-stock-trading.md)
- [Google Docs — collaborative editing](hard/google-docs-collaborative-editing.md)
- [Distributed cache (Redis-like)](hard/distributed-cache-redis-like.md)
- [YouTube — video platform](hard/youtube-video-platform.md)
- [Web crawler](hard/web-crawler.md)
- [Ad click aggregator](hard/ad-click-aggregator.md)
- [Job scheduler (Airflow)](hard/job-scheduler-airflow.md)
- [Payment system (Stripe)](hard/payment-system-stripe.md)
- [Metrics monitoring (Datadog)](hard/metrics-monitoring-datadog.md)
- [Message queue (Kafka)](hard/message-queue-kafka.md)
- [Distributed key-value store](hard/distributed-key-value-store.md)
- [Nearby friends](hard/nearby-friends.md)
- [Google Maps](hard/google-maps.md)
- [Distributed email (Gmail)](hard/distributed-email-gmail.md)
- [Digital wallet (Apple Pay)](hard/digital-wallet-apple-pay.md)
