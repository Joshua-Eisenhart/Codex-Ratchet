# Hole fixtures — one-line notes

Each fixture below is a genuinely flawed receipt or floor-claim that a gate
wrongly admitted. Designer: cross-model batch, opus verifier (2026-07-21),
receipts recovered from this session's scratchpad `gate_stress/`. See
`../CROSS_MODEL_STRESS_LEDGER.md` for full detail and repro commands.

- `tier0_cand4_canonical_no_controls.json` — should be caught by
  `claimgate/claimgate.py` (`requires_control_rigor`), which gates controls
  and preregistration only on `accepted_status_label` in
  `{passes local rerun, canonical by process}` OR `promotion_allowed=true`.
  `classification=canonical` alone does not trigger rigor, so
  `promotion_allowed=false` + no `accepted_status_label` dodges both checks
  even though `verdict=CONFIRMED`. Currently admitted, exit 0.

- `smt_clean_tautology_admitted_by_both_gates.json` — should be caught by
  `claimgate.mjs` and/or `claimgate/claimgate.py` (a content-level SMT check
  neither one has). This is the identical single-valued-function tautology
  (`recover(k)==A and ==B -> A==B`, labeled `z3_role=load_bearing`) from
  `../smt/cand1_tautology_labeled_mechanism.json`, repackaged with a valid
  `preregistered` block and `classification=canonical` so no structural rule
  fires. Currently admitted by both gates, exit 0 each.

- `floor_renamed_key/` (`receipt.json` + `store_seed.json`) — should be
  caught by `ratchet_floor.py`'s `nearest_key` rename hint. Locked floor is
  `gk.acc=0.90` (`store_seed.json`); the receipt claims a new key
  `gk.accuracy=0.80`. Token-set Jaccard on `{gk}` vs `{gk,acc,accuracy}` is
  1/3, below the 0.5 threshold, so the hint returns null and — only when a
  human passes `--allow-new-keys` — a 10-point regression is silently
  admitted as a brand-new floor with no rename warning. Without the flag the
  gate correctly PARKS (exit 3); the hole is specific to the flag path.
