# GitHub-viewable cheat sheets

**Why the interactive HTML looks broken on GitHub:** GitHub's file preview **removes all `<script>` tags**. The original `system_design_cheatsheet_v14.html` builds cards with JavaScript, so grids appear empty.

## Use these instead

| View | Works on GitHub? | Best for |
|------|------------------|----------|
| [v15 GitHub HTML](../system_design_cheatsheet_v15_github.html) | Yes — pre-rendered cards + expandable sections | Full HTML in one file |
| [v15 Markdown index](v15/index.md) | Yes — native rendering | Reading in repo browser |
| [v10 GitHub HTML](../SystemDesign_Complete_v10_github.html) | Yes | ByteByteGo + 26 cards |
| [v10 cards Markdown](v10-cards/index.md) | Yes | Card summaries only |

## Full interactivity (search, tabs, interview mode)

1. **Locally:** open `system_design_cheatsheet_v14.html` in a browser
2. **GitHub Pages:** enable Pages (Settings → Pages → **GitHub Actions**). After deploy, visit `https://<user>.github.io/<repo>/` — JavaScript runs and the interactive edition works

## Interactive source files (local / Pages only)

- [system_design_cheatsheet_v14.html](../system_design_cheatsheet_v14.html)
- [SystemDesign_Complete_v10.html](../SystemDesign_Complete_v10.html)

## Regenerate

```bash
python3 scripts/build_github_view.py
```
