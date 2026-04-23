# Tier F — Axes 1–6 on the Composed Manifold

> **Worker spawn preamble (mandatory):** every spawned Claude worker receives Block B (140-word) from `~/wiki/harness/SALIENCE_PREAMBLE.md` prepended to its system prompt before any task description. See `system_v5/ops/HERMES_RULES.md` §0. Probe-tested 2026-04-17 on fresh Haiku.


Runs after Tier E (canonical composed Axis 0). Axes 1–6 inherit the B/C/D/E infrastructure — no new math, just composition.

Preconditions:
- Tier E gate GREEN: `~/wiki/projects/codex-ratchet/tier_e.md` confirms canonical composed Axis 0
- Composition operator π available
- Layer-pullback gradient defined
- Orthogonality matrix rebuilt against composed Axis 0

## Objective

Each of axes 1–6 gets a composed-manifold canonical sim, using the B/C/D/E legos. Expect: some previously "orthogonal" axes re-couple on the real manifold; some survive; some collapse into each other.

## Axes to sim

| Axis | Candidate math (flat-substrate label) | Expected status on composed |
|---|---|---|
| 1 | axis1_alignment / pre-distinguishability | may become structural not axis-specific |
| 2 | axis2_cohesion | may resolve as flux-coherence layer artifact |
| 3 | axis3_spinor / chirality layer | candidate spinor structure; may couple into Weyl layer |
| 4 | axis4_process / judging-function layer | candidate operator algebra; original Fe/Fi/Te/Ni home |
| 5 | axis5_torus / Hopf layer | likely re-absorbs into Hopf shell-local |
| 6 | axis6_open_seam | current research target per `project_axis0_status.md` |

These labels are **provisional**. Composed-manifold sims may show multiple axes are the same thing under perspectival rotation (per harness/09).

## One worker per axis (Sonnet Claude, separate worktrees)

Each worker:
- Reads harness/00-10, TIER_E.md, axis0_canonical_composed.py
- Writes `system_v4/probes/axis<N>_canonical_composed.py` following the Axis 0 composed template
- Uses the same composition operator π with axis-specific carrier observables
- Enqueues to `system_v5/ops/queue_tier_f.txt` (create if missing)
- Commits per sim: `"tier-f/F<n>: axis<N> canonical composed"`

## Collapse detection (harness/09 doctrine)

After all 6 axes sim, auditor checks:
- Any two axes producing the **same invariant** on composed manifold → collapse candidate
- Axes with no composed-manifold signal distinct from Axis 0 → candidate for absorption
- Axes with emergent-only signal (only appears when simultaneously active) → primary axes

Preserve all surviving candidates. Do NOT prematurely collapse per harness/08.

## Gate

- ✓ 6 composed-axis probes exist, canonical, passes local rerun
- ✓ Orthogonality matrix recomputed against composed axes (not flat)
- ✓ Collapse analysis report at `~/wiki/projects/codex-ratchet/tier_f_collapse.md`
- ✓ Surviving candidate set documented (could be 6, could be 2 — both valid outcomes)

## Post-Tier F: the research frontier

- Bridge claims (rho_AB, Xi, Phi0) per coupling program step 6 — only after Tier E/F
- Dynamic topology / remesh tier (substrate layer currently missing, per viz track slice 10)
- Constraint manifold dynamics — how admissibility predicates evolve under probe-updating

## Reporting

- `~/wiki/projects/codex-ratchet/tier_f.md` gate evidence
- `~/wiki/projects/codex-ratchet/tier_f_collapse.md` collapse analysis
- Per-axis results feed the viz Manim pipeline (viz Tier slice 7+) for a composed-manifold "all 7 axes" explainer video
