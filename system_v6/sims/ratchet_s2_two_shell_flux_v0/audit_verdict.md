# Audit verdict: ratchet_s2_two_shell_flux_v0

Scope: fresh Codex2 cross-backend audit of `system_v6/sims/ratchet_s2_two_shell_flux_v0/`. I did not build this packet. I did not git add or commit anything. Read-only except this verdict file.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md` keeps convention/order pins, can-fail controls, route genuineness, erasure honesty, scratch ceilings, and fresh-context audits; it allows one genuine derivation plus independent solver/cross-engine binding when the split is honest.

Wizard route truth: partial Max Assembly. Three Codex parent readers ran over disjoint audit surfaces (`decision.evidence_boundary`, `failure.falsifier`, `failure.loophole_auditor`) and returned usable receipts. No child/subsubagent layer or full matrix run was claimed. The artifact verdict below is based on direct file reads, recomputation, and read-only checks, not route prose.

Audit-time state:

- Target packet status: `?? system_v6/sims/ratchet_s2_two_shell_flux_v0/`. This verdict audits local untracked artifact evidence, not committed repo evidence.
- Parent/template/calibration paths checked with `git ls-files --stage`: `geo_disintegration_machinery_v0`, `geo_nested_disintegration_v0`, `ratchet_s1_single_shell_pilot_v0`, and `audit_bar_calibration_20260610.md` are tracked.
- Packet validator result existed before this audit and reads `ok=true`, `errors=[]`. I did not rerun `validate_ratchet_s2_two_shell_flux_v0.py` because it writes `*_validator_results.json`.
- Read-only validation used the validator module's `validate(payload)` directly and returned `ok=true`, `errors=[]`.
- Repo validator commands were read-only and passed:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json`
  - same command with `--require-source-backed`
  - same command with `--strict-source-backed`

## Q1: Union Step

Verdict: PASS.

Source support:

- Target pin cites `T_pi/6_union_T_pi/4_via_geo_nested_disintegration_v0_union_rule`, weights `sin(2eta_i)/sum_j...`, physical chi period `pi`, Hopf-compatible scope, and scratch ceiling (`ratchet_s2_two_shell_flux_v0.py:62-76`; result JSON lines 510-512).
- Committed nested rule pins `union_shells=eta1=pi/6,eta2=pi/4` and `union_weights=sin(2eta_i)/sum_j_sin(2eta_j)` (`geo_nested_disintegration_v0_common.py:37-54`).
- Nested audit permits citation only for the explicit two-leaf union and Hopf-compatible tower, while fencing arbitrary finite/countable/three-plus unions, nonleaf/transverse conditioning, boundary leaves, and general order theorems (`geo_nested_disintegration_v0/audit_verdict.md:181-208`).
- Parent lineage is embedded with current file-byte hashes for required parent source/result/audit paths (`ratchet_s2_two_shell_flux_v0.py:150-181`; result JSON lines 444-508).

Recomputations:

- `sin(2*pi/6)=sin(pi/3)=sqrt(3)/2`; `sin(2*pi/4)=sin(pi/2)=1`.
- Normalized weights:
  - `w1=(sqrt(3)/2)/(sqrt(3)/2+1)=sqrt(3)/(sqrt(3)+2)=-3+2*sqrt(3)=0.46410161513775455`.
  - `w2=1/(sqrt(3)/2+1)=2/(sqrt(3)+2)=4-2*sqrt(3)=0.5358983848622454`.
  - `w1+w2=1`.
- Recomputed parent-lineage SHA-256 values matched all embedded source/result/audit hashes for `geo_disintegration_machinery_v0`, `geo_nested_disintegration_v0`, `geo_s2_connection_flux_foliation_v0`, and the S1 template audit/addendum.

Fences respected: yes. The packet stays on the explicit `T_pi/6 union T_pi/4` object, Hopf-compatible eta/chi annulus, and Z4 phase quotient. No transverse conditioning, non-leaf conditioning, boundary leaf conditioning, arbitrary union theorem, general order theorem, manifold, axis, bridge, or physics claim is made (result JSON lines 1065-1081).

## Q2: Per-Leaf Induced Geometry

Verdict: PASS.

Recomputations:

- At `eta=pi/6`: radii `(cos eta, sin eta)=(sqrt(3)/2, 1/2)`, `cos(2eta)=cos(pi/3)=1/2`, metric in `(phi,chi)` is `[[1,1/2],[1/2,1]]`, determinant `3/4`, and `A|_T=dphi+(1/2)dchi = (3/4)dalpha+(1/4)dbeta`.
- At `eta=pi/4`: radii `(sqrt(2)/2, sqrt(2)/2)`, `cos(2eta)=cos(pi/2)=0`, metric in `(phi,chi)` is the identity, determinant `1`, and `A|_T=dphi = (1/2)dalpha+(1/2)dbeta`.
- The self-dual leaf correctly says the `dchi` coefficient vanishes, physical chi-cycle holonomy is `0`, and the global phi cycle remains `2*pi` (result JSON lines 611-670 and 671-728).

Caveat: Julia exact algebra rows mirror these as table/string rows; the load-bearing Julia proof leg is the Z3.jl Stokes identity, not an independent symbolic derivation of every geometry row.

## Q3: Stokes Row

Verdict: PASS.

Convention support:

- Target packet uses `F = -2*sin(2*eta) d_eta ^ d_chi`, physical chi period `pi`, coefficient gap `1/2`, flux `pi/2`, boundary holonomy difference `pi/2`, and `stokes_match=0` (result JSON lines 745-761).
- `geo_nested_disintegration_v0` pins physical chi period `pi` and the double-chart chi period `2*pi` under the 2:1 cover (`geo_nested_disintegration_v0_common.py:43-45`, `56-72`).
- `geo_s2_connection_flux_foliation_v0` pins that one base loop is `chi:0->pi`, while `chi:0->2pi` traverses the base twice, and pins the curvature sign (`geo_s2_connection_flux_foliation_v0_jax.py:37-44`, `60-69`).

Hand derivation under the packet's orientation:

- `cos(2*pi/6)-cos(2*pi/4)=1/2-0=1/2`.
- Physical period `pi` gives annular flux magnitude `pi*(1/2)=pi/2`.
- Matching boundary chi holonomies are `pi/2` at `eta=pi/6` and `0` at `eta=pi/4`, so the boundary gap is `pi/2`.
- The double-chart diagnostic period `2*pi` would give `pi`, and the packet correctly marks this as diagnostic, not the load-bearing physical-period row.
- The flipped-orientation control fires: expected flux `pi/2`, flipped flux `-pi/2`.

Orientation caveat: if one integrates in the raw increasing-eta orientation with `deta wedge dchi`, the sign is opposite. The packet pins the boundary/annulus orientation as `eta1` boundary minus `eta2` boundary and proves the wrong-orientation flip as the can-fail control. Under that pinned orientation, Stokes equality is exact.

## Q4: Step-3 Quotient

Verdict: PASS.

The packet applies Z4 on both leaves by `(phi, chi) -> (phi+pi/2, chi)`, preserving eta and the two-leaf union (result JSON lines 763-810).

Recomputed quotient holonomies:

- `q_global`: both leaves see `pi/2`, gap `0`.
- `z1_alpha` with `(delta phi, delta chi)=(pi,pi)`: eta1 `3*pi/2`, eta2 `pi`, gap `pi/2`.
- `z2_beta` with `(pi,-pi)`: eta1 `pi/2`, eta2 `pi`, gap `-pi/2`.
- `relative_chi_nonprimitive`: gap `pi`, correctly marked double physical chi period and not the load-bearing Stokes row.

Ratchet signatures are computed:

- Narrowing: `S3 -> T_pi/6 union T_pi/4 -> annulus flux -> (T_pi/6 union T_pi/4)/Z4`, with mixture weights present (result JSON lines 985-1026).
- Alteration: per-leaf induced geometry, inter-shell gap before quotient, and surviving quotient primitive rows are present (result JSON lines 815-864).
- Path specificity: requested joint pair and noncommuting variant are both explicit (result JSON lines 1028-1060).

## Q5: Path Specificity

Verdict: PASS with caveat.

Requested joint object:

- `condition_then_quotient_sha256` equals `quotient_then_condition_sha256`.
- The result honestly reports `same_pair_commutes=true` because Z4 preserves eta and therefore preserves the two-leaf union and marginal-ratio weights (result JSON lines 571-577 and 1054-1060).

Symmetry-breaking variant:

- Variant is single-leaf only: `single-leaf phase window on eta=pi/6 only: 0 <= alpha < pi`.
- Orbit `[pi/4, 3*pi/4, 5*pi/4, 7*pi/4]` has membership `[true,true,false,false]`, so it is not Z4-saturated.
- The quotient-then-condition route is not well-defined on `T_pi/6/Z4`, while condition-then-quotient cuts the orbit first (result JSON lines 545-570 and 1029-1053).

Caveat: this earns a quotient well-definedness/equivariance-failure witness, not a numeric order-gap family. The packet says `not_numeric_order_gap_family=true`.

## Q6: Controls

Verdict: PASS.

- Equal-weight union defect is computed from the same union observable, not parallel-constructed: correct weighted `cos(2eta)` coefficient is `-3/2 + sqrt(3)`, equal-weight value is `1/4`, defect is `7/4 - sqrt(3)`, and physical defect is `pi*(7 - 4*sqrt(3))/4` (source lines 270-272, 420-427; result JSON lines 179-185 and 537-543).
- Nothing-excluded control is byte-exact: before and after hashes both `f97d93d95b8b044081057fc931c1dee23ef5b7cbf8908d3c2fb6719dbe0a05e8` (result JSON lines 156-162).
- Naive joint conditioning is dead as `0/0`: denominator `0`, numerator `0`, quotient `nan`, with source control cited to the nested packet (result JSON lines 164-172 and 522-530).
- Empty-intersection mortality is cited and refired: `T_pi/6 INTERSECT T_pi/4`, `sin_squared_difference=-1/4`, source points to `R4_intersection_empty_branch_mortality` (result JSON lines 149-155 and 514-520).
- Wrong Stokes orientation control fires (result JSON lines 173-178 and 531-536).

## Q7: Standard Checks

Verdict: PASS with named caveats.

Fresh read-only checks:

- Packet validator module called read-only via `validate(payload)`: `ok=true`, `errors=[]`.
- Repo validator passed plain, `--require-source-backed`, and `--strict-source-backed`.
- Scratch Python/SymPy/z3/cvc5 recomputation imported the source module without calling `main()` and returned Stokes `pi/2`, wrong-weight defect `7/4 - sqrt(3)`, z3/cvc5 positive `unsat`, erased flip `unsat`, and boundary case `unsat`.
- Scratch Julia/Z3.jl execution, without running the packet writer, returned Julia `1.12.6`, Z3.jl `1.0.4`, positive `unsat`, flipped `unsat`, and boundary `unsat`.
- `rg -ni "fixture|stub|mock|placeholder|todo|hack|fake|simulated|toy|synthetic|dummy|hardcoded|hard-coded" system_v6/sims/ratchet_s2_two_shell_flux_v0` returned no hits.

Tool/schema evidence:

- `schema_version=three_engine_sim_result_v1`, `mode=RATCHETED`, `engine_contract.mode=RATCHETED`, and lanes are scoped to `julia` and `jax` (result JSON lines 334-358, 1063-1065).
- The `jax` lane is explicitly Python exact/SymPy/z3/cvc5 and "does not imply JAX array evidence" (result JSON lines 360-375). This naming convention is accepted for this packet but must not be narrated as JAX array execution.
- Claim-path tools are exactly `sympy`, `z3`, `cvc5`, `Z3`; tool calls are one-to-one and load-bearing (result JSON lines 125-130, 1120-1180 and following).
- Capability receipts are present: Python `3.13.6`, SymPy `1.14.0`, z3 `4.16.0`, cvc5 `1.3.3`, Julia `1.12.6`, Z3.jl `1.0.4` (result JSON lines 82-109).
- Julia leg is real enough for the scoped claim: source uses `using Z3`, constructs solver variables, binds positive/flipped/boundary rows, and records `reads_peer_result=false` (Julia source lines 3-8, 33-75, 146-208; Julia result `all_pass=true`).
- Seeds are deterministic and explicit: `symbolic_seed=2026061102`, `smt_seed=2026061102`, `julia_seed=2026061102`, `eta_shells=[pi/6, pi/4]`, Z4 order `4` (result JSON lines 1083-1093).

Named caveats:

- `CAVEAT_UNTRACKED_TARGET`: the target packet directory is untracked; this is local artifact evidence until intentionally staged/committed.
- `CAVEAT_JAX_NAME`: the result calls the Python exact/SymPy/z3/cvc5 lane `jax`; do not describe it as JAX array evidence.
- `CAVEAT_JULIA_TABLE_ROWS`: Julia mirrors exact scalar rows as explicit string rows; the load-bearing Julia computation is the Z3.jl solver proof and no-peer result.
- `CAVEAT_CAPABILITY_NESTING`: the `Z3` capability receipt is nested under `capability_receipts.julia`, not top-level; the packet validator accepts this and the one-to-one tool call row is present.
- `CAVEAT_NO_REQUIRE_PYTORCH`: I did not run `--require-pytorch` because the packet explicitly omits PyTorch for no graph/network/autograd/PyTorch-specific claim path.
- `CAVEAT_PACKET_VALIDATOR_WRITE`: the packet validator was not rerun as a command because it writes the validator result file; its validation function was called read-only instead.

## Q8: Closure

Verdict: PASS, scoped closure.

This earns:

- a second RATCHETED scratch diagnostic after the S1 single-shell pilot;
- the first joint-conditioned two-shell ratchet object for `T_pi/6 union T_pi/4`;
- exact union weights from the committed nested-disintegration rule;
- per-leaf induced metric/connection/holonomy rows for both leaves;
- inter-shell physical-period flux/holonomy/Stokes equality between the two shells;
- Z4 quotient survival rows for the inter-shell quantities;
- an honest commuting result for the requested joint condition/quotient pair;
- a genuine single-leaf non-Z4-saturated phase-window well-definedness failure within fences;
- load-bearing Python SymPy/z3/cvc5 and Julia Z3.jl checks under a scratch diagnostic ceiling.

This does not earn:

- a committed packet claim by itself;
- three-plus shell union or arbitrary finite/countable union theorem;
- transverse, non-leaf, boundary-leaf, or singular-intersection conditioning;
- general Fubini/Tonelli/order commutation theorem;
- terrain/operator step;
- manifold, axis, bridge, physics, trend, or `M(C,t)` claim;
- formal admission, promotion, canonical admission, or queue/status movement.

## Verdict

PASS: `ratchet_s2_two_shell_flux_v0` passes this fresh read-only audit as a local, untracked, scoped `scratch_diagnostic` artifact. It genuinely supports a two-shell joint-conditioned RATCHETED diagnostic with inter-shell flux/holonomy/Stokes evidence and Z4 quotient survival, under the named caveats above.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; local artifact evidence only until tracked/committed by an explicit later action.
