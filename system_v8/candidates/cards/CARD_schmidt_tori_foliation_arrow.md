# BUILD CARD — schmidt_tori_foliation_arrow

Proposal-sim card (cr-ratchet, stage-5). Standard finite math only. No coined terms.
Ceiling: `classification = "tool_lego_fit_probe"`, `promotion_allowed = false`,
`ordering_status = "PROPOSED not canon"`.

## Goal

Add the geometry rung directly above `pure_to_vn` and `bures_to_fubini_study`:
the Hopf/Schmidt torus foliation of `S^3`, with the entanglement entropy of the
torus-orbit average as an exact function of the Schmidt latitude `eta`. Prove
that the leaf structure `{T_eta}` is an exact entropy level-set system and that
the orbit-average map that produces it is one-way (forgetting the fiber
coordinates `phi, chi`). This is the geometric extension of "VN born at the cut"
onto the documented torus stratum, and it exposes a second, distinct
non-injectivity: the `eta <-> pi/2 - eta` fold at the Clifford torus.

## Per-rung formal objects

| Rung | Formal object | Equation | Doc citation |
|---|---|---|---|
| carrier | normalized spinor carrier | `S^3 = { psi in C^2 : ||psi|| = 1 }` | atlas §3.1 rung 6 |
| spinor chart | Hopf coordinates | `psi_s(phi,chi;eta) = [e^{i(phi+chi)}cos eta, e^{i(phi-chi)}sin eta]^T`, `eta in [0,pi/2]` | atlas §3.2, AXIS0 doc L1020-1026 |
| leaf | torus stratum | `T_eta = { psi_s(phi,chi;eta) : phi,chi in [0,2pi) } subset S^3` | atlas §3.1 rung 9, §3.3 |
| distinguished leaf | Clifford torus | `T_(pi/4)` (`eta = pi/4`) | atlas §3.1 rung 10, §3.3 |
| orbit average | chi-average of the pure density | `rho_bar(eta) = (1/2pi) int_0^{2pi} rho(chi,eta) dchi = diag(cos^2 eta, sin^2 eta)` | atlas §5.1 |
| entropy readout | leaf entropy | `S(eta) = -cos^2 eta log cos^2 eta - sin^2 eta log sin^2 eta = h(cos^2 eta)` | atlas §5.1 |
| Schmidt tie | reduced state of `cos eta|00>+sin eta|11>` | `rho_A = diag(cos^2 eta, sin^2 eta)`, `S(rho_A) = h(cos^2 eta)` (identical readout) | atlas §5.1 (rho_bar form); Schmidt link PROPOSED-not-documented (standard) |
| hemisphere sign | discrete threshold | `b_0 = sign(cos 2eta) = sign(r_z)` | atlas §5.2 |

## The arrow(s) to gate

1. LEAVES ARE EXACT ENTROPY LEVEL SETS. On a fixed `T_eta` the entropy `S(eta)`
   is constant across all `phi, chi` (the orbit average kills the off-diagonal),
   so `S` is a first integral of the foliation. Witness: sample many
   `(phi, chi)` on one `T_eta`, recompute `S(rho_bar)` — max spread `< TOL`.
2. ORBIT-AVERAGE IS ONE-WAY (fiber forget). `rho_bar(eta) = diag(cos^2 eta,
   sin^2 eta)` loses `phi, chi`. Load-bearing witness: two spinors on the same
   `T_eta` with distinct `(phi,chi)` map to the identical `rho_bar` — the map
   `T_eta -> rho_bar(eta)` is non-injective, no inverse.
3. FOLD NON-INJECTIVITY (the new tooth vs pure_to_vn). `S(eta) = h(cos^2 eta)`
   is symmetric under `eta <-> pi/2 - eta` (`h(cos^2) = h(sin^2)`), so
   `eta -> S` is 2-to-1 on `[0, pi/2]`, folding at the Clifford torus
   `eta = pi/4` where `S` is maximal (`= log 2`). The Schmidt latitude is NOT
   recoverable from the entropy alone — the hemisphere sign `b_0` is the
   independent coordinate that resolves the fold. This is a distinct one-way
   loss from the phase-forget in (2).

Expected verdict: `RATCHETED_ONE_WAY` on (2), with (3) reported as a second,
independent non-injectivity (fold), (1) as the exact level-set fact.

## Rivals / controls

- GENUINE control (must stay invertible): the base loop `gamma_base` motion at
  fixed `eta` (atlas §3.4) traverses distinct `rho` on the Bloch sphere — a
  non-averaged path where the Bloch point IS recovered. Contrast with the
  averaged fiber orbit that is not. `control_is_one_way = False`, computed.
- Fold rival: claim "`eta` recoverable from `S`" — refuted by the explicit
  `eta` and `pi/2 - eta` pair with identical `S` but opposite `b_0`.
- Anti-tautology: the one-way witness is the recomputed `rho_bar` collision on a
  real `(phi,chi)` pair, NOT a `recover(k)==A/==B` SMT stand-in (per the
  2026-07-21 systemic finding: an SMT UNSAT is load-bearing only if perturbing
  the actual object changes the result).

## Three-engine scoping

- `sympy` — LOAD-BEARING. Exact `int_0^{2pi} rho dchi = diag(cos^2, sin^2)`,
  exact `S(eta)` and its `eta <-> pi/2-eta` symmetry, symbolic level-set
  constancy.
- `numpy` — LOAD-BEARING. Finite `(phi,chi)` grid on each `T_eta`, orbit-average
  collision witness, fold pair, Clifford maximum.
- `z3` / `cvc5` — SUPPORTIVE only (non-vacuity witness; declare
  `smt_role = supportive_nonvacuity_only`, keep out of `core_ok`). Do NOT label
  load-bearing — the numpy/sympy recompute carries the arrow.
- `jax` / `julia` / `qutip` — memory-gated (run only if psutil-available
  `>= 0.40`; otherwise `tried=False`, honest queue). Julia leg (if it runs) =
  reference recompute of `S(eta)` and the orbit integral; qutip = independent
  `entropy_vn` cross-check on `rho_bar`.

## Acceptance

- Sim starts from `system_v4/probes/SIM_TEMPLATE.py`; `TOOL_MANIFEST` +
  `TOOL_INTEGRATION_DEPTH` + positive/negative/boundary sections present.
- Result JSON in `ratchet_contract/ratchetings/results/`; passes local rerun.
- ClaimGate: `claimgate_plugin/hooks/post_receipt_gate.sh` — tier0 PASS, exit 3
  (honest probe depth) acceptable; `classification` + `promotion_allowed=false`
  declared in the receipt so tier0 is admissible.
- Lev record: emit the schema-valid projection; wiring may stay BLOCKED on the
  installed-CLI consume surface (same honest residual as prior arrows) — do not
  self-promote via a writer-exec.

## Ceiling

`tool_lego_fit_probe`, `promotion_allowed=false`. This finite probe does not
settle a canonical layer ordering or support bridge/axis/canonical promotion.
Poset effect if it holds: inserts the torus-foliation geometry rung between the
spinor carrier and `pure_to_vn`, on Axis A, PROPOSED.
