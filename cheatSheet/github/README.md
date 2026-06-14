# GitHub-viewable cheat sheets

The interactive HTML files in the parent folder use JavaScript to render system cards.
**GitHub's file preview strips `<script>`**, so those pages look empty here.

This folder contains static versions you can read directly on GitHub:

| View | Best for |
|------|----------|
| [v15 index (Pages HTML)](v15/index.html) | **40 systems** — links to pre-rendered cards on GitHub Pages |
| [v15 index (Markdown)](v15/index.md) | Same TOC — renders in the GitHub repo browser |
| [v15 static HTML](v15-static.html) | Same content, single HTML file with expandable sections |
| [v10 cards index (Pages HTML)](v10-cards/index.html) | **26 systems** — links to pre-rendered cards on GitHub Pages |
| [v10 cards index (Markdown)](v10-cards/index.md) | Same TOC — renders in the GitHub repo browser |
| [v10 reference index](v10-reference-index.md) | ByteByteGo chapter + cloud appendix links |

## Interactive versions (full features)

- [system_design_cheatsheet_v14.html](../system_design_cheatsheet_v14.html) — v15, search, interview mode, keyboard shortcuts
- [system_design_cheatsheet_v15_github.html](../system_design_cheatsheet_v15_github.html) — v15 pre-rendered for GitHub Pages
- [SystemDesign_Complete_v10.html](../SystemDesign_Complete_v10.html) — ByteByteGo reference + cloud CLI tables
- [SystemDesign_Complete_v10_github.html](../SystemDesign_Complete_v10_github.html) — v10 pre-rendered for GitHub Pages
- [EDA_Interview_Question_Bank_Complete.html](../EDA_Interview_Question_Bank_Complete.html) — EDA interview bank (26 questions, follow-ups, diagrams)

## Regenerate

```bash
python3 scripts/build_github_view.py
```
