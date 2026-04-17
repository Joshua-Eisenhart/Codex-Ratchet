# Tier VIZ — Visualization Deepening (parallel track)

Independent of Tier A/B/D. Runs in parallel. Produces the truth→live→explainer visualization stack.

Preconditions: read `ops/HERMES_RULES.md` and `ops/OVERNIGHT.md`. Verify harness at `~/wiki/harness/00_READ_FIRST.md`.

## Role

One Hermes terminal owns `system_v4/visualization/` and `system_v4/tests/test_viz_*.py`. Runs autonomously on a cron (every 10–15 min). Works in bounded slices. Never steers into other tier scopes.

## Three surfaces to deepen

| Surface | Purpose | Consumer |
|---|---|---|
| **Truth surface** | replay manifests, exporters, inspection, validator | machine / audit |
| **Live surface** | interactive viewer, scrubber, status headers | operator |
| **Explainer surface** | Manim-rendered videos from admitted run metadata | communication to others |

## Harness-native vocabulary (already landed)

Manifest fields every replay run carries:
- `constraint_set`, `probe_family`, `carrier`, `lane`, `layer`
- `witness_type`, `claim_state`, `promotion_status`, `status_label`
- `geometry_rendering_status`
- `negative_controls`, `exclusion_criteria`
- `eligible_consumers`, `blocked_consumers`, `promotion_blockers`
- `live_splits`, `witness_trace`, `admission_stage`, `promotion_target_stage`

Viewer/status surfaces display constraint→probe→admission→claim before per-frame metrics.

## Bounded slices — ordered

1. ✅ `consumer_admission` executable (block viewer launch for denied consumers, skip blocked runs in best-run resolution)
2. ✅ Richer status surface + scrubber header (constraint/probe/claim-ceiling/admission/exclusion)
3. ⬜ Wire consumer-admission visibility into `best_run_viewer` render output + CLI flags
4. ⬜ Add CLI `--consumer <name>` to `scripts/view_best_replay.sh`
5. ⬜ Add a **Manim-facing export summary** object at `system_v4/visualization/manim_export.py` — collects `constraint_set`, `witnesses`, `exclusions`, `admitted_survivors`, per-lane progression. Pure data, no rendering.
6. ⬜ Add `tool_integration_manim.py` capability sim once Manim is introduced (keeps it on the tool ladder)
7. ⬜ Prototype one Manim scene that renders a small atlas transition from manim_export.py output
8. ⬜ Add witness/exclusion timeline overlay to live scrubber
9. ⬜ Add lane-admission gate visualization (show required lower-lane prerequisites)
10. ⬜ Dynamic topology/remesh metadata in replay contract (last deep substrate tier)

## Hard rules

1. Only touch `system_v4/visualization/*`, `system_v4/tests/test_viz_*.py`, `scripts/view_*.sh`, `scripts/render_manim_*.py`. No repo-wide refactors.
2. Run targeted tests after each slice, then full `pytest system_v4/tests/test_viz_*.py -q`.
3. Commit per slice: `"tier-viz/<n>: <one-line>"`.
4. Language discipline per `~/wiki/harness/03_language_discipline.md`. No banned verbs.
5. Claim→Evidence→Verification format in reports. Use `status_label` spine (exists / runs / passes local rerun / canonical by process).
6. No cross-tier work. If tier A/B/D probe landing looks related, log in `~/wiki/projects/codex-ratchet/_steward_questions.md` and continue viz work.
7. Fail-closed on runtime/model mismatch or protected-file write-back ambiguity (per the canonical failure rules the viz terminal derived).

## Cron spec (for the Hermes terminal that owns this track)

- Cadence: every 10 min (tighten/loosen if slice cycle changes)
- Model: `gpt-5.4-low` (viz work is mostly mechanical; low is sufficient)
- Provider: `openai-codex`
- Repeat: indefinite until owner stops
- First tick: run one slice now

## Autonomy defaults (viz-specific)

- If `system_v4/visualization/exporters/` produces a new exporter, enqueue one smoke-test probe to `ops/queue_tier_a.txt`.
- If pytest fails at full viz rerun, revert the last slice and report blocker to `_steward_questions.md`.
- If the viz terminal needs to add a new Python dep, write a proposal to `_steward_questions.md` and wait for owner — do not auto-install.
- Manim is available as the Hermes `manim-video` skill. Use the skill; do NOT pip-install. Prototype scene work is allowed using the skill surface.

## Reporting

- On gate-worthy progress: append `<ISO> viz-cron slice=<n> status=<passes local rerun> evidence=<test output>` to `_steward_log.md`.
- On blocker: write question to `_steward_questions.md`, include file paths + error text, telegram L3 once.
- Progress chatter: none. Only slice-complete or blocker.

## Where viz fits in STATUS.md

Wiki steward adds a `## Viz track` section with:
- Current slice number + status
- Tests passing count
- Last commit sha
- Open slices remaining
