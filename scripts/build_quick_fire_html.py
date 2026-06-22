#!/usr/bin/env python3
"""Build Notion-style colorful HTML from interview-quick-fire.md and enrich the MD with severity badges."""

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "cheatSheet" / "interview-quick-fire.md"
HTML_PATH = ROOT / "cheatSheet" / "interview-quick-fire.html"
DIAGRAMS_HTML_PATH = ROOT / "cheatSheet" / "interview-quick-fire-diagrams.html"
DIAGRAMS_INC_PATH = ROOT / "cheatSheet" / "quick-fire-diagrams.inc.html"

SEVERITY = {
    "critical": {
        "emoji": "🔴",
        "label": "Critical",
        "alert": "CAUTION",
        "hint": "Outage / data-loss risk — probe failure modes first",
        "css": "sev-critical",
    },
    "high": {
        "emoji": "🟠",
        "label": "High",
        "alert": "WARNING",
        "hint": "Resilience under stress — name degraded mode + recovery",
        "css": "sev-high",
    },
    "important": {
        "emoji": "🟣",
        "label": "Important",
        "alert": "IMPORTANT",
        "hint": "Correctness / invariants — strong consistency territory",
        "css": "sev-important",
    },
    "pattern": {
        "emoji": "🟢",
        "label": "Pattern",
        "alert": "TIP",
        "hint": "Core design pattern — pattern + trade-off + anchor",
        "css": "sev-pattern",
    },
    "prep": {
        "emoji": "🔵",
        "label": "Prep",
        "alert": "NOTE",
        "hint": "Interview framework — how to answer and go deeper",
        "css": "sev-prep",
    },
}

SECTION_SEV = {
    "Classic failure modes & distributed pitfalls": "critical",
    "Availability & resilience": "high",
    "Security & abuse": "high",
    "Consistency & correctness": "important",
    "Money & transactions": "important",
    "Writes & throughput": "pattern",
    "Reads & caching": "pattern",
    "Fan-out & real-time": "pattern",
    "Storage & media": "pattern",
    "Messaging & async": "pattern",
    "Geo & search": "pattern",
    "Observability & ops": "prep",
    "How to go deeper — interview prep": "prep",
    "Answer template (use every time)": "prep",
    "Visual archetypes": "prep",
    "Practice drill": "prep",
    "Quick decision shortcuts": "prep",
    "Navigation": "prep",
}

PATTERN_OVERRIDE = {
    "High write burst (flash sale)": "high",
    "Prevent double booking": "high",
    "Write contention (multi-seat reservation)": "high",
    "Cascading failure": "high",
    "DB primary fails": "high",
    "Metastable failure": "critical",
    "Split brain": "critical",
    "Dual-write problem": "critical",
    "Payment correctness": "critical",
    "Inventory / wallet balance": "critical",
    "Retry storm": "critical",
}

PROBLEM_STATEMENTS: dict[str, str] = {
    "Thundering herd": "What happens when your cache TTL expires and thousands of clients hit the database at once?",
    "Cache stampede (dogpile)": "An expensive cached computation expires — how do you stop every request from re-running it simultaneously?",
    "Retry storm": "Clients retry on timeout, the service slows down, and retries multiply — how do you break the loop?",
    "Metastable failure": "The system was stable at 70% load but collapses at 80% and cannot recover — what is happening?",
    "Hot partition / hot key": "One Redis key or DB partition gets 100× normal traffic — how do you handle it?",
    "Split brain": "Your DB primary fails over but the old primary still accepts writes — how do you prevent split brain?",
    "Poison message": "One bad queue message crashes every consumer — how do you isolate it without stopping the pipeline?",
    "Head-of-line blocking": "One slow message blocks the entire queue — how do you prevent head-of-line blocking?",
    "N+1 queries": "Your API runs one DB query per item in a list — how do you fix the N+1 problem?",
    "Connection pool exhaustion": "Under load your app runs out of database connections — what is going wrong?",
    "Replica lag / stale read": "A user updates data but immediately reads the old value from a replica — how do you handle lag?",
    "Slow node (straggler)": "One node in a scatter-gather query is 10× slower — how do you limit tail latency?",
    "Dual-write problem": "You write to the database and search index separately and they drift — how do you keep them in sync?",
    "Circular dependency / retry loop": "Service A calls B, B calls A, and retries create a loop — how do you break it?",
    "Handle traffic spikes": "Traffic spikes 10× during a flash event — how do you absorb it without downtime?",
    "Eliminate single point of failure": "Walk me through how you would remove single points of failure in this design.",
    "DB primary fails": "Your database primary goes down — what is your failover and recovery plan?",
    "Cascading failure": "One service failure takes down everything downstream — how do you stop cascading failures?",
    "Regional outage": "An entire cloud region goes offline — how does your system stay available?",
    "Zero-downtime deploy": "How do you deploy new code without taking the service offline?",
    "Reduce DB read load": "Reads are hammering your database — how do you reduce read load on the primary?",
    "Hot key / viral content": "A viral post makes one cache key receive millions of reads per second — what do you do?",
    "Stale cache after update": "Users see stale data after an update because the cache was not invalidated — how do you fix it?",
    "Reduce global read latency": "Users in Asia see 800ms latency reading from your US database — how do you reduce global latency?",
    "Pagination at scale": "OFFSET pagination gets slower as users page deeper — how do you paginate at scale?",
    "Search across billions of records": "How would you build full-text search across billions of documents?",
    "Autocomplete / typeahead": "Design autocomplete that returns suggestions within 50ms as the user types.",
    "Scale writes past single DB": "Write throughput exceeds what one database can handle — how do you scale writes?",
    "High write burst (flash sale)": "A flash sale creates a sudden 50× write spike — how do you handle it?",
    "Idempotent writes": "Network retries cause duplicate writes — how do you make writes idempotent?",
    "Prevent double booking": "Two users book the last hotel room at the same time — how do you prevent double booking?",
    "Write contention (multi-seat reservation)": "80,000 seats, 300K users hit Reserve at once — two fans book overlapping seats and you see ERROR: deadlock detected. How do you prevent double-booking and deadlocks at the database layer?",
    "Distributed counter": "You need a globally accurate view count across millions of servers — how do you implement it?",
    "Unique ID at scale": "You need unique IDs at 10,000 per millisecond — what approach do you use?",
    "Strong vs eventual consistency": "When would you choose strong consistency versus eventual consistency?",
    "Guarantee exactly-once": "How do you guarantee exactly-once processing in a distributed pipeline?",
    "Cross-service transaction": "Payment requires debiting one service and crediting another — how do you handle the transaction?",
    "Read-your-writes": "After a user posts, their feed does not show it — how do you guarantee read-your-writes?",
    "Payment correctness": "A payment timeout causes a client retry — how do you prevent double charging?",
    "Inventory / wallet balance": "How do you keep inventory or wallet balances correct under concurrent updates?",
    "Fan-out to millions of followers": "A user with 50M followers posts — how do you fan out to follower feeds?",
    "WebSocket at scale": "How do you scale WebSocket connections to millions of concurrent users?",
    "Push notifications at scale": "How do you deliver push notifications to 100M devices reliably?",
    "Decouple services": "Two services are tightly coupled and one outage takes down the other — how do you decouple them?",
    "Webhook delivery": "You must deliver webhooks to third parties with retries and idempotency — how do you design it?",
    "Store large files": "How do you store and serve large files (images, PDFs, backups) at scale?",
    "Video streaming": "Design video upload, transcoding, and streaming for YouTube-scale traffic.",
    "Rate limiting": "Design a rate limiter for your public API.",
    "DDoS / abuse": "Your API is being abused or DDoS'd — how do you protect it?",
    "Nearby search (Yelp, Uber)": "Find all restaurants or drivers within 5km of a user — how do you implement nearby search?",
    "Debug production incidents": "Production is degraded and the cause is unclear — walk me through your incident response.",
    "Cardinality explosion (metrics)": "Your metrics bill exploded because someone used user_id as a label — how do you prevent it?",
}

PATTERN_SECTIONS: list[tuple[str, list[str]]] = [
    (
        "Classic failure modes & distributed pitfalls",
        [
            "Thundering herd",
            "Cache stampede (dogpile)",
            "Retry storm",
            "Metastable failure",
            "Hot partition / hot key",
            "Split brain",
            "Poison message",
            "Head-of-line blocking",
            "N+1 queries",
            "Connection pool exhaustion",
            "Replica lag / stale read",
            "Slow node (straggler)",
            "Dual-write problem",
            "Circular dependency / retry loop",
        ],
    ),
    (
        "Availability & resilience",
        [
            "Handle traffic spikes",
            "Eliminate single point of failure",
            "DB primary fails",
            "Cascading failure",
            "Regional outage",
            "Zero-downtime deploy",
        ],
    ),
    (
        "Reads & caching",
        [
            "Reduce DB read load",
            "Hot key / viral content",
            "Stale cache after update",
            "Reduce global read latency",
            "Pagination at scale",
            "Search across billions of records",
            "Autocomplete / typeahead",
        ],
    ),
    (
        "Writes & throughput",
        [
            "Scale writes past single DB",
            "High write burst (flash sale)",
            "Idempotent writes",
            "Prevent double booking",
            "Write contention (multi-seat reservation)",
            "Distributed counter",
            "Unique ID at scale",
        ],
    ),
    (
        "Consistency & correctness",
        [
            "Strong vs eventual consistency",
            "Guarantee exactly-once",
            "Cross-service transaction",
            "Read-your-writes",
        ],
    ),
    (
        "Money & transactions",
        [
            "Payment correctness",
            "Inventory / wallet balance",
        ],
    ),
    (
        "Fan-out & real-time",
        [
            "Fan-out to millions of followers",
            "WebSocket at scale",
            "Push notifications at scale",
        ],
    ),
    (
        "Messaging & async",
        [
            "Decouple services",
            "Webhook delivery",
        ],
    ),
    (
        "Storage & media",
        [
            "Store large files",
            "Video streaming",
        ],
    ),
    (
        "Security & abuse",
        [
            "Rate limiting",
            "DDoS / abuse",
        ],
    ),
    (
        "Geo & search",
        [
            "Nearby search (Yelp, Uber)",
        ],
    ),
    (
        "Observability & ops",
        [
            "Debug production incidents",
            "Cardinality explosion (metrics)",
        ],
    ),
    (
        "Practice drill",
        [
            "Level 1 — Quick-fire (30s each)",
            "Level 2 — Deep dive (3 min each)",
            "Level 3 — Interruption drill",
        ],
    ),
]

SECTION_ORDER = [name for name, _ in PATTERN_SECTIONS]

SECTION_BANNERS = {
    sev_key: (
        f"\n> [!{SEVERITY[sev_key]['alert']}]\n"
        f"> **{SEVERITY[sev_key]['emoji']} {SEVERITY[sev_key]['label']}** — {SEVERITY[sev_key]['hint']}\n\n"
    )
    for sev_key in SEVERITY
}


def _pattern_block_title(block: str):
    m = re.match(r"### (?:[🔴🟠🟣🟢🔵] )?(.+)", block.strip())
    return m.group(1).strip() if m else None


def reorganize_pattern_sections(md: str) -> str:
    """Split collapsed pattern blob into topical ## sections (idempotent)."""
    marker = "## Classic failure modes & distributed pitfalls"
    if marker not in md:
        return md

    # Already split if a second pattern section exists after classic failures.
    tail = md.split(marker, 1)[1]
    if re.search(r"\n## (?:Reads & caching|Availability & resilience|Writes & throughput)\b", tail):
        return md

    footer_m = re.search(r"\n\*Eddy Hung", md)
    if not footer_m:
        return md

    before = md[: md.index(marker)]
    region = md[md.index(marker) : footer_m.start()]
    after = md[footer_m.start() :]

    blocks = re.split(r"\n(?=### )", region.strip())
    by_title: dict[str, str] = {}
    for block in blocks[1:]:
        title = _pattern_block_title(block)
        if title:
            by_title[title] = block.strip()

    out = before.rstrip() + "\n\n"
    missing: list[str] = []
    for sec_name, titles in PATTERN_SECTIONS:
        sev_key = SECTION_SEV.get(sec_name, "prep")
        out += f"## {sec_name}\n{SECTION_BANNERS[sev_key]}"
        for title in titles:
            block = by_title.pop(title, None)
            if block:
                out += block + "\n\n"
            else:
                missing.append(f"{sec_name}: {title}")

    if by_title:
        out += "## Uncategorized\n\n"
        for block in by_title.values():
            out += block + "\n\n"

    if missing:
        print("Warning: missing pattern blocks:", ", ".join(missing))

    return out + after.lstrip()


def parse_java_blocks(rest: str) -> list[dict]:
    blocks = []
    for m in re.finditer(r"```java\n(.*?)```", rest, re.S):
        code = m.group(1).strip("\n")
        title = ""
        lines = code.split("\n")
        if lines and lines[0].startswith("//"):
            title = lines[0][2:].strip()
            code = "\n".join(lines[1:]).strip("\n")
        blocks.append({"title": title, "code": code})
    return blocks


def render_java_html(blocks: list[dict]) -> str:
    if not blocks:
        return ""
    parts = ['<div class="qf-java-wrap">']
    for b in blocks:
        if b["title"]:
            parts.append(f'<div class="qf-java-label">{html.escape(b["title"])}</div>')
        parts.append(f'<pre class="qf-java"><code>{html.escape(b["code"])}</code></pre>')
    parts.append("</div>")
    return "".join(parts)


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def parse_patterns(body: str) -> list[dict]:
    parts = re.split(r"\n### ", body)
    patterns = []
    for part in parts[1:]:
        lines = part.strip().split("\n")
        title = lines[0].strip()
        title = re.sub(r"^[🔴🟠🟣🟢🔵]\s*", "", title)
        title = re.sub(r"^Diagram ·\s*", "Diagram · ", title)  # keep diagram titles distinct
        rest = "\n".join(lines[1:])
        weak = staff = staff_plus = trade = example = visual = problem = ""
        m = re.search(
            r"\*\*(?:💬 )?Problem:\*\*\s*(.+?)(?=\n> \[!|\n\*\*🔴|\n\*\*Trade|\n📊|\n---|\Z)",
            rest,
            re.S,
        )
        if m:
            problem = re.sub(r"\n> ?", " ", m.group(1)).strip()
        m = re.search(r"\*\*🔴 Weak\*\* —\s*(.+?)(?=\n> \[!|\n\*\*Trade|\n📊|\n---|\Z)", rest, re.S)
        if m:
            weak = re.sub(r"\n> ?", " ", m.group(1)).strip()
        m = re.search(
            r"\*\*🟡 Strong\*\* —\s*(.+?)(?=\n> \[!|\n\*\*Trade|\n📊|\n---|\Z)",
            rest,
            re.S,
        )
        if m:
            staff = re.sub(r"\n> ?", " ", m.group(1)).strip()
        if not staff:
            m = re.search(
                r"(?:^|\n)>?\s*\*\*Staff-level answer:\*\*\s*(.+?)(?=\n>?\s*\*\*Trade-offs|\n\n📊|\n---|\n### |\Z)",
                rest,
                re.S,
            )
            if m:
                staff = re.sub(r"\n> ?", " ", m.group(1)).strip()
        m = re.search(
            r"\*\*🟢 Staff\+\*\* —\s*(.+?)(?=\n\*\*Trade|\n📊|\n---|\Z)",
            rest,
            re.S,
        )
        if m:
            staff_plus = re.sub(r"\n> ?", " ", m.group(1)).strip()
        else:
            staff_plus = ""
        m = re.search(
            r"(?:^|\n)>?\s*\*\*Trade-offs:\*\*\s*(.+?)(?=\n>?\s*\*\*Example|\n\n📊|\n---|\n### |\Z)",
            rest,
            re.S,
        )
        if m:
            trade = re.sub(r"\n> ?", " ", m.group(1)).strip()
        m = re.search(
            r"(?:^|\n)>?\s*\*\*Example:\*\*\s*(.+?)(?=\n\n📊|\n---|\n### |\Z)",
            rest,
            re.S,
        )
        if m:
            example = re.sub(r"\n> ?", " ", m.group(1)).strip()
        m = re.search(r"📊 \*\*Visual:\*\*\s*(.+)", rest)
        if m:
            visual = m.group(1).strip()
        java_blocks = parse_java_blocks(rest)
        if not staff or title.startswith("Diagram ·") or title.startswith("Pattern →"):
            continue
        if not problem:
            problem = PROBLEM_STATEMENTS.get(
                title, f"How would you handle {title.lower()} in a large-scale system?"
            )
        patterns.append(
            {
                "title": title,
                "slug": slugify(title),
                "problem": problem,
                "weak": weak,
                "staff": staff,
                "staff_plus": staff_plus,
                "trade": trade,
                "example": example,
                "visual": visual,
                "java_blocks": java_blocks,
            }
        )
    return patterns


def parse_sections(md: str) -> list[dict]:
    md = md.split("\n", 1)[1] if md.startswith("# ") else md
    intro = ""
    if "## Navigation" in md:
        intro, md = md.split("## Navigation", 1)
        md = "## Navigation" + md

    chunks = re.split(r"\n(?=## )", md)
    sections = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("## "):
            continue
        first_nl = chunk.find("\n")
        title = chunk[3:first_nl].strip() if first_nl != -1 else chunk[3:].strip()
        body = chunk[first_nl + 1 :] if first_nl != -1 else ""
        sev_key = SECTION_SEV.get(title, "prep")
        patterns = parse_patterns(body) if title not in ("Navigation",) else []
        for p in patterns:
            p["severity"] = PATTERN_OVERRIDE.get(p["title"], sev_key)
        sections.append(
            {
                "title": title,
                "slug": slugify(title),
                "severity": sev_key,
                "body": body,
                "patterns": patterns,
            }
        )
    return intro.strip(), sections


def md_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def render_md_table(block: str) -> str:
    rows: list[list[str]] = []
    for line in block.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return f"<p>{md_inline(block)}</p>"
    head, *body = rows
    h = "<table><thead><tr>" + "".join(f"<th>{md_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
    for row in body:
        h += "<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in row) + "</tr>"
    return h + "</tbody></table>"


CALLOUT_CSS = {
    "NOTE": "prep",
    "TIP": "pattern",
    "WARNING": "high",
    "CAUTION": "critical",
    "IMPORTANT": "important",
}


def md_blocks(text: str) -> str:
    if not text.strip():
        return ""
    out: list[str] = []
    for block in re.split(r"\n\n+", text.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            out.append(f"<h2>{md_inline(block[3:].strip())}</h2>")
        elif block.startswith("### "):
            out.append(f"<h3>{md_inline(block[4:].strip())}</h3>")
        elif block.startswith("|"):
            out.append(render_md_table(block))
        elif block.startswith(">"):
            alert = "NOTE"
            content_lines: list[str] = []
            for line in block.split("\n"):
                line = line.lstrip("> ").strip()
                m = re.match(r"\[!(NOTE|TIP|WARNING|CAUTION|IMPORTANT)\]", line)
                if m:
                    alert = m.group(1)
                    continue
                if line:
                    content_lines.append(line)
            css = CALLOUT_CSS.get(alert, "prep")
            content = md_inline(" ".join(content_lines))
            out.append(f'<div class="callout {css}"><strong>{alert}</strong>{content}</div>')
        elif re.match(r"^[-*] ", block):
            items = [
                md_inline(line[2:].strip())
                for line in block.split("\n")
                if re.match(r"^[-*] ", line)
            ]
            out.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
        else:
            out.append(f"<p>{md_inline(block.replace(chr(10), ' '))}</p>")
    return "\n".join(out)


def split_intro(intro: str) -> str:
    """Opening paragraphs only — preamble ## sections stay in the .md source."""
    intro = intro.strip()
    m = re.search(r"\n## ", intro)
    return intro[: m.start()].strip() if m else intro


def parse_page_title(md: str) -> tuple[str, str]:
    m = re.match(r"#\s+(.+?)(?:\s*—\s*(.+))?\s*\n", md)
    if not m:
        return "Interview quick-fire", ""
    return m.group(1).strip(), (m.group(2) or "").strip()


LINK_LABELS = {
    "system_design_cheatsheet_v14.html": "Full cheatsheet",
    "github/v15/index.html": "40 system cards",
    "github/v15/index.md": "40 system cards",
}

DIAGRAM_LINK_RE = re.compile(
    r"\[([^\]]+)\]\((?:interview-quick-fire-diagrams|interview-quick-fire)\.html#?([^)]*)\)"
)


def rewrite_visual_html(visual: str) -> str:
    if not visual:
        return ""

    out: list[str] = []
    last = 0
    for m in DIAGRAM_LINK_RE.finditer(visual):
        if m.start() > last:
            out.append(md_inline(visual[last : m.start()]))
        label = md_inline(m.group(1))
        did = m.group(2).strip() or m.group(1).lower().replace(" ", "-")
        if did == "diagrams":
            did = ""
        href = f"#{html.escape(did, quote=True)}" if did else "#diagrams"
        data_diag = (
            f' data-diag="{html.escape(did, quote=True)}"' if did else ' data-diag="diagrams"'
        )
        out.append(f'<a href="{href}" class="diag-link"{data_diag}>{label}</a>')
        last = m.end()
    if last < len(visual):
        out.append(md_inline(visual[last:]))
    return "".join(out)


def rewrite_md_diagram_links(md: str) -> str:
    return md.replace(
        "interview-quick-fire-diagrams.html#",
        "interview-quick-fire.html#",
    ).replace(
        "interview-quick-fire-diagrams.html)",
        "interview-quick-fire.html#diagrams)",
    )


def extract_diagram_ids(inc: str) -> list[str]:
    return re.findall(r"^\s+id: '([^']+)'", inc, re.M)


def parse_diagram_inc(text: str) -> tuple[str, str, str]:
    css_m = re.search(r"<style id=\"diag-inc-css\">(.*?)</style>", text, re.S)
    html_m = re.search(r"</style>\s*(.*?)\s*<script id=\"diag-inc-js\">", text, re.S)
    js_m = re.search(r"<script id=\"diag-inc-js\">(.*?)</script>", text, re.S)
    return (
        css_m.group(1) if css_m else "",
        html_m.group(1).strip() if html_m else "",
        js_m.group(1) if js_m else "",
    )


def build_diagram_redirect() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url=interview-quick-fire.html">
<title>Redirecting…</title>
<script>location.replace('interview-quick-fire.html'+location.hash);</script>
</head>
<body><p>Moved to <a href="interview-quick-fire.html">interview-quick-fire.html</a>.</p></body>
</html>"""


def render_hero(lead_md: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\n+", lead_md.strip()) if p.strip()]
    parts: list[str] = []
    for para in paras:
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", para)
        if len(links) >= 2:
            pills = []
            for label, href in links:
                if href == "interview-quick-fire.html":
                    continue
                if href == "github/v15/index.md":
                    href = "github/v15/index.html"
                text = LINK_LABELS.get(href, label)
                pills.append(
                    f'<a href="{html.escape(href, quote=True)}">{md_inline(text)}</a>'
                )
            if pills:
                parts.append('<div class="hero-links">' + "".join(pills) + "</div>")
            continue
        parts.append(f"<p>{md_inline(para.replace(chr(10), ' '))}</p>")
    return "".join(parts)


def enrich_markdown(md: str, sections: list[dict]) -> str:
    legend = """
## Severity legend

| Badge | Level | When interviewers probe here |
|-------|-------|------------------------------|
| 🔴 **Critical** | Outage / cascade / data loss | Failure modes, "what if X dies?", metastable |
| 🟠 **High** | Resilience under stress | Availability, security, flash-sale contention |
| 🟣 **Important** | Correctness & invariants | Consistency tiers, money, inventory |
| 🟢 **Pattern** | Standard staff answer | Reads, writes, fan-out, storage flows |
| 🔵 **Prep** | Framework & drill | Answer template, DMOP, practice |

> [!NOTE]
> **Colorful view:** open [interview-quick-fire.html](interview-quick-fire.html) for Notion-style callouts, filters, and severity sidebar.

"""

    if "## Severity legend" in md:
        md = re.sub(r"\n## Severity legend\n.*?(?=\n## Navigation)", "\n" + legend, md, flags=re.S)
    else:
        md = md.replace(
            "\n## Navigation",
            legend + "\n## Navigation",
            1,
        )

    for sec in sections:
        if not sec["patterns"]:
            continue
        sev = SEVERITY[sec["severity"]]
        banner = (
            f"\n> [!{sev['alert']}]\n"
            f"> **{sev['emoji']} {sev['label']}** — {sev['hint']}\n\n"
        )
        marker = f"## {sec['title']}"
        if banner.strip() not in md and f"## {sec['title']}\n\n> [!{sev['alert']}]" not in md:
            md = md.replace(f"## {sec['title']}\n", f"## {sec['title']}\n{banner}", 1)

        for p in sec["patterns"]:
            if p["title"].startswith("Diagram ·"):
                continue
            sev_p = SEVERITY[p["severity"]]
            md = md.replace(f"### {sev_p['emoji']} {p['title']}", f"### {p['title']}", 1)  # normalize
            if f"### {sev_p['emoji']} {p['title']}\n" not in md:
                md = md.replace(f"### {p['title']}\n", f"### {sev_p['emoji']} {p['title']}\n", 1)

            prob = p.get("problem", "")
            header = f"### {sev_p['emoji']} {p['title']}\n"
            if prob and header in md and "**💬 Problem:**" not in md.split(header, 1)[1].split("\n### ", 1)[0]:
                md = md.replace(header, f"{header}\n> **💬 Problem:** {prob}\n\n", 1)

            if not p["staff"]:
                continue
            if f"**🔴 Weak** —" in md and f"### {sev_p['emoji']} {p['title']}" in md:
                continue
            if f"> [!{sev_p['alert']}]\n> **Staff-level answer:** {p['staff'][:40]}" in md:
                continue
            card = (
                f"\n> [!{sev_p['alert']}]\n"
                f"> **Staff-level answer:** {p['staff']}\n>\n"
                f"> **Trade-offs:** {p['trade']}\n>\n"
                f"> **Example:** {p['example']}\n"
            )
            if p["visual"]:
                card += f"\n📊 **Visual:** {p['visual']}\n"

            block_re = re.compile(
                rf"### {re.escape(sev_p['emoji'])} {re.escape(p['title'])}\n\n"
                rf"(?:\*\*Staff-level answer:\*\*.*?(?=\n---|\n### |\Z))",
                re.S,
            )
            md = block_re.sub(f"### {sev_p['emoji']} {p['title']}\n{card}\n", md, count=1)

    if "interview-quick-fire.html" not in md.split("## Navigation")[0]:
        md = md.replace(
            "interview-quick-fire-diagrams.html)",
            "interview-quick-fire.html#diagrams)",
            1,
        )

    nav_colorful = "- [Colorful HTML view](interview-quick-fire.html) — Notion-style severity callouts\n"
    if nav_colorful not in md:
        md = md.replace("## Navigation\n\n", f"## Navigation\n\n{nav_colorful}", 1)

    return rewrite_md_diagram_links(md)


def build_html(intro: str, sections: list[dict], md: str = "") -> str:
    diag_inc = load_diagram_inc() if DIAGRAMS_INC_PATH.exists() else ""
    diag_css, diag_html, diag_js = parse_diagram_inc(diag_inc) if diag_inc else ("", "", "")
    diagram_ids = extract_diagram_ids(diag_inc) if diag_inc else []
    diagram_ids_json = json.dumps(diagram_ids, ensure_ascii=False)

    data = []
    for sec in sections:
        if sec["title"] == "Navigation":
            continue
        data.append(
            {
                "title": sec["title"],
                "slug": sec["slug"],
                "severity": sec["severity"],
                "patterns": [
                    {
                        **p,
                        "problem_html": md_inline(p.get("problem", "")),
                        "weak_html": md_inline(p.get("weak", "")),
                        "staff_html": md_inline(p["staff"]),
                        "staff_plus_html": md_inline(p.get("staff_plus", "")),
                        "trade_html": md_inline(p["trade"]),
                        "example_html": md_inline(p["example"]),
                        "visual_html": rewrite_visual_html(p["visual"]),
                        "java_html": render_java_html(p.get("java_blocks", [])),
                        "java": "\n".join(b["code"] for b in p.get("java_blocks", [])),
                    }
                    for p in sec["patterns"]
                ],
            }
        )

    order = {name: i for i, name in enumerate(SECTION_ORDER)}
    data.sort(key=lambda s: order.get(s["title"], 999))

    payload = json.dumps(data, ensure_ascii=False)
    page_title, page_sub = parse_page_title(md)
    if page_sub:
        page_sub = page_sub[0].upper() + page_sub[1:]
    hero_html = render_hero(split_intro(intro))
    hero_fallback = (
        "<p>Problem → staff-level answer. Filter by severity — drill critical failure modes first.</p>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Interview Quick-Fire — Patterns &amp; Diagrams</title>
<meta name="description" content="System design quick-fire — severity-coded patterns plus 17 interactive Mermaid diagrams, offline.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23185fa5'/><text x='16' y='22' text-anchor='middle' fill='white' font-size='14' font-family='sans-serif' font-weight='700'>SD</text></svg>">
<style>
:root{{
  --bg:#f7f6f3;--card:#fff;--text:#37352f;--muted:#787774;
  --critical-bg:#fdebec;--critical-bdr:#e16259;--critical-txt:#7f1d1d;
  --high-bg:#fbf3db;--high-bdr:#d9a006;--high-txt:#713f12;
  --important-bg:#f3e8ff;--important-bdr:#9065b0;--important-txt:#581c87;
  --pattern-bg:#edf3ec;--pattern-bdr:#448361;--pattern-txt:#1a3d2a;
  --prep-bg:#e7f3f8;--prep-bdr:#337ea9;--prep-txt:#0c4a6e;
  --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
  --r:10px;
}}
html[data-theme="dark"]{{
  --bg:#191919;--card:#252525;--text:#e3e2de;--muted:#9b9a97;
  --critical-bg:#3d1f1f;--critical-bdr:#e16259;--critical-txt:#fecaca;
  --high-bg:#3d3018;--high-bdr:#d9a006;--high-txt:#fde68a;
  --important-bg:#2e1f3d;--important-bdr:#9065b0;--important-txt:#e9d5ff;
  --pattern-bg:#1f2e22;--pattern-bdr:#448361;--pattern-txt:#bbf7d0;
  --prep-bg:#1a2a33;--prep-bdr:#337ea9;--prep-txt:#bae6fd;
}}
@media(prefers-color-scheme:dark){{
  html:not([data-theme="light"]){{
    --bg:#191919;--card:#252525;--text:#e3e2de;--muted:#9b9a97;
    --critical-bg:#3d1f1f;--critical-bdr:#e16259;--critical-txt:#fecaca;
    --high-bg:#3d3018;--high-bdr:#d9a006;--high-txt:#fde68a;
    --important-bg:#2e1f3d;--important-bdr:#9065b0;--important-txt:#e9d5ff;
    --pattern-bg:#1f2e22;--pattern-bdr:#448361;--pattern-txt:#bbf7d0;
    --prep-bg:#1a2a33;--prep-bdr:#337ea9;--prep-txt:#bae6fd;
  }}
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.55}}
a{{color:var(--prep-bdr)}}
.app{{display:flex;min-height:100vh}}
.content-area{{flex:1;min-width:0;display:flex;flex-direction:column}}
.view-shell{{display:none;flex:1;min-height:0}}
.view-shell.view-active{{display:block}}
.view-diagrams.view-active{{display:flex;flex-direction:column}}
.view-diagrams.view-active .diag-app{{height:100vh}}
.sidebar{{width:280px;background:var(--card);border-right:1px solid rgba(0,0,0,.08);padding:16px 12px;position:sticky;top:0;height:100vh;overflow-y:auto;flex-shrink:0}}
.view-tabs{{display:flex;gap:6px;margin-bottom:14px}}
.view-tabs .vtab{{flex:1;font-size:.78rem;font-weight:600;padding:7px 10px;border-radius:8px;border:1px solid rgba(0,0,0,.1);background:var(--bg);color:var(--muted);cursor:pointer}}
.view-tabs .vtab.on{{background:var(--prep-bg);border-color:var(--prep-bdr);color:var(--prep-txt)}}
.main{{flex:1;max-width:920px;padding:28px 32px 80px}}
.diag-link{{font-weight:500}}
h1{{font-size:1.75rem;margin-bottom:8px;letter-spacing:-.02em}}
.hero-sub{{color:var(--muted);font-size:1rem;margin:-2px 0 14px}}
.lead p{{color:var(--muted);margin-bottom:12px;font-size:.95rem;line-height:1.6}}
.hero-links{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}}
.hero-links a{{font-size:.82rem;padding:5px 12px;border-radius:100px;border:1px solid rgba(0,0,0,.1);background:var(--card);text-decoration:none;color:var(--text);font-weight:500}}
.hero-links a:hover{{border-color:var(--prep-bdr);color:var(--prep-bdr)}}
.legend{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:20px 0 28px}}
.leg{{padding:10px 12px;border-radius:var(--r);border-left:4px solid;font-size:.8rem;font-weight:600}}
.leg small{{display:block;font-weight:400;color:var(--muted);margin-top:2px;font-size:.72rem}}
.leg.critical{{background:var(--critical-bg);border-color:var(--critical-bdr);color:var(--critical-txt)}}
.leg.high{{background:var(--high-bg);border-color:var(--high-bdr);color:var(--high-txt)}}
.leg.important{{background:var(--important-bg);border-color:var(--important-bdr);color:var(--important-txt)}}
.leg.pattern{{background:var(--pattern-bg);border-color:var(--pattern-bdr);color:var(--pattern-txt)}}
.leg.prep{{background:var(--prep-bg);border-color:var(--prep-bdr);color:var(--prep-txt)}}
.toolbar{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;align-items:center}}
.toolbar input{{flex:1;min-width:180px;padding:8px 12px;border-radius:8px;border:1px solid rgba(0,0,0,.12);background:var(--card);color:var(--text)}}
.fchip{{font-size:.75rem;padding:5px 12px;border-radius:100px;border:1px solid rgba(0,0,0,.1);background:var(--card);cursor:pointer}}
.fchip.on{{font-weight:600}}
.fchip.critical.on{{background:var(--critical-bg);border-color:var(--critical-bdr);color:var(--critical-txt)}}
.fchip.high.on{{background:var(--high-bg);border-color:var(--high-bdr);color:var(--high-txt)}}
.fchip.important.on{{background:var(--important-bg);border-color:var(--important-bdr);color:var(--important-txt)}}
.fchip.pattern.on{{background:var(--pattern-bg);border-color:var(--pattern-bdr);color:var(--pattern-txt)}}
.fchip.prep.on{{background:var(--prep-bg);border-color:var(--prep-bdr);color:var(--prep-txt)}}
.tb{{font-size:.8rem;padding:6px 12px;border-radius:8px;border:1px solid rgba(0,0,0,.1);background:var(--card);cursor:pointer;color:var(--muted)}}
.sec{{margin-bottom:36px}}
.sec-hdr{{display:flex;align-items:center;gap:10px;margin-bottom:14px;padding:12px 16px;border-radius:var(--r);font-size:1.05rem;font-weight:700}}
.sec-hdr.critical{{background:var(--critical-bg);color:var(--critical-txt);border:1px solid var(--critical-bdr)}}
.sec-hdr.high{{background:var(--high-bg);color:var(--high-txt);border:1px solid var(--high-bdr)}}
.sec-hdr.important{{background:var(--important-bg);color:var(--important-txt);border:1px solid var(--important-bdr)}}
.sec-hdr.pattern{{background:var(--pattern-bg);color:var(--pattern-txt);border:1px solid var(--pattern-bdr)}}
.sec-hdr.prep{{background:var(--prep-bg);color:var(--prep-txt);border:1px solid var(--prep-bdr)}}
.card{{background:var(--card);border-radius:var(--r);margin-bottom:12px;overflow:hidden;border:1px solid rgba(0,0,0,.06);box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.card-hdr{{display:flex;align-items:center;gap:10px;padding:14px 16px;cursor:pointer;user-select:none}}
.card-hdr:hover{{background:rgba(0,0,0,.02)}}
.badge{{font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:6px;white-space:nowrap}}
.badge.critical{{background:var(--critical-bg);color:var(--critical-txt);border:1px solid var(--critical-bdr)}}
.badge.high{{background:var(--high-bg);color:var(--high-txt);border:1px solid var(--high-bdr)}}
.badge.important{{background:var(--important-bg);color:var(--important-txt);border:1px solid var(--important-bdr)}}
.badge.pattern{{background:var(--pattern-bg);color:var(--pattern-txt);border:1px solid var(--pattern-bdr)}}
.badge.prep{{background:var(--prep-bg);color:var(--prep-txt);border:1px solid var(--prep-bdr)}}
.card-title{{font-weight:600;font-size:.95rem;flex:1}}
.card-chev{{color:var(--muted);transition:transform .15s}}
.card.open .card-chev{{transform:rotate(90deg)}}
.card-body{{display:none;border-top:1px solid rgba(0,0,0,.06)}}
.card.open .card-body{{display:block}}
.callout{{margin:12px 16px;padding:12px 14px;border-radius:8px;border-left:4px solid;font-size:.88rem;line-height:1.65}}
.callout strong{{display:block;margin-bottom:4px;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;opacity:.85}}
.callout.critical{{background:var(--critical-bg);border-color:var(--critical-bdr)}}
.callout.high{{background:var(--high-bg);border-color:var(--high-bdr)}}
.callout.important{{background:var(--important-bg);border-color:var(--important-bdr)}}
.callout.pattern{{background:var(--pattern-bg);border-color:var(--pattern-bdr)}}
.callout.prep{{background:var(--prep-bg);border-color:var(--prep-bdr)}}
.callout.problem{{background:var(--prep-bg);border-color:var(--prep-bdr);font-style:italic}}
.qf-java-wrap{{margin:4px 16px 14px}}
.qf-java-label{{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--prep-bdr);margin:14px 0 6px}}
.qf-java-wrap .qf-java-label:first-child{{margin-top:0}}
.qf-java{{font-family:var(--mono);font-size:.72rem;line-height:1.55;background:rgba(0,0,0,.06);border:1px solid rgba(0,0,0,.08);padding:12px 14px;margin:0 0 10px;border-radius:8px;overflow-x:auto;white-space:pre;color:var(--text);tab-size:4}}
.qf-java:last-child{{margin-bottom:0}}
.qf-java code{{font-family:inherit;font-size:inherit;background:none;padding:0;border-radius:0;display:block}}
html[data-theme="dark"] .qf-java{{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.1)}}
.visual{{margin:0 16px 14px;font-size:.82rem;color:var(--muted)}}
.visual a{{font-weight:500}}
.sb-link{{display:block;padding:5px 10px;font-size:.8rem;color:var(--muted);text-decoration:none;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sb-link:hover{{background:rgba(0,0,0,.04);color:var(--text)}}
.sb-group{{margin-bottom:6px}}
.sb-sec-link{{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);padding:10px 8px 4px;text-decoration:none;border-radius:6px;cursor:pointer}}
.sb-sec-link:hover{{background:rgba(0,0,0,.04);color:var(--text)}}
.sb-count{{font-size:.62rem;font-weight:600;padding:1px 6px;border-radius:100px;background:rgba(0,0,0,.06);color:var(--muted);flex-shrink:0}}
.sb-dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.links{{margin-top:16px;font-size:.85rem}}
.links a{{margin-right:12px}}
code{{font-family:var(--mono);font-size:.85em;background:rgba(0,0,0,.06);padding:1px 5px;border-radius:4px}}
@media(max-width:768px){{
  .app{{display:block}}
  .sidebar{{position:relative;height:auto;width:100%;border-right:none;border-bottom:1px solid rgba(0,0,0,.08)}}
  .main{{padding:20px 16px}}
  .view-diagrams.view-active .diag-app{{height:auto;min-height:calc(100vh - 0px)}}
}}
</style>
<style id="diag-inc-css">{diag_css}</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div style="font-weight:700;font-size:.9rem;margin-bottom:4px">Quick-fire</div>
    <div class="view-tabs">
      <button class="vtab on" type="button" data-view="patterns">Patterns</button>
      <button class="vtab" type="button" data-view="diagrams">Diagrams</button>
    </div>
    <div id="sb-patterns-tools">
      <div style="font-size:.75rem;color:var(--muted);margin-bottom:12px">Browse by topic</div>
      <div id="sb-nav"></div>
    </div>
    <div class="links">
      <a href="interview-quick-fire.md">Markdown</a>
      <a href="index.html">Index</a>
    </div>
  </aside>
  <div class="content-area">
  <div id="view-patterns" class="view-shell view-active">
  <main class="main">
    <h1>{html.escape(page_title)}</h1>
    {f'<p class="hero-sub">{md_inline(page_sub)}</p>' if page_sub else ''}
    <div class="lead">{hero_html or hero_fallback}</div>
    <div class="legend">
      <div class="leg critical">🔴 Critical<small>Outage / cascade</small></div>
      <div class="leg high">🟠 High<small>Resilience stress</small></div>
      <div class="leg important">🟣 Important<small>Correctness / money</small></div>
      <div class="leg pattern">🟢 Pattern<small>Standard flows</small></div>
      <div class="leg prep">🔵 Prep<small>Framework & drill</small></div>
    </div>
    <div class="toolbar">
      <input type="search" id="q" placeholder="Search patterns…" autocomplete="off">
      <button class="fchip critical" data-f="critical" type="button">🔴 Critical</button>
      <button class="fchip high" data-f="high" type="button">🟠 High</button>
      <button class="fchip important" data-f="important" type="button">🟣 Important</button>
      <button class="fchip pattern" data-f="pattern" type="button">🟢 Pattern</button>
      <button class="fchip prep on" data-f="prep" type="button">🔵 Prep</button>
      <button class="fchip on" data-f="all" type="button">All</button>
      <button class="tb" id="theme" type="button">◐ Theme</button>
      <button class="tb" id="expand" type="button">Expand all</button>
    </div>
    <div id="root"></div>
  </main>
  </div>
  {diag_html}
  </div>
</div>
<script src="vendor/mermaid.min.js"></script>
<script id="diag-inc-js">
{diag_js}
</script>
<script>
const SEV = {json.dumps(SEVERITY, ensure_ascii=False)};
const DATA = {payload};
const DIAGRAM_IDS = new Set({diagram_ids_json});
let currentView = 'patterns';

function isDiagramHash(hash) {{
  const id = (hash || '').replace(/^#/, '');
  return id === 'diagrams' || DIAGRAM_IDS.has(id);
}}

function setView(view, opts = {{}}) {{
  currentView = view;
  document.getElementById('view-patterns')?.classList.toggle('view-active', view === 'patterns');
  document.getElementById('view-diagrams')?.classList.toggle('view-active', view === 'diagrams');
  document.querySelectorAll('.view-tabs .vtab').forEach(b => {{
    b.classList.toggle('on', b.dataset.view === view);
  }});
  const tools = document.getElementById('sb-patterns-tools');
  if (tools) tools.style.display = view === 'patterns' ? '' : 'none';
  if (view === 'diagrams' && typeof bootDiagrams === 'function') {{
    let diagId = opts.diagId;
    if (diagId === 'diagrams') diagId = null;
    if (!diagId && isDiagramHash(location.hash)) {{
      const h = location.hash.replace(/^#/, '');
      diagId = h === 'diagrams' ? null : h;
    }}
    bootDiagrams(diagId || null);
  }}
}}

function routeHash() {{
  if (isDiagramHash(location.hash)) {{
    const id = location.hash.replace(/^#/, '');
    setView('diagrams', {{ diagId: id }});
    return;
  }}
  setView('patterns');
  if (location.hash) {{
    setTimeout(() => {{
      const el = document.querySelector(location.hash);
      if (el) {{
        el.scrollIntoView({{ behavior: 'smooth' }});
        el.classList?.add('open');
      }}
    }}, 120);
  }}
}}

document.querySelectorAll('.view-tabs .vtab').forEach(b => {{
  b.onclick = () => {{
    if (b.dataset.view === 'diagrams') {{
      location.hash = 'diagrams';
    }} else {{
      if (location.hash) history.replaceState(null, '', location.pathname + location.search);
      setView('patterns');
    }}
  }};
}});

document.addEventListener('click', e => {{
  const a = e.target.closest('a.diag-link');
  if (!a) return;
  e.preventDefault();
  const id = a.dataset.diag || (a.getAttribute('href') || '').replace(/^#/, '');
  if (id) location.hash = id;
}});

window.addEventListener('hashchange', routeHash);

function render() {{
  const root = document.getElementById('root');
  const sb = document.getElementById('sb-nav');
  const q = (document.getElementById('q').value || '').toLowerCase();
  const active = [...document.querySelectorAll('.fchip.on')].map(b => b.dataset.f);
  const showAll = active.includes('all') || active.length === 0;
  root.innerHTML = '';
  sb.innerHTML = '';
  DATA.forEach(sec => {{
    const patterns = sec.patterns.filter(p => {{
      if (!showAll && !active.includes(p.severity)) return false;
      const hay = (p.title + ' ' + (p.problem||'') + ' ' + (p.weak||'') + ' ' + p.staff + ' ' + p.trade + ' ' + (p.java||'')).toLowerCase();
      return !q || hay.includes(q);
    }});
    if (!patterns.length) return;
    const s = SEV[sec.severity] || SEV.prep;
    const secEl = document.createElement('section');
    secEl.className = 'sec';
    secEl.id = sec.slug;
    secEl.innerHTML = `<div class="sec-hdr ${{sec.severity}}">${{s.emoji}} ${{sec.title}}</div>`;
    const sbSec = document.createElement('div');
    sbSec.className = 'sb-group';
    const secLink = document.createElement('a');
    secLink.className = 'sb-sec-link';
    secLink.href = '#' + sec.slug;
    secLink.innerHTML = `<span>${{s.emoji}} ${{sec.title}}</span><span class="sb-count">${{patterns.length}}</span>`;
    secLink.onclick = e => {{
      e.preventDefault();
      document.getElementById(sec.slug)?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }};
    sbSec.appendChild(secLink);
    patterns.forEach(p => {{
      const ps = SEV[p.severity] || SEV.pattern;
      const card = document.createElement('div');
      card.className = 'card';
      card.id = p.slug;
      card.innerHTML = `
        <div class="card-hdr">
          <span class="badge ${{p.severity}}">${{ps.emoji}} ${{ps.label}}</span>
          <span class="card-title">${{p.title}}</span>
          <span class="card-chev">▶</span>
        </div>
        <div class="card-body">
          ${{p.problem_html ? `<div class="callout problem"><strong>💬 Problem</strong>${{p.problem_html}}</div>` : ''}}
          ${{p.weak_html ? `<div class="callout critical"><strong>🔴 Weak</strong>${{p.weak_html}}</div>` : ''}}
          <div class="callout ${{p.severity}}"><strong>🟡 Strong</strong>${{p.staff_html}}</div>
          ${{p.staff_plus_html ? `<div class="callout pattern"><strong>🟢 Staff+</strong>${{p.staff_plus_html}}</div>` : ''}}
          <div class="callout ${{p.severity}}" style="opacity:.92"><strong>Trade-offs</strong>${{p.trade_html}}</div>
          <div class="callout ${{p.severity}}" style="opacity:.85"><strong>Example</strong>${{p.example_html}}</div>
          ${{p.java_html ? p.java_html : ''}}
          ${{p.visual_html ? `<div class="visual">📊 <strong>Visual:</strong> ${{p.visual_html}}</div>` : ''}}
        </div>`;
      card.querySelector('.card-hdr').onclick = () => card.classList.toggle('open');
      secEl.appendChild(card);
      const link = document.createElement('a');
      link.className = 'sb-link';
      link.href = '#' + p.slug;
      link.innerHTML = `<span class="sb-dot" style="background:var(--${{p.severity}}-bdr)"></span>${{p.title}}`;
      link.onclick = e => {{ e.preventDefault(); document.getElementById(p.slug)?.scrollIntoView({{behavior:'smooth'}}); card.classList.add('open'); }};
      sbSec.appendChild(link);
    }});
    root.appendChild(secEl);
    sb.appendChild(sbSec);
  }});
}}

document.querySelectorAll('.fchip').forEach(b => {{
  b.onclick = () => {{
    if (b.dataset.f === 'all') {{
      document.querySelectorAll('.fchip').forEach(x => x.classList.toggle('on', x.dataset.f === 'all'));
    }} else {{
      document.querySelector('.fchip[data-f="all"]').classList.remove('on');
      b.classList.toggle('on');
      if (!document.querySelectorAll('.fchip.on').length) document.querySelector('.fchip[data-f="all"]').classList.add('on');
    }}
    render();
  }};
}});
document.getElementById('q').oninput = render;
document.getElementById('theme').onclick = () => {{
  const d = document.documentElement;
  const dark = d.dataset.theme ? d.dataset.theme === 'light' : !matchMedia('(prefers-color-scheme:dark)').matches;
  d.dataset.theme = dark ? 'dark' : 'light';
  localStorage.setItem('qf-color-theme', d.dataset.theme);
}};
const saved = localStorage.getItem('qf-color-theme');
if (saved) document.documentElement.dataset.theme = saved;
let expanded = false;
document.getElementById('expand').onclick = () => {{
  expanded = !expanded;
  document.querySelectorAll('.card').forEach(c => c.classList.toggle('open', expanded));
  document.getElementById('expand').textContent = expanded ? 'Collapse all' : 'Expand all';
}};
// Default: show critical + high for drill focus; user can click All
document.querySelectorAll('.fchip').forEach(x => x.classList.remove('on'));
['critical','high','important','pattern'].forEach(f => document.querySelector(`.fchip[data-f="${{f}}"]`)?.classList.add('on'));
render();
routeHash();
</script>
</body>
</html>"""


def load_diagram_inc() -> str:
    return DIAGRAMS_INC_PATH.read_text(encoding="utf-8")


def main():
    md = MD_PATH.read_text(encoding="utf-8")
    md = reorganize_pattern_sections(md)
    intro, sections = parse_sections(md)
    md = enrich_markdown(md, sections)
    MD_PATH.write_text(md, encoding="utf-8")
    HTML_PATH.write_text(build_html(intro, sections, md), encoding="utf-8")
    DIAGRAMS_HTML_PATH.write_text(build_diagram_redirect(), encoding="utf-8")
    n_patterns = sum(len(s["patterns"]) for s in sections)
    print(f"Updated {MD_PATH.name} with severity badges & callouts")
    print(f"Wrote {HTML_PATH.name} ({n_patterns} patterns, combined with diagrams)")
    print(f"Wrote {DIAGRAMS_HTML_PATH.name} (redirect to combined page)")


if __name__ == "__main__":
    main()
