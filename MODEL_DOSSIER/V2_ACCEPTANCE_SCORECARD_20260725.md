# V2 architecture — measured scorecard against its own 25 acceptance tests

**Date:** 2026-07-25
**Subject:** `CR_FORMAL_ASSURANCE_AND_CLOUD_SCIENCE_ARCHITECTURE_V2_20260724.md`
**Method:** its §20 list is the best thing in it — 25 machine-testable conditions. Scored against HEAD, not against its audit point.
**Note:** V2 audited `fe9673568`. HEAD is **14 commits later**, so several of its P0s are already closed.

---

## 1. Where V2 corrects ME (both accepted)

| V2 correction | Verdict |
|---|---|
| **"Reactant.jl supplies a same-GPU independent Julia witness → REJECT as independence."** Reactant and JAX both lower to XLA; it is not an independent failure domain. | **V2 is right, I was wrong.** I called Reactant "the highest-value cloud addition" for supplying the mandatory second engine. It would supply a *second lane sharing one compiler backend* — precisely the shared-builder defect. Withdrawn. |
| **"PyG is the renesting machinery → DEMOTE."** PyG may learn/score rewrite proposals; authoritative typed rewriting belongs in Catlab/AlgebraicRewriting, Metatheory, Maude, Alloy. | **Accepted, and better than my version.** Catlab and Metatheory are *already installed* in this repo (project-local), so the authoritative rewrite lane is available now — PyG was never needed for validity, only for proposal ranking. |

Two further V2 refinements I adopt: **commit–challenge with Merkle sampling** instead of my blanket "every GPU number needs a CPU cross-check" (full CPU repetition of a large GPU run is often impossible), and **autograd differentiates the implemented float graph**, not the intended geometry.

---

## 2. Acceptance scorecard (25 tests)

| # | Test | State | Evidence |
|---|---|---|---|
| 3 | PyTorch-only numeric receipt rejected | **PASS** | `schedule_tournament_v0` REJECTS — single-engine numeric, no second witness |
| 8 | SMT tautology passes solver but fails semantic mutation | **PASS** | flip battery: real loop flip_rate **1.0**, commuting control **0.0** |
| 9 | Duplicate key rejected before object construction | **PASS** | `intake_supervisor.py`, raw-parse `object_pairs_hook`, any depth |
| 10 | NaN metric rejected | **PASS** | incl. `1e400→inf` and non-finite as dict value (red-team blind spots, closed) |
| 12 | Rotation preserves loop identity; reversal changes it | **PASS** | measured on the engine: rotation **2.2e-15**, reversal **6.4e-2**, adjacency **2.5e-3** |
| 21 | Missing required node parks or blocks | **PASS** | missing artifact → `BLOCKED_MISSING`, never N/A-ok |
| 22 | Valid negative preserved in Purgatory | **PASS** | `mss.frontier()` returns purgatory entries with exact failure + re-entry condition |
| 23 | LLM-written `all_pass: true` ignored or rejected | **PASS** | harness gate BLOCKS producer self-verdict |
| 25 | LevOS checkout byte-identical after bridge runs | **PASS** | `side_effect: read`; `lev-main` clean after every run this session |
| 2 | NumPy-hidden workhorse with JAX headers rejected | **PARTIAL** | seal rejects `numpy` as load_bearing; the *disguised* case (numpy computes, JAX header wraps) is untested |
| 6 | SAT counterexample refutes without invalidating the run | **PARTIAL** | `solver_sat_counterexample` fixture HOLDS; the five status axes are not yet separate fields |
| 11 | Metadata-only receipt cannot enter Ratchet | **PARTIAL** | `SEAL_METADATA_ONLY` still returns pass, not `TRANSPORT_OK` |
| 15 | Density-only run cannot claim history-pair coverage | **PARTIAL** | blindness *measured* (identical ρ_out, diff exactly 0.0) but no gate enforces the carrier type |
| 19 | Partial artifact cannot finalize | **PARTIAL** | transport canary has atomic finalization; not enforced repo-wide |
| 24 | LevOS claim without session/event evidence blocks | **PARTIAL** | `live_lev_consumed` distinction exists and is documented; not gated |
| 1 | Contained NumPy analysis runs, cannot change a verdict | **UNTESTED** | no numpy-satellite arrow wired to a claim |
| 5 | SAT existence witness accepted after replay | **UNTESTED** | no witness-replay path |
| 13 | Axis-6 sign mutation changes semantic digest | **UNTESTED** | no semantic digest over the EngineSpec yet |
| 16 | Stale cloud generation cannot overwrite newer | **UNTESTED** | no cloud lane |
| 18 | Forged GPU claim fails device evidence | **UNTESTED** | no GPU |
| 20 | Missing optional node allowed only when predeclared | **UNTESTED** | applicability registry not built |
| 4 | Invalid rewrite rejected by a deterministic kernel | **FAIL** | no rewrite kernel — the gap V2 correctly identifies |
| 7 | UNSAT with a broken proof is parked | **FAIL** | no proof production; cvc5 Alethe path absent |
| 14 | Nonassoc bracket mutation changes bracket-tree digest | **FAIL** | no bracket-tree digest anywhere |
| 17 | Cloud worker cannot predict the challenge | **FAIL** | no commit–challenge protocol |

**Tally: 9 PASS · 6 PARTIAL · 4 FAIL · 6 UNTESTED.**

---

## 3. V2's P0 repair ledger, re-scored at HEAD

| P0 repair | State |
|---|---|
| Strict duplicate/finite JSON parser | **DONE** — corpus went 7 HOLD/3 GAP → **10 HOLD/0 GAP**, no drift |
| Add TLA+ protocol estate | **PARTIAL** — 1 of its 6 named modules exists (`ClaimGateChain.tla`, chain control-flow), with exhaustive z3 + independent cvc5 |
| Remove hard-coded local Python path | **OPEN** — `SIM_PY = "/Users/joshuaeisenhart/..."` still at `three_engine_seal.py:31` |
| Replace global backend authority tuple | **OPEN** — `AUTHORITATIVE = (...)` still global |
| Remove `\|\| true` / `continue-on-error` | **OPEN** — still in `ci.yml` |
| Demote metadata-only pass to `TRANSPORT_OK` | **OPEN** |
| Fix SMT polarity | **PARTIALLY OUTDATED CRITICISM** — the hostile fixtures already carry `m1_status`/`m1_polarity` pairs, and my formal lane is per-obligation (REAL→UNSAT, ERASED→SAT). What is genuinely missing is V2's **obligation envelope registry** with declared `polarity` + `expected_status` per call. That part is a fair call. |

---

## 4. What to build next, ordered by measured value

1. **Freeze the EngineSpec with a semantic digest** over `cycle_identity` (canonical oriented cycle modulo rotation) + `run_coordinate` {start_stage, direction, initial_state}. Test #12 already passes on the engine; this makes it enforceable rather than incidental. Unblocks #13.
2. **Deterministic rewrite kernel on Catlab/Metatheory** — both already installed. Unblocks #4 and the renesting test that has been unrunnable.
3. **Obligation envelope registry** (`polarity`, `expected_status`, `witness_schema`, mutation controls per solver call) — makes SAT/UNSAT meaning explicit rather than conventional.
4. **cvc5 proof production + independent checker** — unblocks #7, converts trusted UNSAT into checked UNSAT.
5. **The three cheap OPEN P0s**: resolve the interpreter from the sealed env and hash it; cap metadata-only at `TRANSPORT_OK`; split CI into gating vs informational jobs.
6. **Bracket-tree digest** for the nonassociative lane — unblocks #14, and pairs with the GPU-reassociation hazard both documents flag.

---

## 5. The gap all three documents now name and none has closed

**A shared builder can satisfy two witness roles.** V2 states it (§15 "shared-builder false independence"), the AR01 covert-cheat audit stated it (CHEAT-001), and my synthesis stated it. It remains unbuilt, and V2's Reactant correction sharpens it: sharing a *compiler backend* is the same defect as sharing a result builder.

Required: each lane receives only the frozen contract and raw fixture — never executable decisive common code; asymmetric mutation (mutate one lane → only that lane changes); dependency-kill (kill a lane → it fails, no fallback); decisive-overlap classified `schema-only | fixture-only | decisive`; plus a hand-derived exact-small oracle for the common-mode case where two lanes independently implement the *same wrong equation*.

`promotion_allowed: false` throughout.
