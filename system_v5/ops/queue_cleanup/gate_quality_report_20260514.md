# Gate Quality Report - 2026-05-14

Status: active gate-quality note for the v5 clean rebuild.

## Principle

Bounded exploration is not conservative exploration. The intended shape is many
branches under hard constraints: propose aggressively, keep failures visible,
and let evidence gates select without pretending early survivors are canonical.

## Gate Findings

| Gate | Current State | Quality | Repair |
|---|---|---|---|
| v4 probe write fence | `check_v5_rebuild_preflight.py` blocks staged v4 changes and dirty-state drift against `v4_probe_status_baseline_20260514.json` | stronger, useful | Refresh only through manifest-approved v4 cleanup batches. |
| provider proposals | JSON receipts under `formal_scouts/provider_receipts/` validate non-evidence status | stronger, useful | Keep Grok/Gemini/Sonnet outputs proposal-only until translated through repo callables. |
| formal-scout result validation | `validate_formal_scout_results.py` checks receipt fields and has `--fresh-rerun` | stronger, useful | Use fresh rerun before promoting any scout into a harder harness. |
| large generated inventories | preflight warns on staged files over 1 MB | useful but weak | Add path-specific deny/warn lists for generated result estates before evidence snapshots. |
| v4 probe corpus cleanup | inventory exists, but quarantine is not dry-run enforced | weak | Add one manifest dry-run path and no-reference-file selector check. |
| scout naming | `lint_formal_scout_names.py` blocks axis/engine/gstack/rosetta/type labels in formal-scout executable names | stronger, useful | Run before committing new formal-scout harnesses. |
| provider liveness | Grok and Sonnet have receipts; Gemini CLI is blocked by browser auth | honest but incomplete | Build direct Gemini API or keep Gemini blocked with closure criteria. |
| formal-scout gates | require receipt fields, graveyards, boundary, claim ceiling | good if not used as canonical proof | Do not block rough tower variants for lack of final physical graveyards; set low claim ceiling instead. |

## Too-Strict Risks

- Requiring full proof, unique layer order, or complete physical graveyards
  before formal scouts would kill useful tower exploration.
- Treating every rough manifold layer as a canonical claim would force excessive
  gate weight too early.
- Blocking provider proposals because they are not evidence would waste model
  diversity; the better gate is proposal-only receipts plus Codex grounding.

## Too-Weak Risks

- Letting new files enter `system_v4/probes` silently makes v4 unusable as a
  reference corpus.
- Letting elapsed-time-only result churn become commits creates noise without
  more evidence.
- Letting provider prose become a formal-scout receipt skips the real callable
  and no-hardcoding checks.
- Letting naming contamination enter new v5 executable names recreates the
  axis/engine/rosetta failure mode.

## Next Gate Work

1. Add a generated-artifact deny/warn table for result estates.
2. Add a v4 quarantine manifest dry-run for one generated family.
3. Add direct Gemini API receipt or keep Gemini CLI disabled with explicit
   closure criteria.
