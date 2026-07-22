# Fix patterns

The template library `claimgate_plugin/suggest.mjs` draws on. Each row: when
you see X (a gate finding's `code`), do Y, pointed at a real in-repo example.

This file is documentation only. It does not gate anything; `suggest.mjs`
reads the live rule/registry files at run time, so this table can drift
without breaking the tool — treat it as an index, and trust `suggest.mjs`'s
own output over this file if they ever disagree.

## Index: when you see X, do Y

| Finding code | Source gate | Do this |
|---|---|---|
| `classification_missing` / `classification_not_allowed` | `claimgate/claimgate.py` | Add `"classification"` from the live allowed set (`ALLOWED_CLASSIFICATIONS` in `claimgate/claimgate.py`) and `"promotion_allowed": false` unless canonical evidence genuinely exists. |
| `promotion_without_canonical_evidence` | `claimgate/claimgate.py` | Set `promotion_allowed: false`, or earn `accepted_status_label: "canonical by process"` for real — never flip the label to unblock. |
| `verdict_inflation` / `R1-verdict-inflation` | `claimgate/claimgate.py`, `claimgate.mjs` | Make `pass` agree with the verdict string, or add a >30-char `gate_miss_note` / `divergence_note` / `caveat` explaining the honest divergence. |
| `controls_missing` | `claimgate/claimgate.py` | Add a `"controls"` block with an independently computed sub-run. |
| `controls_copy_of_main_run` / `bc_scan_symmetry_forced` / `bc_scan_decorative_finite` | `claimgate/claimgate.py`, `bc_scan.py` | **Frozen-control pattern** — see below. |
| `negative_mutual_information` | `claimgate/claimgate.py` | Real correctness bug: fix the entropy sign convention in the computation, don't hide the field. |
| `preregistration_missing` / `R4-no-preregistration` / `R4-posthoc-gate` | `claimgate/claimgate.py`, `claimgate.mjs` | Add `"preregistered": [...]` listing the exact `checks` keys, before the run. |
| `R2-claim-without-evidence` | `claimgate.mjs` | Add a sibling field containing a provenance token (`raw`, `data`, `ci95`, `bootstrap`, ... — see `rules_ratchet.json`). |
| `R3-baseline-honesty` | `claimgate.mjs` | Add a sibling field containing a baseline token (`majority_baseline`, `null_mean`, `twin`, `chance`, ...). |
| `R5-recompute-*` | `claimgate.mjs` | Fix the raw array, the op, or the tolerance so the declared recompute contract genuinely reproduces the claim — never widen `tol` past 5% of `|claim|`. |
| `unclassified_claim_kind` | `claim_verify.py` | Add `"claim_kind"` from the live `gate_registry.json` `claim_kinds` keys. |
| `required_tier_unmet` | `claim_verify.py` | Run the named registry gate for the unmet tier, or accept exit 3 honestly if the receipt is genuinely a probe. |
| `tier4_prose_verdict` | `claim_verify.py` tier4 | **Honest classification token** — see below. |
| `tier4_no_auditor_identity` / `tier4_self_audit` / `tier4_not_calibrated` | `claim_verify.py` tier4 | Add `auditor: <name>` distinct from the producer, using a name in `gate_registry.json`'s `audit_policy.calibration_gates` (currently `honest`). |
| `smt_maybe_decorative` / a `TOOL_INTEGRATION_DEPTH` load-bearing SMT leg | static heuristic | **Genuine-mechanism SMT** — see below. |
| `floor_park_unknown_key` | `ratchet_floor.py` | **Floor-key registration** — see below. |
| `floor_regression` / `floor_direction_tamper` | `ratchet_floor.py` | No self-serve fix exists (design gap, Tier D). Route to the owner. |

## Template: genuine-mechanism SMT (vs. decorative)

The systemic finding (git `4fcd539d6`, `b12c0e8c7`): almost every z3/cvc5 leg
in this repo was the same generic single-valued-function tautology —
`recover(k) == A AND recover(k) == B -> UNSAT`, true for *any* `A != B`,
completely decoupled from the actual mechanism (partial trace, dephasing,
associativity, rank, sign). That pattern is `TOOL_INTEGRATION_DEPTH:
supportive`, never `load_bearing`, and needs an honest `smt_role` +
`load_bearing_evidence` field naming the real witness (the numpy/sympy
recompute that actually carries the arrow).

**Genuine template:** `ratchet_contract/ratchetings/magma_smt_genuine.py`.
It pins the *actual* magma table as 9 `z3.Function` constraints plus the
associativity congruence, so UNSAT genuinely depends on the table
(perturbing one entry flips the result; the unsat core is a subset of the
real constraints; erasing the table makes it SAT). That is what makes
`TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"` honest there.

If your SMT leg is the generic tautology: downgrade it —
```
"TOOL_INTEGRATION_DEPTH": {"z3": "supportive", ...},
"smt_role": "supportive_nonvacuity_only",
"load_bearing_evidence": "<name the real numpy/sympy witness here>"
```

## Template: discriminating control (vs. frozen)

The systemic control defect (same commits): `vn_to_shannon` and
`pure_to_vn`'s controls fed only *unitary, invertible* channels, so the
"is this recoverable" predicate could never flip — `BY_CONSTRUCTION` was
dead code. The fix is **feed-both-and-differ**: the same predicate must be
run against the real mechanism AND a genuinely different one, and must
disagree.

**Templates:**
- `ratchet_contract/ratchetings/vn_to_shannon.py` — dephasing/partial-trace
  (`one_way = True`) vs. a coherence-preserving unitary control
  (`one_way = False`); `control_discriminates = bool(dephasing_is_one_way and
  not control_is_one_way)`.
- `ratchet_contract/ratchetings/finite_to_continuum_rung.py` — lossy
  many-to-one discretization (`collapses = True`) vs. a lossless
  1-per-representative map (`collapses = False`).

A control that only ever agrees with the main run (`controls_copy_of_main_run`,
or a `bc_scan` `symmetry_forced` / `decorative_finite` name match) is the
same defect: rewrite it so it is fed a mechanism that genuinely differs, and
assert the predicate separates the two.

## Template: honest classification + promotion ceiling

Every receipt needs:
```
"classification": "<value from claimgate/claimgate.py's ALLOWED_CLASSIFICATIONS>",
"promotion_allowed": false
```
unless it has actually earned `canonical by process` (passes local rerun +
SIM_TEMPLATE + tool manifest + non-empty reasons + classification field —
see repo-root `CLAUDE.md`, "Status Labels"). `tool_lego_fit_probe` is the
correct default ceiling for pre-admission evidence: it must state
`promotion_allowed: false` and does not by itself satisfy canonical, bridge,
QIT, GStack, axis, or nonclassical admission.

## Template: floor-key registration

`ratchet_floor.py` already emits the exact fix inline when it PARKs an
unknown key — it names the nearest existing floor key (token-Jaccard >= 0.5)
so you can decide rename-vs-new:
```
python3 claimgate_plugin/ratchet_floor.py admit <receipt> --store <store> --allow-new-keys
```
Only use `--allow-new-keys` if the metric is genuinely new. If a
`nearest_existing_key` is reported, prefer renaming the `floor_claims` key to
match it over registering a near-duplicate floor.

## Not covered here: design gaps (Tier D)

`floor_regression` (a claim that weakens a locked floor) and
`floor_direction_tamper` (a claim that flips a locked direction) have **no
admissible receipt-level fix** today. `ratchet_floor.py` correctly rejects
both and offers no override — that is by design (constraints only tighten).
Closing this gap needs a new field (a logged `--allow-regression <reason>`
or a human-only floor reset), which is an owner decision, not something a
suggest layer can paper over. Route it.

## Ownership boundary

`suggest.mjs` and this file are read-only over every gate's output. They do
not edit, and must never be made to edit: `gate_registry.json`,
`gates_manifest.json`, `claim_verify.py`, `claimgate.mjs`,
`claimgate/claimgate.py`, `ratchet_floor.py`, `fixtures/`, or any
`AUDIT_VERDICT.md`. Those are the dual-tier0 (`claimgate/claimgate.py` +
`claimgate_plugin/claimgate.mjs`) and audit-token (`claim_verify.py` tier4)
contended surfaces, owned by their own sessions. If a fix genuinely requires
changing one of those files (a new override field, a relaxed check), that
change is routed there — `suggest.mjs` names the destination but does not
make the change itself.
