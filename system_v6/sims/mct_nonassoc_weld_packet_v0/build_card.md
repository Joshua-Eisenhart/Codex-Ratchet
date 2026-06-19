# BUILD CARD: mct_nonassoc_weld_packet_v0 — weld 2: associator as a measured M(C,t) operation

One object, one claim, one card. CLAIM UNDER TEST (mine receipt §E verbatim): a finite M(C,t) packet can compute one load-bearing bracketing-sensitive associator operation over a source-pinned finite carrier support, with density-erasure, quaternion/alternativity, G2-installed, and drop-bracketing controls.

CARRIER (derived default under current doctrine — owner may override; provenance: weld2 mine §D): main support = branch (b), the 3-spinor floor — S_t = {(psi, x, y, z, bracket) : psi in finite (C^2)^3 witness set, x,y,z in O_basis bounded triples}; the octonion algebra enters through the on-disk structure constants (system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json — import or regenerate under identical table/version/hash policy) as the BRACKETING OPERATION table, not as an admitted primitive carrier; direct-O support = a projection/lift row only (branch (a)); sedenion zero-divisor rows = graveyard/control (branch (c)); split-O = Var_t inactive lane (branch (d)).

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false; no canonical carrier admission, no final M(C), no Axis0, no bridge, no physics; G2 NEVER claimed root-forced (installed only); binary order tests stay separate from ternary bracketing tests.

## Read first (binding)
1. system_v6/receipts/weld2_nonassoc_integration_mine_20260610.md — THE SPEC: implement §E verbatim (finite object, probe families, the sixth operation, controls, kill conditions); §A inventory gives the import paths
2. system_v6/sims/axis_independence_discriminators_036/audit_verdict.md — the DECORATIVE lessons (H1-H7): NO fixture-isolated observables, NO label-echo classes, NO tautological controls (x-x / pass=True / hardcoded zeros), NO derived-boolean SMT, NO synthetic autograd
3. system_v6/sims/mct_dynamic_admissibility_packet_v0/ — the committed floor (tuple fields, five operations, ceiling pattern)
4. The committed tower packets (assoc/G2/pg32) — import facts as branch/control rows only, never a tower rebuild

## PIN block (frozen; identical across legs)
- pinned triple set (mine §E): positive O witness (e1,e2,e4) [committed residual 2*e7], quaternion control (e1,e2,e3), repeated-input alternativity control (e1,e1,e4), plus a small deterministic basis sweep; full 512 ordered-triple sweep as verification sidecar if cheap
- the sixth operation associator_bracketing: applies ((x*y)*z) and (x*(y*z)) via the imported structure constants, records the residual vector/norm/component rows, then updates Probe_t, ~_t, Q_t, H_t, R_t according to whether bracketing rows are active
- probe rows per §E: surviving (P_density, P_order, P_phase, relation/update) lifted to the new support; new (P_assoc_vec, P_assoc_norm, P_assoc_component, P_bracket_side, P_density_erasure, P_g2_dim_der, P_g2_closure, P_alt_control); P_shell/P_loop/Axis0 = projection-only flags
- the five committed operations retained on the new support; binary vs ternary kept as separate receipt families

## Build gates (each per §E controls + R3 lessons)
W1. The associator computed from the imported structure-constant table on the shared support (carrier-coupled; no per-row template lookups); the (e1,e2,e4) residual must reproduce the committed value through THIS packet's path.
W2. DENSITY-ERASURE control (the B1 law): the associator visible on the lifted/spinor row and ERASED under the density quotient — both directions computed, with the quotient genuinely recomputed (not asserted) — this is the weld's load-bearing demonstration of WHERE bracketing lives.
W3. Collapse controls all can-fail: quaternion triple -> 0; repeated-input -> 0 (alternativity); raw matrix-composition representation -> associative collapse; each emits the value it would take on failure.
W4. Drop-bracketing quotient flip: with bracketing rows active, ~_t refines; dropped, it coarsens — class counts emitted both ways.
W5. G2 installed-vs-forced rows: dim Der(O) = 14 and corrupted-table = 3 recomputed through this packet's path; bare-root SAT control present; NO root-forced language.
W6. Raw-value SMT (z3 AND cvc5): bind computed associator component/norm values; derive nonzero-associator for the witness triple (UNSAT for "residual = 0") and the erased/quaternion control flips to SAT. No moved/not_moved booleans.
W7. Shuffle: relabel basis elements and recompute — computed bracketing evidence survives, label-derived claims break (both emitted).
W8. Kill conditions live (mine §E): if the packet can only see density rows, or conflates order with bracketing, emit the kill honestly.

## Engines (three-engine claim-bearing; identical PIN; source_sha256 fields per current convention)
Julia = canon (imports/mirrors labeled honestly; Z3.jl). JAX = sweep + z3/cvc5 raw-value proofs. PyTorch = independent computation path for shared scalars or explicit pytorch_role demotion (no synthetic autograd). NumPy control-lane only.

## Files (one folder, atomic)
system_v6/sims/mct_nonassoc_weld_packet_v0/
  mct_nonassoc_weld_packet_v0_julia.jl / _jax.py / _pytorch.py / _envelope.py
  build_card.md (verbatim copy)
  results/*.json
No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true (+ --require-source-backed recorded); W1-W8 receipt fields present; all controls fired with can-fail evidence; carrier provenance fields exact (derived-default note, branches as Var_t); ceiling exact.
