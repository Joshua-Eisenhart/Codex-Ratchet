# Engine View Visualizer Skill

Use this skill when polishing the Carnot or Szilard engine visualizer views.

## Contract

- Do not alter proof or sim claims.
- Do not invent results.
- Read existing JSON/result artifacts before displaying values.
- Only improve layout, animation, interaction, affordances, and explanatory clarity.
- Keep labels sourced from `visualizer/data.js`, engine visualizer payloads, or canonical sim result files.
- Preserve a strict source-vs-fallback distinction in the UI.

## Workflow

1. Inspect `visualizer/ratchet-visualizer.html`, `visualizer/app.jsx`, and the engine view files.
2. Inspect available engine data payloads and canonical result JSON before changing displayed fields.
3. Patch only visualizer files unless a trivial loader/path issue blocks the view.
4. Verify script order and that each displayed source-backed value has an explicit provenance path.
