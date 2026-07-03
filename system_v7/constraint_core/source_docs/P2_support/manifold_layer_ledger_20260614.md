# Manifold Layer Ledger (DRAFT)

ASSISTANT-GLOSS: status: DRAFT. claim_ceiling: doctrine draft, no admission of anything.
This ledger is the campaign instrument's tracking table, NOT a result. One row per canonical layer
(Part A of `manifold_layer_order_and_completeness_contract_20260614.md`); columns = the contract boxes
(Part B). Seeded with CURRENT real state read from result JSONs this session. Most boxes are empty by
design — this is the honest state, not a target picture. Trust the result-JSON over any verdict prose.

LADDER LABELS (never collapse): `exists` < `runs` < `passes local rerun` < `canonical by process`.
A layer is DONE only when every contract box is checked WITH a cited artifact path, INCLUDING the
fresh-context audit (box viii). No row below is DONE.

CONTRACT-BOX COLUMNS (from Part B):
- i  = max sim-set enumerated (template-derived, classification, manifest, >=1 load-bearing tool)
- ii = positive + boundary tests populated
- iii= ALL the negatives genuinely fire (the 12-falsifier roster)
- iv = qubit-ladder depth to useful + one beyond
- v  = passes the full axiom-grounded gate stack
- vi = nested via compatibility law + extension fibers computed
- vii= section-5 predicted-modification forecast recorded AND checked
- viii=fresh-context audit (builder != auditor)
- ix = nesting-law queue position recorded
- box (x/xi/xii) status-label honesty / claim-ceiling fields / stage-gate position are checked per-row in prose.

Legend: `Y` = checked with cited artifact; `P` = partial (computed but not at full scope / not all rungs);
`-` = empty / not done; `N/A` = does not apply at this layer's current rung.

---

## CURRENT REAL STATE — two running sims seed the bottom of the tower

Read this session from the result JSONs (NOT from verdict prose):

1. `system_v7/sims/distinguishability_quotient_floor_v0/` — the probe-quotient floor (L1), 1q only.
   - Result JSON classification: **`scratch_diagnostic`**, `promotion_allowed: false`, `formal_admission_allowed: false`.
     (DIVERGENCE flagged: the campaign-seed text called this "GOLD"; the actual result JSON says
     `scratch_diagnostic`. Per the kernel rule "trust result-JSON over verdict prose," the JSON wins; the
     row below is seeded `scratch_diagnostic`.)
   - Ladder reached: `passes local rerun` (Julia + JAX + PyTorch + agreement check ran to exit 0; three
     engines agree; SMT flip z3=`sat`/`unsat`, cvc5=`sat`/`unsat` confirmed; autograd identity ok).
   - 1q-only -> NOT valid alone for any multi-qubit claim (box iv ladder gate); honest as a non-validity
     `scratch_diagnostic`.
   - Artifacts: `.../results/distinguishability_quotient_floor_v0_jax_results.json`,
     `..._julia_results.json`, `..._pytorch_results.json`, `..._agreement_results.json`, `spec.json`.

2. `system_v7/sims/finite_probe_quotient_inverse_limit_tower_1q_through_4q/` — the inverse-limit tower,
   1q through 4q. THIS is the running foundation-tower sim that exercises L1, L2, L5, L8, L9, L10, and the
   compatibility law / extension fibers (box vi) and the section-5 forecast (box vii) at depths up to 4q.
   - Agreement-result JSON: classification `scratch_diagnostic`, `promotion_allowed: false`,
     `formal_admission_allowed: false`, `does_not_self_upgrade: true`.
   - Ladder reached: `passes local rerun` (all three engines ran to exit 0 and agree; `all_three_agree: true`).
   - Per-rung quotient counts (full/erased): 1q 5/5, 2q 10/8, 3q 10/9, 4q 5/5. Erasing pairwise `ZZ` merges
     `mix_00_11`+`maxmix_2` (2q) and `mix_000_111`+`maxmix_3` (3q) — the load-bearing quotient flip.
   - SMT flip (load-bearing, not a count tautology): z3 `sat`->`unsat`, cvc5 `sat`->`unsat`, confirmed.
   - Compatibility: `tower_self_seals: true`, `one_beyond_self_seals: true` (computed partial traces, not
     label echo, per the audit verdict's own flip condition).
   - Forecast (section-5): `forecast_matches_computed` true at 1q/2q/3q/4q with computed evidence (Bloch
     radii at 2q; rank tuples `[1,1,1]`/`[1,2,2]`/`[2,2,2]` at 3q; rank-tuple lattice at 4q).
   - Declared `ladder_useful_depth: 3q`, `ladder_one_beyond: 4q`.
   - OPEN: box (viii) — the `audit_verdict.md` is the BUILD'S OWN self-assessment (`does_not_self_upgrade:
     true`); a fresh-context audit is NOT yet run. Box (v) gate-stack run not yet recorded against this packet.
   - Artifacts: `.../results/..._agreement_results.json`, `..._julia_results.json`, `..._jax_results.json`,
     `..._pytorch_results.json`, `spec.json`, `audit_verdict.md`.

---

## THE LEDGER

| # | Layer | i | ii | iii | iv | v | vi | vii | viii | ix | Ladder label | Missing boxes (named) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Probe-quotient floor `S/~_M` | Y | P | P | N/A | P | P | N/A | - | Y | passes local rerun | iii (full 12-roster: only SMT-flip + autograd present; product-negativity / perturbed-marginal / scrambled-pin / alt-probe-family / lineage-removed / value-coupled-geometry not run for the floor), ii (boundary section thin), v (full gate stack not run against this packet this session), viii (fresh-context audit) |
| 2 | Density-rank strata + partial-trace marginals | Y | P | P | P | P | Y | N/A | - | Y | passes local rerun | iii (perturbed-marginal-FAILS, alternate-probe-family, lineage-removed not all recorded as firing), v (gate stack not run), viii (fresh audit) — covered by the inverse-limit tower at 2q+ |
| 3 | Spinor / phase / projective + local Hopf skeleton | P | - | - | - | - | - | - | - | Y | runs | ii, iii, iv, v, vi, vii, viii — only the 1q pure-state Bloch radius is computed (in the tower); no standalone Hopf-skeleton packet |
| 4 | Local Weyl factors (product states only) | - | - | - | - | - | - | - | - | Y | not started | all (i-viii) — no packet; section-5 product-only restriction not yet exercised |
| 5 | Nested tori -> marginal-radius shells + Schmidt strata (section-5 modified) | P | - | P | P | - | Y | Y | - | Y | passes local rerun (forecast-check only) | i (standalone packet), ii, iii, v, viii — the tower CHECKS the forecast (box vii Y: shells at 2q, Schmidt strata at 3q, rank-tuple lattice at 4q) but no standalone shells/strata layer packet |
| 6 | Metric layer restricted to survivors + induced `G_A` | - | - | - | - | - | - | - | - | Y | not started | all — `InducedGeometry` recompute-on-survivors not yet built as a packet |
| 7 | Connections / curvature / FLUX (geometric feedstock) + lift-erasure | - | - | - | - | - | - | - | - | Y | not started | all — feedstock only; no v7-era runtime packet |
| 8 | The cut lattice (`2^{n-1}-1` bipartitions) | P | - | - | P | - | P | N/A | - | Y | passes local rerun (implicit) | i (standalone), ii, iii, v, viii — cuts are implicit in the tower's Schmidt strata at 3q/4q; no dedicated cut-lattice packet |
| 9 | Schmidt strata per cut | P | - | - | P | - | Y | Y | - | Y | passes local rerun (in tower) | i (standalone), ii, iii, v, viii — computed in the tower (rank tuples at 3q/4q); not a standalone layer packet |
| 10 | Entropy per cut availability (`S_A`, `S_AB`, `I_AB`, ...) | P | - | - | P | - | P | N/A | - | Y | passes local rerun (partial) | i (standalone), ii, iii (entangled-vs-separable divergence roster), v, viii — von Neumann entropy computed per rung in the tower; `I(A:B|C)` and the full per-cut availability table not a standalone packet |
| 11 | Channels / flows / 16 ordered maps + order/noncommutation matrix | - | - | - | - | - | - | - | - | Y | not started | all — no map-library/order-matrix packet |
| 12 | Region discovery from observables | - | - | - | - | - | - | - | - | Y | not started | all — no region-discovery packet (FORK 3: terrain-family vs direct-from-observables unresolved) |
| 13 | Flux-fate (runtime/QIT flux) | - | - | - | - | - | - | - | - | Y | not started | all — needs nesting + multi-qubit depth (FORK 4: feedstock vs runtime flux unresolved) |
| 14 | The runner / QCA + finite trajectories | - | - | - | - | - | - | - | - | Y | not started | all — FORK 5: QCA in base build vs deferred surface substrate unresolved |
| 15 | `Cl(2n)` + chirality projectors `P_L/P_R` | - | - | - | - | - | - | - | - | Y | not started | all — no Clifford/chirality packet at v7 |
| G1 | The G2 layer | - | - | - | - | - | - | - | - | Y | DEFERRED | LICENSE NOT MET: needs explicit 7D `W_A` + pinned 3-form `phi` + the four tests |
| G2 | SU(3) = `Stab_G2(u)`, `G2/SU(3)=S^6` | - | - | - | - | - | - | - | - | Y | DEFERRED | LICENSE NOT MET: G1 must be licensed first |
| G3 | Spin(7) via Cayley form | - | - | - | - | - | - | - | - | Y | DEFERRED | LICENSE NOT MET: needs the 8D extension |
| G4 | Spin(8) triality | - | - | - | - | - | - | - | - | Y | NAMED, NOT SCHEDULED | LICENSE NOT MET: needs the three maps `8v->8s->8c->8v` |
| G5 | F4 = `Aut(J3(O))` | - | - | - | - | - | - | - | - | Y | NAMED, NOT SCHEDULED | LICENSE NOT MET: needs the 27D Jordan target `J` |
| G6 | split `G2(2)` + sedenion zero-divisor boundary (controls) | - | - | - | - | - | - | - | - | Y | NAMED, NOT SCHEDULED | LICENSE NOT MET: run as controls for G1-G5, not promoted |

---

## Per-row notes (honest scope, the open boxes)

- **L1 (probe-quotient floor).** Strongest current row. The standalone floor sim (`distinguishability_
  quotient_floor_v0`) is 1q-only `scratch_diagnostic` at `passes local rerun`; its load-bearing evidence is
  the real-vs-erased SMT flip (negative roster item 6) + three-engine agreement + autograd identity. The
  OTHER negatives on the 12-roster (product-state-negativity-zero, perturbed-marginal-fails, scrambled-pin,
  alternate-probe-family beyond the single Z-erasure, lineage-removed, value-coupled-geometry) are NOT all
  recorded as firing for the floor packet -> box (iii) is PARTIAL. Box (viii) fresh audit OPEN.

- **L2 / L5 / L8 / L9 / L10 (covered by the inverse-limit tower at 2q-4q).** The tower
  (`finite_probe_quotient_inverse_limit_tower_1q_through_4q`) is the running foundation-tower sim and is the
  reason these rows are not all empty. It computes: the compatibility law with `tower_self_seals: true` and
  extension fibers (box vi Y for L2); the section-5 forecast checked against computed geometry at every rung
  (box vii Y for L5); Schmidt strata / rank tuples at 3q-4q (L9); von Neumann entropy per rung (L10, partial).
  Its ladder is declared useful=3q, one-beyond=4q (box iv). But: box (iii) full negative roster is NOT
  complete (only the SMT flip + the ZZ-erasure probe swap fire; product-negativity, perturbed-marginal-fails,
  lineage-removed, value-coupled-geometry are not all recorded as firing); box (v) the axiom-grounded gate
  stack is NOT yet run against this packet this session; box (viii) the `audit_verdict.md` is the BUILD'S OWN
  self-assessment (`does_not_self_upgrade: true`) -> a fresh-context audit is OPEN.

- **L3 (spinor/Hopf skeleton).** Only the 1q pure-state Bloch radius surfaces (inside the tower). No
  standalone Hopf-skeleton packet -> `runs`-level at best as a standalone object; most boxes empty.

- **L4, L6, L7, L11-L15.** Not started at v7. No packet. Honest label: `not started`.

- **L13, L14 carry unresolved FORKS** (feedstock-vs-runtime flux; QCA-in-base vs deferred surface) per the
  contract's noted-fork list. Do not start these on the strength of L1/L2 being strong (stage-gate, box xii).

- **G1-G6 (gated/deferred).** No packet is permitted until each one's explicit LICENSING OBJECT exists
  (box ix in the contract). All rows DEFERRED / NAMED-NOT-SCHEDULED; box (ix) queue position is the only Y.

---

## Tower-completeness honesty statement

NO row above is DONE (`canonical by process`). The two strongest rows (L1; and L2/L5/L9 via the tower) reach
`passes local rerun` with three-engine agreement and a load-bearing SMT flip, but every one of them has box
(viii) fresh-context audit OPEN and box (iii) full-negative-roster INCOMPLETE, and box (v) gate-stack not run
this session. Per the binding stage-gate order, the lego stage is NOT complete, so NO coupling / coexistence /
bridge / axis work is licensed. "Done at the 1q/2q-4q rung of the foundation tower" is NOT "the tower is
complete" (box ix). This ledger is a DRAFT campaign instrument; it admits nothing.
