#!/usr/bin/env python3
"""Build AI Interview Prep HTML from cheatSheet/AI_TOPICS_INTERVIEW_PREP.md."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "cheatSheet" / "AI_TOPICS_INTERVIEW_PREP.md"
OUT = ROOT / "cheatSheet" / "AI_Interview_Prep.html"

REVIEW_IDS = {"rag", "agents", "how-ai", "hallucination"}


def slugify(title: str) -> str:
    s = re.sub(r"^\d+\.\s*", "", title.strip().lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    mapping = {
        "rag-retrieval-augmented-generation": "rag",
        "agents": "agents",
        "how-you-use-ai-your-personal-framework": "how-ai",
        "hallucination-handling": "hallucination",
        "tie-it-all-together-one-story-for-the-ai-session": "story",
        "live-demo-script-2-minutes": "demo",
        "cheat-sheet-morning-of": "cheatsheet",
        "questions-to-ask-them-shows-maturity": "questions",
        "how-to-use-this-doc": "how-to",
    }
    return mapping.get(s, s[:32])


def md_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def parse_table(lines: list[str]) -> tuple[str, list[str]]:
    rows: list[list[str]] = []
    rest: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                i += 1
                continue
            rows.append(cells)
            i += 1
            continue
        rest = lines[i:]
        break
    if not rows:
        return "", lines
    head, *body = rows
    h = '<table class="md-table"><thead><tr>' + "".join(
        f"<th>{md_inline(c)}</th>" for c in head
    ) + "</tr></thead><tbody>"
    for row in body:
        h += "<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in row) + "</tr>"
    h += "</tbody></table>"
    return h, rest


def parse_blocks(body: str) -> str:
    lines = body.split("\n")
    parts: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.strip() == "---":
            i += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            cls = "code-bash" if lang == "bash" else "code-block"
            parts.append(
                f'<pre class="{cls}"><code>{html.escape(chr(10).join(code_lines))}</code></pre>'
            )
            continue
        if line.strip().startswith("|"):
            tbl, rest_lines = parse_table(lines[i:])
            parts.append(tbl)
            consumed = len(lines[i:]) - len(rest_lines)
            i += consumed
            continue
        if line.startswith("> "):
            quote: list[str] = []
            while i < len(lines) and (lines[i].startswith("> ") or lines[i].strip() == ""):
                if lines[i].startswith("> "):
                    quote.append(lines[i][2:])
                i += 1
            parts.append(f'<div class="abx">{md_inline(" ".join(quote))}</div>')
            continue
        if re.match(r"^[-*]\s+", line):
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]))
                i += 1
            parts.append(
                "<ul class=\"md-ul\">"
                + "".join(f"<li>{md_inline(it)}</li>" for it in items)
                + "</ul>"
            )
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]))
                i += 1
            parts.append(
                "<ol class=\"md-ol\">"
                + "".join(f"<li>{md_inline(it)}</li>" for it in items)
                + "</ol>"
            )
            continue
        para: list[str] = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(
            ("#", ">", "|", "-", "*", "`")
        ) and not re.match(r"^\d+\.\s+", lines[i]):
            para.append(lines[i])
            i += 1
        parts.append(f"<p>{md_inline(' '.join(para))}</p>")
    return "\n".join(parts)


def parse_sections(md: str) -> list[dict]:
    title_m = re.match(r"# (.+)\n", md)
    title = title_m.group(1) if title_m else "AI Interview Prep"
    rest = md[title_m.end() :] if title_m else md
    intro = ""
    intro_m = re.match(r"^(.+?)\n---\n", rest, re.S)
    if intro_m:
        intro = intro_m.group(1).strip()
        rest = rest[intro_m.end() :]
    chunks = re.split(r"\n(?=## )", rest)
    sections = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("## "):
            continue
        first, _, body = chunk.partition("\n")
        sec_title = first[3:].strip()
        sid = slugify(sec_title)
        body = re.sub(r"\n---\s*\n?", "\n", body).strip()
        sub_html = ""
        sub_parts = re.split(r"\n(?=### )", body)
        preamble = sub_parts[0].strip()
        if preamble:
            sub_html += parse_blocks(preamble)
        for sub in sub_parts[1:]:
            sub = sub.strip()
            if not sub.startswith("### "):
                continue
            sub_line, _, sub_body = sub.partition("\n")
            sub_title = sub_line[4:].strip()
            is_push = sub_title.lower().startswith("if they push")
            is_30s = "30-second" in sub_title.lower()
            inner = parse_blocks(sub_body.strip())
            if is_30s:
                sub_html += f'<div class="blbl">30-second answer</div>{inner}'
            elif is_push:
                sub_html += f'<div class="blbl">If they push</div>{inner}'
            elif sub_title.startswith("Step ") or sub_title.startswith("Golden set"):
                sub_html += f'<h4 class="sub-h4">{md_inline(sub_title)}</h4>{inner}'
            else:
                sub_html += f'<div class="blbl">{md_inline(sub_title)}</div>{inner}'
        sections.append(
            {
                "id": sid,
                "title": sec_title,
                "html": sub_html,
                "review": sid in REVIEW_IDS,
            }
        )
    return {"title": title, "intro": intro, "sections": sections}


def build_html(data: dict) -> str:
    nav_items = []
    for i, s in enumerate(data["sections"]):
        rev = (
            f'<span class="scnt rev-dot" id="dot-{s["id"]}"></span>'
            if s["review"]
            else ""
        )
        label = re.sub(r"^\d+\.\s*", "", s["title"])
        nav_items.append(
            f'<button class="sbi" data-id="{s["id"]}" onclick="go(\'{s["id"]}\')">'
            f'<span class="sdot" style="background:var(--tag-{i % 4})"></span>'
            f"{html.escape(label)}{rev}</button>"
        )
    nav_html = "".join(nav_items)

    cards = "".join(
        f'<article class="sec-card{" reviewable" if s["review"] else ""}" id="{s["id"]}" data-review="{str(s["review"]).lower()}">'
        f'<header class="sec-hdr" onclick="toggleSec(this.parentElement)">'
        f'<h2>{html.escape(s["title"])}</h2><span class="sec-chev">▶</span></header>'
        f'<div class="sec-body">{s["html"]}</div></article>'
        for s in data["sections"]
    )
    intro_html = parse_blocks(data["intro"]) if data["intro"] else ""
    sections_json = json.dumps(data["sections"], ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Interview Prep — RAG, Agents, Evals</title>
<meta name="description" content="Interview prep for RAG, agents, hallucination handling, and how you use AI — tied to Player Service + Ollama.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0D1117;--surf:#161B22;--surf2:#1C2128;--surf3:#21262D;--bdr:#30363D;--bdr2:#3D444D;
  --tx:#E6EDF3;--tx2:#8B949E;--tx3:#484F58;--acc:#A371F7;--acc-bg:rgba(163,113,247,.12);--acc-bdr:rgba(163,113,247,.35);
  --grn:#3FB950;--grn-bg:rgba(63,185,80,.1);--grn-bdr:rgba(63,185,80,.3);
  --amb:#D29922;--amb-bg:rgba(210,153,34,.1);
  --tag-0:#A371F7;--tag-1:#58A6FF;--tag-2:#3FB950;--tag-3:#F85149;
  --mono:'JetBrains Mono',monospace;--sans:'Inter',sans-serif;--r:8px;--rl:12px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--tx);font-family:var(--sans);font-size:14px;line-height:1.6;min-height:100vh}}
.hdr{{background:var(--surf);border-bottom:1px solid var(--bdr);padding:0 24px;position:sticky;top:0;z-index:100;display:flex;align-items:center;gap:16px;height:56px}}
.logo{{font-family:var(--mono);font-size:13px;font-weight:500;color:var(--acc);background:var(--acc-bg);border:1px solid var(--acc-bdr);padding:3px 10px;border-radius:6px;flex-shrink:0}}
.hdr-t{{font-size:14px;font-weight:500}}.hdr-s{{font-size:12px;color:var(--tx2)}}
.hdr-r{{margin-left:auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
.hdr-link{{font-size:12px;color:var(--tx2);text-decoration:none}}.hdr-link:hover{{color:var(--acc)}}
.pw{{display:flex;align-items:center;gap:8px}}.pl{{font-size:12px;color:var(--tx2)}}
.pb{{width:100px;height:4px;background:var(--surf3);border-radius:2px;overflow:hidden}}
.pf{{height:100%;background:var(--grn);width:0%;transition:width .3s}}
.pc{{font-size:12px;font-family:var(--mono);color:var(--grn);min-width:32px}}
.layout{{display:flex;min-height:calc(100vh - 56px)}}
.sb{{width:230px;flex-shrink:0;background:var(--surf);border-right:1px solid var(--bdr);padding:16px 0;position:sticky;top:56px;height:calc(100vh - 56px);overflow-y:auto}}
.sbl{{font-size:10px;font-weight:600;letter-spacing:.08em;color:var(--tx3);text-transform:uppercase;padding:0 16px;margin:12px 0 6px}}
.sbi{{display:flex;align-items:center;gap:8px;padding:7px 16px;cursor:pointer;color:var(--tx2);font-size:12.5px;border-left:2px solid transparent;width:100%;background:transparent;border-right:0;border-top:0;border-bottom:0;text-align:left}}
.sbi:hover{{background:var(--surf2);color:var(--tx)}}.sbi.active{{color:var(--acc);border-left-color:var(--acc);background:var(--acc-bg)}}
.sdot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.scnt{{margin-left:auto;font-size:10px;color:var(--tx3)}}
.rev-dot{{width:8px;height:8px;border-radius:50%;background:var(--surf3);border:1px solid var(--bdr)}}
.rev-dot.done{{background:var(--grn);border-color:var(--grn-bdr)}}
.main{{flex:1;padding:24px;min-width:0;max-width:900px}}
.intro{{background:var(--surf);border:1px solid var(--bdr);border-radius:var(--rl);padding:16px 18px;margin-bottom:20px;font-size:13px;color:var(--tx2);line-height:1.7}}
.intro a{{color:var(--acc)}}
.sw{{position:relative;margin-bottom:16px}}
.si{{width:100%;background:var(--surf);border:1px solid var(--bdr);border-radius:var(--r);color:var(--tx);font-size:13px;padding:8px 12px;font-family:var(--sans)}}
.si:focus{{outline:none;border-color:var(--acc-bdr)}}
.sec-card{{background:var(--surf);border:1px solid var(--bdr);border-radius:var(--rl);margin-bottom:10px;overflow:hidden}}
.sec-card.open{{border-color:var(--acc-bdr)}}
.sec-card.hidden{{display:none}}
.sec-hdr{{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;cursor:pointer;user-select:none}}
.sec-hdr:hover{{background:var(--surf2)}}
.sec-hdr h2{{font-size:14px;font-weight:500;line-height:1.4;padding-right:12px}}
.sec-chev{{color:var(--tx3);transition:transform .2s;flex-shrink:0}}
.sec-card.open .sec-chev{{transform:rotate(90deg)}}
.sec-body{{display:none;padding:0 16px 16px;border-top:1px solid var(--bdr);font-size:13px;color:var(--tx2);line-height:1.75}}
.sec-card.open .sec-body{{display:block}}
.blbl{{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--tx3);margin:14px 0 8px;display:flex;align-items:center;gap:6px}}
.blbl::after{{content:'';flex:1;height:1px;background:var(--bdr)}}
.sub-h4{{font-size:12px;font-weight:600;color:var(--tx);margin:12px 0 6px}}
.abx{{background:var(--surf2);border:1px solid var(--bdr);border-left:3px solid var(--acc);border-radius:var(--r);padding:12px 14px;margin:8px 0;font-size:13px;line-height:1.75;color:var(--tx)}}
.md-table{{width:100%;border-collapse:collapse;font-size:12px;margin:10px 0}}
.md-table th{{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--tx3);padding:8px 10px;border-bottom:1px solid var(--bdr);text-align:left;background:var(--surf2)}}
.md-table td{{padding:8px 10px;border-bottom:1px solid var(--bdr);vertical-align:top}}
.md-table tr:last-child td{{border-bottom:none}}
.md-table code{{font-family:var(--mono);font-size:11px;background:var(--surf3);padding:1px 5px;border-radius:4px}}
.md-ul,.md-ol{{margin:8px 0 8px 20px}}.md-ul li,.md-ol li{{margin:4px 0}}
p{{margin:8px 0}}
code{{font-family:var(--mono);font-size:11.5px;background:var(--surf3);padding:1px 5px;border-radius:4px;color:var(--tx)}}
.code-block,.code-bash{{font-family:var(--mono);font-size:11.5px;background:var(--surf2);border:1px solid var(--bdr);border-radius:var(--r);padding:12px 14px;margin:10px 0;overflow-x:auto;white-space:pre;color:var(--tx);line-height:1.55}}
.bact{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;padding-top:12px;border-top:1px solid var(--bdr)}}
.abtn{{font-size:12px;padding:6px 12px;border-radius:var(--r);cursor:pointer;border:1px solid;font-family:var(--sans)}}
.abtn-g{{background:var(--grn-bg);color:var(--grn);border-color:var(--grn-bdr)}}
.abtn-n{{background:var(--surf3);color:var(--tx2);border-color:var(--bdr)}}
@media(max-width:760px){{.sb{{display:none}}.hdr-r .pw{{display:none}}}}
</style>
</head>
<body>
<header class="hdr">
  <span class="logo">AI</span>
  <div>
    <div class="hdr-t">AI Interview Prep — RAG, Agents, Evals</div>
    <div class="hdr-s">Player Service · 4 core topics · demo script · morning-of cheat sheet</div>
  </div>
  <div class="hdr-r">
    <a class="hdr-link" href="index.html">Index</a>
    <a class="hdr-link" href="system_design_cheatsheet_v14.html">v15 SD</a>
    <a class="hdr-link" href="https://github.com/eddyclhung/backend-java-player-service" target="_blank" rel="noopener">Player Service repo</a>
    <div class="pw"><span class="pl">Reviewed</span><div class="pb"><div class="pf" id="pf"></div></div><span class="pc" id="pc">0 / 4</span></div>
  </div>
</header>
<div class="layout">
  <nav class="sb" id="sb">{nav_html}</nav>
  <main class="main">
    <div class="intro">{intro_html}<p style="margin-top:10px">Source: <a href="AI_TOPICS_INTERVIEW_PREP.md">AI_TOPICS_INTERVIEW_PREP.md</a> · <a href="https://github.com/eddyclhung/backend-java-player-service/blob/main/AI_TOPICS_INTERVIEW_PREP.md" target="_blank" rel="noopener">upstream repo</a></p></div>
    <div class="sw"><input class="si" id="search" placeholder="Search topics, files, patterns…" oninput="filter(this.value)"></div>
    <div id="cards">{cards}</div>
  </main>
</div>
<script>
const SECTIONS = {sections_json};
const REVIEW_KEY = 'ai-prep-reviewed';
const REVIEW_IDS = {json.dumps(sorted(REVIEW_IDS))};

function loadReviewed() {{
  try {{ return JSON.parse(localStorage.getItem(REVIEW_KEY) || '{{}}'); }} catch(e) {{ return {{}}; }}
}}
function saveReviewed(r) {{ localStorage.setItem(REVIEW_KEY, JSON.stringify(r)); }}

function updateProgress() {{
  const r = loadReviewed();
  const n = REVIEW_IDS.filter(id => r[id]).length;
  document.getElementById('pf').style.width = (n / REVIEW_IDS.length * 100) + '%';
  document.getElementById('pc').textContent = n + ' / ' + REVIEW_IDS.length;
  REVIEW_IDS.forEach(id => {{
    const dot = document.getElementById('dot-' + id);
    if (dot) dot.classList.toggle('done', !!r[id]);
  }});
}}

function go(id) {{
  const el = document.getElementById(id);
  if (!el) return;
  document.querySelectorAll('.sbi').forEach(b => b.classList.toggle('active', b.dataset.id === id));
  el.classList.add('open');
  el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  if (location.hash !== '#' + id) history.replaceState(null, '', '#' + id);
}}

function toggleSec(card) {{
  card.classList.toggle('open');
}}

function markReview(id, yes) {{
  const r = loadReviewed();
  r[id] = yes;
  saveReviewed(r);
  updateProgress();
}}

function filter(q) {{
  q = q.toLowerCase().trim();
  document.querySelectorAll('.sec-card').forEach(c => {{
    const text = c.textContent.toLowerCase();
    c.classList.toggle('hidden', q && !text.includes(q));
  }});
}}

document.querySelectorAll('.sec-card.reviewable .sec-body').forEach(body => {{
  const card = body.parentElement;
  const id = card.id;
  const act = document.createElement('div');
  act.className = 'bact';
  act.innerHTML = '<button class="abtn abtn-g" onclick="markReview(\\'' + id + '\\',true)">Mark reviewed</button><button class="abtn abtn-n" onclick="markReview(\\'' + id + '\\',false)">Clear</button>';
  body.appendChild(act);
}});

document.querySelectorAll('.sbi').forEach(b => {{
  b.addEventListener('click', () => go(b.dataset.id));
}});

if (location.hash) {{
  const id = location.hash.slice(1);
  setTimeout(() => go(id), 50);
}} else {{
  document.querySelector('.sec-card')?.classList.add('open');
}}

updateProgress();
</script>
</body>
</html>"""


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    data = parse_sections(md)
    OUT.write_text(build_html(data), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(data['sections'])} sections)")


if __name__ == "__main__":
    main()
