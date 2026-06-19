# Audit verdict: geo_nested_disintegration_v0

Scope: fresh read-only audit of `system_v6/sims/geo_nested_disintegration_v0/`, except this `audit_verdict.md`. I did not build this sim. I did not git add or commit anything. I did not rerun packet builders because they would rewrite packet result JSONs; all recomputation below is scratch/read-only.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md` keeps convention/order pins, can-fail controls, route genuineness, erasure honesty, scratch ceilings, and fresh-context audits; it allows one genuine derivation plus independent solver/cross-engine binding when the split is honest.

Audit-time state:

- HEAD: `00d784cebe0b8014775725cfd07afe1e1dfa0895`.
- Target packet status: `?? system_v6/sims/geo_nested_disintegration_v0/`; this verdict audits the working-tree packet contents.
- Committed anchors were tracked and clean at audit time. `git ls-files --stage -- system_v6/sims/geo_disintegration_machinery_v0 system_v6/receipts/audit_bar_calibration_20260610.md system_v6/sims/ratchet_s1_single_shell_pilot_v0` listed tracked blobs, and `git diff --quiet -- ...` returned `diff_quiet_exit=0`.
- Parent anchor blob examples: calibration `c447fb12edd0b58cdd3c6f3b01f6e3b9391de28e`; parent disintegration common `5a9dd1d7206f4b38366322cbacd1624ddb702efb`; parent disintegration envelope result `3b9cadcc73655cebdcbb1de358bd8fc22fc67b74`; parent disintegration audit `efdeae9db6612c1a9dbdc1fee6c7db6c0af8cc05`.

## Sources read

- `geo_nested_disintegration_v0_common.py`: pins `stage1_eta_marginal=sin(2*eta)`, `stage1_conditional_chart_density=1/(4*pi^2)`, `stage2_chi_marginal_physical=1/pi`, `stage2_phi_conditional=1/(2*pi)`, `double_chart_chi_marginal=1/(2*pi)`, the 2:1 double cover, union shells `pi/6, pi/4`, empty intersection mortality, and the order row.
- `geo_nested_disintegration_v0_jax.py`: SymPy derives the continuous tower, union band-limit, empty-intersection row, order row, and controls; z3/cvc5 derive finite tower identity with erased controls; JAX gives supportive x64 weights and cover-count diagnostics.
- `geo_nested_disintegration_v0_julia.jl`: Julia Symbolics/Z3 mirrors tower/order/union/control rows and gives an independent finite Z3.jl proof.
- `geo_nested_disintegration_v0_envelope.py`: combines engine results, verifies source hashes, gates, ceilings, no peer reads, and summary boundaries.
- Parent committed packet: `geo_disintegration_machinery_v0` fixed-eta rule and audit caveat; pilot `ratchet_s1_single_shell_pilot_v0` for the single-shell fence/mortality context.

## Q1: Iterated tower exact

Verdict: PASS.

Quoted source/result anchors:

- Source pin: `stage2_chi_marginal_physical=1/pi`, `stage2_phi_conditional=1/(2*pi)`, `double_chart_chi_marginal=1/(2*pi)`, and `chart_double_cover=(phi,chi)~(phi+pi,chi+pi)`.
- Result quote: `chi_period_honored` says physical `chi` is modulo `pi`; double-chart `chi` is modulo `2*pi` with the two sheets identified.
- Result rows: physical common-refinement density `sin(2*eta)/(2*pi**2)`; double-chart density `sin(2*eta)/(4*pi**2)`; stage-2 physical chi marginal `1/pi`; stage-2 phi conditional `1/(2*pi)`.

Hand recomputation:

- Stage 1 fixed-leaf flat conditional over the double chart is `dphi dchi/(4*pi^2)`.
- Stage 2 over physical `chi in [0,pi)` and `phi in [0,2*pi)` gives `(1/pi)*(1/(2*pi)) = 1/(2*pi^2)`.
- Pulling this through the 2:1 chart: double-chart chi marginal is `1/(2*pi)`, so `(1/(2*pi))*(1/(2*pi)) = 1/(4*pi^2)`, matching the committed flat conditional.
- Recovery for the constant observable:
  `int_0^(pi/2) sin(2eta) deta * int_0^pi (1/pi) dchi * int_0^(2pi) (1/(2pi)) dphi = 1`.

Scratch SymPy recompute for the packet's cover-invariant test family gave:

- `cover_shift_defect = 0`
- `stage2_fiber_average = a + b*cos(2*eta) + c*sin(2*eta)**2 + d*cos(2*chi) + e*sin(2*chi)`
- `stage2_leaf_average = a + b*cos(2*eta) + c*sin(2*eta)**2`
- `tower = a + 2*c/3`
- `global_phys = a + 2*c/3`, defect `0`
- `global_double = a + 2*c/3`, defect `0`

The stage-2 marginal is therefore derived from the flat conditional with the 2:1 cover honored, not merely asserted.

## Q2: Union conditional

Verdict: PASS.

Quoted source/result anchors:

- Source derives band masses by integrating `sin(2*eta)` over shrinking bands around `eta1` and `eta2`, then takes the `eps -> 0+` limit.
- Result quote: conditional measure is `w1*mu(.|T_eta1)+w2*mu(.|T_eta2), with each leaf using the committed flat torus conditional`.
- Result rows give ratio `sqrt(3)/2`, weights `sqrt(3)/(sqrt(3)+2)` and `2/(sqrt(3)+2)`, and equal-weight defect `7/4 - sqrt(3)`.

Hand recomputation:

- `rho1 = sin(2*pi/6) = sin(pi/3) = sqrt(3)/2`.
- `rho2 = sin(2*pi/4) = sin(pi/2) = 1`.
- Weight ratio is `sqrt(3)/2 : 1`.
- Normalized:
  `w1 = (sqrt(3)/2)/(sqrt(3)/2 + 1) = sqrt(3)/(sqrt(3)+2) = -3 + 2*sqrt(3) = 0.4641016151377546`.
- `w2 = 1/(sqrt(3)/2 + 1) = 2/(sqrt(3)+2) = 4 - 2*sqrt(3) = 0.5358983848622454`.

Equal-weight control:

- For observable `cos(2*eta)`, `cos(pi/3)=1/2` and `cos(pi/2)=0`.
- Correct value: `w1*(1/2)+w2*0 = -3/2 + sqrt(3) = 0.2320508075688773`.
- Equal-weight value: `(1/2)*(1/2)+(1/2)*0 = 1/4 = 0.25`.
- Defect equal-minus-correct: `7/4 - sqrt(3) = 0.017949192431122706`, nonzero.

The union conditional is derived from the stage-1 marginal density ratio, not assigned by equal prior weights.

## Q3: Empty intersection

Verdict: PASS.

Quoted source/result anchors:

- Pin says `intersection_eta1_ne_eta2=empty` and `empty_conditioning_undefined=branch_mortality`.
- Result defines `T_eta` by `|z2|^2 = sin(eta)^2 with eta in [0, pi/2]`.
- Result quote: `there is no conditional on T_eta1 intersect T_eta2 when eta1 != eta2`.

Hand recomputation:

- `sin(pi/6)^2 = 1/4`.
- `sin(pi/4)^2 = 1/2`.
- Difference is `-1/4`, so a point cannot satisfy both leaf equations in the pinned eta interval.
- Thus `T_pi/6 intersect T_pi/4 = empty`, and conditioning on it is undefinable rather than a zero-probability leaf disintegration case.

Pilot tie: the committed pilot remains single-shell only and explicitly says no nested or multi-layer conditioning is attempted. This packet's branch-mortality row is consistent with that fence: fixed leaves can be conditioned through a disintegration rule, but a genuinely empty two-leaf intersection has no branch to assign a conditional measure to. It does not overclaim the pilot's separate quotient-window mortality row.

## Q4: N01 order row

Verdict: PASS for scoped common-refinement agreement; no general order theorem is earned.

Quoted source/result anchors:

- Packet pin: `order_row=eta_torus_then_phi_equals_direct_Hopf_fiber_disintegration_on_common_refinement`.
- Result row: `agreement_or_gap = agreement_on_common_refinement`.
- Result scope quote: no general commutation claim beyond this Hopf-compatible nested phi-circle refinement.

Both towers are computed in the JAX/SymPy lane:

- Eta-torus-then-phi route computes the stage-2 fiber average, then the stage-2 leaf average, then integrates against `sin(2*eta)`.
- Hopf-fiber-first route computes the same phi-fiber average and integrates over base density `sin(2*eta)/pi` on `eta in [0,pi/2], chi in [0,pi)`.

Scratch recomputation:

- Eta-then-phi tower: `a + 2*c/3`.
- Hopf-fiber-first tower: `a + 2*c/3`.
- Order defect: `0`.
- Direction of finding: agreement on the common refinement, not a gap.

Caveat: Julia Symbolics mirrors closed-form families and Z3 finite rows, but it does not independently re-integrate both continuous routes from first principles in the way the Python/SymPy lane does. Under the calibrated bar, this is acceptable because the continuous derivation is genuine and has independent cross-engine/solver binding; it is still a caveat against claiming a broad Fubini/order theorem.

## Q5: Controls

Verdict: PASS.

- Wrong stage-2 marginal control: result records wrong marginal `1/(2*pi)` on physical `chi in [0,pi)`, wrong recovery `1/2`, correct recovery `1`, defect `-1/2`. Scratch recompute matched.
- Naive union conditioning: result records denominator mass `0`, numerator mass `0`, naive quotient `nan`, and failure as `0/0`.
- Equal union weights: nonzero defect `7/4 - sqrt(3)`.
- Single-leaf reduction: symbolic limit `eta2 weight lambda -> 0` gives `a + b/2 + 3*c/4`, equal to the single-leaf `eta1` average. Exact parent rows match: `stage1_conditional_chart_density = 1/(4*pi**2)`, `conditional_total_mass = 1`, `finite_grid_physical_points = N^2/2`.

The committed parent rule says `conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart`, `chart_double_cover=(phi,chi)~(phi+pi,chi+pi)`, and `conditional_chart_density=1/(4*pi^2)`. The target packet's single-leaf limit recovers those exact rows.

## Q6: Standard checks

Verdict: PASS with named caveats.

Fresh commands/checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_envelope_results.json
-> {"ok": true, "result_json": "...geo_nested_disintegration_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_envelope_results.json
-> {"ok": true, "result_json": "...geo_nested_disintegration_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_envelope_results.json
-> {"ok": true, "result_json": "...geo_nested_disintegration_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_nested_disintegration_v0/geo_nested_disintegration_v0_jax.py
-> load-bearing tools sympy, z3, cvc5 status ok; violations []

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_nested_disintegration_v0/geo_nested_disintegration_v0_envelope.py
-> load_bearing_tools []; violations []

rg -ni "fixture|mock|dummy" system_v6/sims/geo_nested_disintegration_v0
-> no hits
```

SMT/finite rows:

- z3: valid negated finite tower identity is `unsat`; erased stage-2 marginal and doubled-cover controls are `sat`.
- cvc5: same verdicts.
- Julia Z3.jl: same verdicts.
- Finite hand total: eta weights `[1,2,1]`, chi rows `[[2,4,6,8],[3,5,7,9],[5,7,11,13]]`, `phi_count=8` give target `832`; wrong marginal total `416`; doubled-cover total `1664`.
- The source binds integer eta weights, phi counts, chi-class values, and fiber sums inside the solvers before asserting the negated identity. It is not a free Boolean contradiction.

Mode/tooling:

- Mode is honest: `julia_canon_plus_jax_diagnostic`; PyTorch is explicitly omitted because there is no graph/network/autograd claim path.
- Classification and ceilings are preserved: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.
- Capability receipts are present for Python/JAX/SymPy/z3/cvc5 and Julia/Symbolics/Z3; source hashes are current for target engine sources.
- One-to-one claim tools are represented by tool calls: `Symbolics`, `Z3`, `sympy`, `z3`, `cvc5`; `jax` is supportive only.
- Seeds are present: `python_jax=2026061101`, `julia=2026061101`, finite grid `N=8`, union shells `pi/6`, `pi/4`.

Anchor caveat: the packet cites the committed parent and recovers the parent exact rows, and this audit binds the committed parent via git index blob hashes. However, the target envelope itself does not embed the parent packet's `pin_sha256` or source/result SHA fields as first-class parent-anchor fields. This is a durability caveat, not a kill, because the parent was tracked-clean in this audit and the exact single-leaf rows match.

## Q7: Closure

Verdict: PASS, scoped closure.

This genuinely closes `CAVEAT_NESTED_SCOPE` for the named prerequisite surface:

- iterated tower conditioning `eta -> physical chi -> phi` on the Hopf-compatible common refinement;
- two-leaf union conditional for `T_pi/6 union T_pi/4` with weights proportional to `sin(2*eta_i)`;
- empty intersection mortality for distinct fixed eta leaves;
- agreement of torus-tower and Hopf-fiber-first disintegrations on the packet's common refinement.

Multi-shell ratchet cards may cite the union rule for `T_pi/6 union T_pi/4` and the eta-then-phi tower rule for Hopf-compatible nested conditioning.

What remains fenced:

- `CAVEAT_WORKTREE_STATE`: the audited target packet is untracked at audit time.
- `CAVEAT_TWO_LEAF_SCOPE`: this packet proves the explicit two-leaf union `eta1=pi/6`, `eta2=pi/4`; it does not prove arbitrary finite, countable, or three-plus leaf unions.
- `CAVEAT_HOPF_COMPATIBLE_ORDER_ONLY`: the order row proves agreement on the declared Hopf-compatible common refinement only; it does not prove arbitrary order commutation, arbitrary foliations, or general Fubini/Tonelli admissibility.
- `CAVEAT_NO_NONLEAF_CONDITIONING`: conditioning on non-leaf sets, bands after limits with additional structure, transverse intersections of different foliations, or singular/nontransverse intersections remains unproved.
- `CAVEAT_BOUNDARY_LEAVES`: endpoints `eta=0` and `eta=pi/2` remain separately fenced because the Hopf torus degenerates there.
- `CAVEAT_PARENT_HASH_EMBED`: parent exact rows are audited and git-index bound here, but target result JSON does not embed parent source/PIN hashes as durable first-class fields.
- `CAVEAT_TEST_FAMILY`: continuous symbolic equality is exact for the declared cover-invariant symbolic family, not a full measure-theory proof for arbitrary measurable functions.
- `CAVEAT_SOLVER_FINITE`: z3/cvc5/Z3.jl rows are finite tower and erasure checks; they support route genuineness and can-fail controls, not the continuous disintegration proof by themselves.
- `CAVEAT_NO_RATCHET_RUN`: no ratchet sim, manifold claim, axis claim, bridge claim, physics claim, canonical admission, or formal admission is made.

## Verdict

PASS: `geo_nested_disintegration_v0` earns the scoped nested-disintegration prerequisite needed to retire the parent packet's `CAVEAT_NESTED_SCOPE` for the explicit two-leaf union and Hopf-compatible iterated tower it computes.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

Allowed citation: multi-shell ratchet cards may cite this packet for `T_pi/6 union T_pi/4` union conditioning and eta-then-phi Hopf-compatible nested conditioning only, with the caveats above.

## Builder-hardening addendum: CAVEAT_PARENT_HASH_EMBED

Status: `CAVEAT_PARENT_HASH_EMBED` closed by full reruns of the Julia leg, JAX leg, and envelope after adding durable first-class `parent_lineage` blocks to each result JSON.

Embedded anchors:

- `geo_disintegration_machinery_v0_source`: `system_v6/sims/geo_disintegration_machinery_v0/geo_disintegration_machinery_v0_common.py`
- `geo_disintegration_machinery_v0_result`: `system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json`
- `geo_disintegration_machinery_v0_pin`: `system_v6/sims/geo_disintegration_machinery_v0/geo_disintegration_machinery_v0_common.py#/PIN_SPEC`
- `audit_bar_calibration_20260610`: `system_v6/receipts/audit_bar_calibration_20260610.md`

The PASS verdict stands. The scoped fences remain unchanged: `CAVEAT_TWO_LEAF_SCOPE`, `CAVEAT_HOPF_COMPATIBLE_ORDER_ONLY`, `CAVEAT_NO_NONLEAF_CONDITIONING`, and `CAVEAT_BOUNDARY_LEAVES` are not weakened by this hash-embedding hardening.
