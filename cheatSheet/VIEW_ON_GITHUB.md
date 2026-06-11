# How to view cheat sheets on GitHub

Clicking an `.html` file on GitHub shows **syntax-highlighted source code**, not a rendered page. That is normal — GitHub serves HTML as `text/plain` in the repo browser.

## What works today (no setup)

| Format | Link | Experience |
|--------|------|------------|
| **v15 Markdown (recommended)** | [github/v15/index.md](github/v15/index.md) | Renders in GitHub — 40 systems, expandable per-card links |
| **v10 Markdown** | [github/v10-cards/index.md](github/v10-cards/index.md) | 26 system cards |
| **Quick-fire** | [interview-quick-fire.html](interview-quick-fire.html) or [.md](interview-quick-fire.md) | Colorful HTML locally; MD on GitHub |

## Render HTML without cloning

Paste the **blob** URL (from GitHub: `...` → *Copy permalink*) into a preview service:

- [html-preview.github.io](https://html-preview.github.io/) — prepend `https://html-preview.github.io/?` to your GitHub file URL
- Example (v15 pre-rendered):  
  `https://html-preview.github.io/?https://github.com/eddyclhung/systemDesign/blob/main/cheatSheet/system_design_cheatsheet_v15_github.html`
- Simpler static file (smaller):  
  `https://html-preview.github.io/?https://github.com/eddyclhung/systemDesign/blob/main/cheatSheet/github/v15-static.html`

## Full interactivity (search, tabs, interview mode)

**Option A — GitHub Pages (best)**

1. Repo → **Settings** → **Pages** → Build type: **GitHub Actions**
2. Push to `main` (workflow `.github/workflows/pages.yml` deploys `cheatSheet/`)
3. Open: `https://eddyclhung.github.io/systemDesign/`  
   (or `.../system_design_cheatsheet_v15_github.html`)

**Option B — Local**

```bash
git clone git@github.com:eddyclhung/systemDesign.git
open systemDesign/cheatSheet/index.html
```

## File guide

| File | Use when |
|------|----------|
| `system_design_cheatsheet_v14.html` | Local/Pages — full JS (search, interview mode) |
| `system_design_cheatsheet_v15_github.html` | Pages or html-preview — pre-rendered cards + JS tabs |
| `github/v15-static.html` | html-preview — lightweight, no JS |
| `github/v15/*.md` | **GitHub repo browser** — always works |

Regenerate after edits:

```bash
python3 scripts/build_prerendered_html.py
python3 scripts/build_github_view.py
```
