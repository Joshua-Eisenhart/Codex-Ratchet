# Ratchet Visualizer Design Contract

## Visual Theme & Atmosphere

Use a finite constraint-surface style: dark or paper technical surfaces, thin rules, compact labels, and inspectable mechanics. Prefer mechanical diagrams, ledgers, and source paths over metaphor.

## Color Palette & Roles

- Near-black or warm paper backgrounds define the work surface.
- Amber marks active/source-backed mechanics.
- Cyan marks cold, record, or boundary channels.
- Rose marks warnings, killed states, or claim boundaries.
- Dim paper text is for metadata, provenance, and inactive controls.

## Typography Rules

Use Inter for normal interface text and JetBrains Mono for labels, ledgers, stage IDs, and source paths. Keep letter spacing at zero except short all-caps micro-labels already established in the visualizer.

## Component Stylings

Panels use one-pixel borders and squared corners. Controls should be compact, stable, and readable. Diagrams should be SVG or HTML mechanics surfaces with explicit labels and no decorative glow.

## Layout Principles

Separate process flow, mathematical primitives, and ontology overlays. Process views should keep stage order visible. Ledger views should keep source-vs-fallback status visible. Do not hide noncommutation or order-of-operations when relevant.

## Motion / Interaction

Interaction should select stages, operations, layers, or evidence rows. Motion may clarify state transitions, but must not imply a proof result or physical value not present in source data.

## Do's and Don'ts

- Do read existing JSON/result artifacts before displaying values.
- Do cite the mirrored browser payload and canonical result path when values are source-backed.
- Do label fallback UI skeleton data clearly.
- Do not alter canonical sim, proof, or math claims from the visualizer.
- Do not invent efficiencies, demon correctness, Landauer values, proof success, or axis admission.
- Do not use mystical metaphors, generic AI-glow styling, or decorative effects as evidence.

## Responsive Behavior

Views should remain inspectable on narrower screens by allowing panels to scroll. Fixed-format diagrams need stable aspect ratios and should not resize text into overlap.

## Agent Prompt Guide

Future visualizer agents should improve layout, animation, interaction, affordances, and explanatory clarity only. Preserve strict source-vs-fallback distinction, keep labels sourced from `data.js` or sim result files, and treat sim/proof outputs as the source of truth.
