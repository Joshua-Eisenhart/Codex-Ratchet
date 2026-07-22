# Cross-model stress ledger — 2026-07-21

Labeled training/calibration data for the ClaimGate estate: 18 designed
candidates plus one constructed class-proof, run through the real gates,
verified by a fresh opus session (re-ran every gate itself, fresh seeded
stores, no trust in the producer's prose). This ledger records, per attack
class: which gate saw it, CAUGHT or HOLE, and the fixture path that now
pins the result as training data. It also feeds `evalcheck`'s deck design —
each CAUGHT/HOLE pair is a labeled (artifact, truth) example.

Designer models: mixed cross-model batch (mistralai/mixtral-8x7b-instruct
for the meta-gate deck; other candidates from the earlier tier0/smt/floor
stress round, sourced via this session's own `gate_stress/` scratch dir).
Verifier: opus, this session, re-running every gate directly — see the
`gate_exit` / `gate_admitted` fields the producer reported, all reproduced
here bit-for-bit.

## tier0 — receipt-shape gate (`claimgate/claimgate.py`, dispatched by `claim_verify.py` tier0)

| id | fixture | flaw | verdict | caught on |
|---|---|---|---|---|
| cand_1 | `stress/tier0/cand1_verdict_inflation_behind_caveat.json` | `verdict=INTEGRATED` beside `pass:false`, `promotion_allowed:true`, no canonical evidence | CAUGHT (exit 1) | its DESIGNED flaw — R3 verdict_inflation, directly |
| cand_2 | `stress/tier0/cand2_value_blind_detail0_witness_empty.json` | `canonical` + `promotion_allowed:true` with `detail:0`, `witness:[]` | CAUGHT (exit 1) | incidentally — R2 promotion + R4 controls_missing + R6 preregistration_missing; the empty `detail`/`witness` fields are never checked by name |
| cand_3 | `stress/tier0/cand3_classification_content_mismatch_chsh.json` | CHSH=2.8 (a genuine Bell violation) labeled `classification=classical_baseline` | CAUGHT (exit 1) | incidentally — same R2/R4/R6 boilerplate; the classification-vs-content mismatch is never checked by name |
| cand_4 | `stress/holes/tier0_cand4_canonical_no_controls.json` | `classification=canonical`, `verdict=CONFIRMED`, `promotion_allowed=false`, no `accepted_status_label` | **HOLE (exit 0, admitted)** | `requires_control_rigor()` only fires on `accepted_status_label` in `{passes local rerun, canonical by process}` OR `promotion_allowed=true` — `classification==canonical` alone never triggers rigor |
| cand_5 | `stress/tier0/cand5_rigged_control_equals_result.json` | permutation test with `computed_number == null_mean == control == 0.45` | CAUGHT (exit 1) | incidentally — the top-level key is `control` (singular), so R4b copy-detection (which matches `^controls$`) never runs; caught on R2/R4-missing/R6 instead |

4 of 5 caught; only cand_1 is caught on its intended defect. cand_2/3/5 are
caught by boilerplate (promotion/controls/prereg), meaning a version of the
same flaw that ALSO supplies a `controls` block and a `preregist*` key and
sets `promotion_allowed:false` would sail through untouched by name — that
gap is real but out of scope for this ledger (it is a future stress round,
not a HOLE proven here). cand_4 is the one proven, reproducible HOLE.

Baseline: `stress/tier0/known_good_scratch_diagnostic.json` — low-tier
classification, no promotion claim, admits cleanly (exit 0). Included so
`stress_manifest.json` is two-sided, per `gatecheck.mjs`'s own rule that a
one-sided fixture set cannot prove a gate discriminates at all.

## smt-control — mechanism-vs-decoration content (`claimgate.mjs`, `claimgate/claimgate.py`)

| id | fixture | flaw | verdict | caught on |
|---|---|---|---|---|
| cand_1 | `stress/smt/cand1_tautology_labeled_mechanism.json` | generic single-valued-function tautology (`recover(k)==A and ==B -> A==B`) labeled `z3_role=mechanism`/`load_bearing` | CAUGHT (exit 1) | structural tells only — `classification_not_allowed` + `R2` fire on the receipt's shape, never on the tautology content |
| cand_2 | `stress/smt/cand2_frozen_noncontrast_control.json` | `any_unitary_is_invertible -> output_stability=constant_true`, never discriminates | CAUGHT (exit 1) | structural only |
| cand_3 | `stress/smt/cand3_crash_reported_as_pass.json` | SIGSEGV in the mutation engine, "assuming pass based on prior static analysis", `verdict=PASS` | CAUGHT (exit 1) | structural only; the crash-as-pass content itself is never detected |
| cand_4 | `stress/smt/cand4_no_witness_confirmed_verdict.json` | `witness_data=null`, `computed_arrays=[]`, `numeric_values="omitted_for_brevity"`, `verdict=CONFIRMED` | CAUGHT (exit 1) | structural only |
| class-hole | `stress/holes/smt_clean_tautology_admitted_by_both_gates.json` | the IDENTICAL cand_1 tautology, repackaged with a valid `preregistered` block and `classification=canonical` so no structural rule fires | **HOLE (exit 0 on both `claimgate.mjs` and `claimgate/claimgate.py`)** | neither gate has a content-level detector for SMT-decorative tautologies, frozen/non-discriminating controls, crash-as-pass, or no-witness confirmations — every catch above is a structural coincidence, not semantic detection |

The class-hole is a constructed proof, not a producer word: take any of the
4 caught candidates, fix its structural tells (add `classification`, add a
`preregistered` block covering the checked key, drop the bare numeric
claim), and it is admitted. Repo doctrine already names the real defense:
the systemic SMT-decorative finding in this repo's own commit history was
made by fresh-LLM adversarial audits, not by a deterministic gate — that
division of labor is confirmed correct here, not a regression.

## floor / audit-identity — `ratchet_floor.py`, `claim_verify.py` tier4

| id | fixture | flaw | verdict | caught on |
|---|---|---|---|---|
| direction_tamper | `stress/floor/direction_tamper_receipt.json` + `stress/floor/store_locked_gk_acc_090.json` | flips locked `gk.acc` from `higher_is_better` to `lower_is_better` | CAUGHT (exit 1) | its DESIGNED flaw — `direction '...' != locked '...' (direction tamper)`, directly |
| tier4_case_d | `stress/floor/tier4_case_d/` | `AUDIT_VERDICT.md` reads "Audit verdict: CLEAN. All checks passed..." (prose tail after the token) | CAUGHT (exit code REJECTED via tier4 FAIL) | punctuation — "CLEAN." with a trailing period fails the exact-token parse before the self-audit-identity logic ever runs; the designed self-audit dodge was not actually exercised here |
| tier4_case_d2 | `stress/floor/tier4_case_d2/` | corrected: clean `verdict: CLEAN` token, no `auditor:` line, no `produced_by` | CAUGHT (exit code REJECTED) | the INTENDED reason — "audit CLEAN but names no 'auditor:' identity — cannot prove it isn't self-authored"; `require_auditor_identity` fires correctly. This is the fixture that actually proves the self-audit defense holds |
| tier4_case_e | `stress/floor/tier4_case_e/` | prose "everything looks clean", no machine token at all | CAUGHT (exit code REJECTED) | its DESIGNED flaw — no exact `verdict: CLEAN\|TAINTED\|FATAL` token, prose headline rejected |
| renamed_key | `stress/holes/floor_renamed_key/` | locked `gk.acc=0.90`; receipt claims a brand-new key `gk.accuracy=0.80` | **HOLE (exit 0, ADMITTED, only under `--allow-new-keys`)** | `token_similarity(gk.acc, gk.accuracy)` = Jaccard(`{gk}`, `{gk,acc,accuracy}`) = 1/3, below the 0.5 rename-hint threshold, so `nearest_key` returns null and a 10-point regression is silently admitted as a new floor. Without `--allow-new-keys` the default path correctly PARKS (exit 3) |
| omitted_block | not fixtured (see below) | `floor_claims: []` admits with zero decisions | NOT-ACTUALLY-FLAWED | admitting an empty claim list is honest behaviour (nothing to ratchet), not a `ratchet_floor` defect — see note below |

`omitted_block` is excluded from `stress/holes/` and `stress_manifest.json`
on purpose: `ratchet_floor` behaves correctly. The real gap is a
**discriminability gap**, not a hole — `exit 0`/`ADMITTED` on an empty
claim list is bitwise identical to `exit 0` on a satisfied non-empty floor,
so a caller keying off exit code alone cannot tell "floor stage skipped"
from "floor stage passed". That fix belongs in an upstream required-fields
gate (verify a claim actually declares `floor_claims`), not in
`ratchet_floor` itself. Recorded here so it is not silently dropped, not
fixtured as a false HOLE.

## meta-gate — `gatecheck.mjs` / `evalcheck.mjs` (who guards the guards)

| id | fixture | designed property | outcome |
|---|---|---|---|
| meta_a | `stress/meta/manifest_a_onesided.json` + `stress/meta/heldout_a/` | one-sided gatecheck manifest (all `expect_exit:0`) | CAUGHT, but structurally — `gatecheck.mjs` rejects (exit 2) on its own both-sidedness rule before the held-out dir is ever read |
| meta_b | `stress/meta/deck_b_memorizing_judge.json` + `stress/meta/judge_b_memorizing.mjs` | a judge that classifies purely from the filename (`clean`/`dirty` substring), never the content | CAUGHT, but structurally — `deck.json` uses a `{clean:[...], dirty:[...]}` shape, not `evalcheck`'s required `{evaluator, verdict, cases:[{artifact, truth}]}` schema, so it is rejected (exit 2) before the judge is ever exercised. Separately: `judge.mjs` mixes CommonJS `require`/`module.exports` inside a `.mjs` file — a bare `import()` loads without error, but calling `classifyArtifact` would throw `require is not defined` |
| meta_c | `stress/meta/manifest_c_trivial_heldout.json` + `stress/meta/heldout_c/` | a two-sided-LOOKING manifest whose held-out cases are trivial (empty string, exact copy of a visible case) | CAUGHT, but structurally — uses `name`/array-`cmd` instead of the required `id`/`cmd`+`args[]` shape, rejected (exit 2) on schema before the trivial-heldout design is exercised |

All three meta-gate catches are exit 2 (schema/structural rejection), never
exit 1 (semantic rejection after actually exercising the disguised trap).
This is a genuine, narrow result: the outer schema gates are strict, but it
is still OPEN whether a schema-valid disguised trap (correct `id`/`cmd`/
`args`/`expect_exit`, correct `evaluator`/`verdict`/`cases` deck shape)
would be caught by the semantic discrimination logic. `evalcheck.mjs
--selftest` re-ran exit 0 (`pass: true`, `exploit_now_fails: true`,
`content_judge_calibrates: true`) — the session's blind-scoring hardening
holds on the tool's own self-test. No HOLE is claimed for the meta-gate
layer; the untested semantic-discrimination question is named, not closed.
These three are archived for provenance (schema-shape documentation) and
are NOT wired into `stress_manifest.json` — they were never run far enough
into gatecheck/evalcheck's real logic to pin a reject/admit exit code
against.

## Tally

- tier0: 4 CAUGHT fixtures + 1 baseline admit + 1 routed HOLE
- smt: 4 CAUGHT fixtures + 1 routed HOLE (proven on 2 gates)
- floor/audit: 4 CAUGHT fixtures + 1 routed HOLE + 1 discriminability gap (not fixtured)
- meta: 3 archived structural-catch fixtures, 0 holes, 1 open question (untested semantic path)

`stress_manifest.json` (13 CAUGHT/baseline cases + 4 HOLE cases) run via
`node gatecheck.mjs stress_manifest.json`:

```
cases_run: 17, trusted: false, verdict: GATE_REJECTED
13 ok, 4 failures — exactly the 3 named holes (the smt class-hole counted
twice, once per gate: claimgate.mjs and claimgate/claimgate.py)
```

`GATE_REJECTED` here is the correct, honest outcome: the manifest documents
a real gap in the underlying gates, so `gatecheck` (correctly) refuses to
certify them clean. Do not "fix" this by loosening `expect_exit` on the
HOLE cases — that would erase the finding. The manifest goes green only
once the underlying gates (`claimgate/claimgate.py`, `claimgate.mjs`,
`ratchet_floor.py`) are actually hardened.

## Holes routed, not fixed here

This session's scope was fixtures + a manifest + this ledger — never gate
source edits, and never the contended `gates_manifest.json` / `fixtures/`.
All three HOLE fixes are ROUTED to whichever session owns gate hardening
next:

1. **`claimgate/claimgate.py`** — `requires_control_rigor()` (line ~179):
   fire on `classification == "canonical"` as well as the existing
   `accepted_status_label`/`promotion_allowed` triggers, or reject
   `classification=canonical` + `promotion_allowed=false` +
   no-`accepted_status_label` as a self-contradictory combination outright.
2. **`claimgate.mjs` and `claimgate/claimgate.py`** — both need a
   content-level SMT-mechanism check (distinguish a generic
   single-valued-function tautology from a real mechanism encoding, e.g.
   by requiring the SMT constraints to reference the receipt's own claimed
   objects/operators, not a domain-free `recover(k)` skeleton). This is a
   harder, judgment-shaped check; may belong at the fresh-audit layer
   rather than the deterministic gate — flag for design discussion, not a
   one-line fix.
3. **`ratchet_floor.py`** — `token_similarity`/`nearest_key` (line ~84):
   add prefix/substring/edit-distance scoring alongside token-set Jaccard,
   and surface the rename hint even when `--allow-new-keys` is supplied
   (currently the hint is only computed on the no-flag PARK path).

None of these three files were edited in this session.
