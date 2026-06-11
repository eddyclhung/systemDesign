# GitHub-viewable cheat sheets

The interactive HTML files in the parent folder use JavaScript to render system cards.

**Important:** GitHub's repo browser does **not** render `.html` files as web pages — it shows HTML **source code**. For browsing inside GitHub, use **Markdown** below. For HTML, use [GitHub Pages](../VIEW_ON_GITHUB.md) or [html-preview](https://html-preview.github.io/?https://github.com/eddyclhung/systemDesign/blob/main/cheatSheet/github/v15-static.html).

| View | Best for |
|------|----------|
| [**v15 index**](v15/index.md) | **40 systems** — renders on GitHub (start here) |
| [Interview quick-fire](../interview-quick-fire.html) | **70+ patterns** — colorful offline HTML |
| [Interview quick-fire MD](../interview-quick-fire.md) | Same content — GitHub-native Markdown |
| [v15 static HTML](v15-static.html) | Lightweight HTML for html-preview / Pages |
| [Viewing guide](../VIEW_ON_GITHUB.md) | Pages setup, preview links, local open |
| [v10 cards index](v10-cards/index.md) | **26 systems** — ByteByteGo card summaries |
| [v10 reference index](v10-reference-index.md) | ByteByteGo chapter + cloud appendix links |

## Interactive versions (full features)

- [system_design_cheatsheet_v14.html](../system_design_cheatsheet_v14.html) — v15, search, interview mode, keyboard shortcuts
- [SystemDesign_Complete_v10.html](../SystemDesign_Complete_v10.html) — ByteByteGo reference + cloud CLI tables

## Regenerate

```bash
python3 scripts/build_github_view.py
```
