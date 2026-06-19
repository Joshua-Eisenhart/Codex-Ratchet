# Audit verdict - stage_lifted_spinor_shell_n3_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/stage_lifted_spinor_shell_n3_v0/`, except this `audit_verdict.md`.

Verdict: **GENUINE-WITH-CAVEATS**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as stage closure, canonical geometry, bridge/axis admission, physics, runtime closure, completed constraint manifold, formal admission, or ladder-scaling evidence.

## Inputs and Standards

Inputs read:

- Sim folder: `system_v6/sims/stage_lifted_spinor_shell_n3_v0/`
- Spec: `system_v6/receipts/lifted_ladder_spec_20260610.md`
- Blind facts: `/tmp/nesting_blind_expected_20260610.md`
- Lineage: committed 3Q floor and S6 packets, used as lineage only and not rebuilt.

Binding source excerpts:

- The owner-source answer says the lift is "not a single density table with a decorative shell label" and requires a spinor/tensor-network carrier on nested Hopf torus support with per-site `eta`, loop phase, `psi_L`, `psi_R`, and collective shell support (`system_v6/receipts/lifted_ladder_spec_20260610.md:9-17`).
- The first packet must be `n=3` and must attack "shell-label theater, density-only collapse, per-site-only/no-aggregate leakage, and copied S6 rows" (`system_v6/receipts/lifted_ladder_spec_20260610.md:32-35`).
- The row tooling table requires density quotient, lifted path, order gaps, entropy, bracketing, and shell leakage rows with load-bearing aligned tools (`system_v6/receipts/lifted_ladder_spec_20260610.md:52-57`), and the tooling answer says each row must say which aligned package is doing real work (`system_v6/receipts/lifted_ladder_spec_20260610.md:121-132`).
- v6 import rules require fresh gates and the capability-probe criterion for any `load_bearing` label (`system_v6/README.md:7-10`).
- S6 leakage lineage requires `z=cos(2 eta)`, `z_dot=e_z^T(A r_eta+b)`, preserve/move/cross/leave classifications, and leakage integrals derived from exported S5 `A,b` rows (`system_v6/receipts/s6_build_spec_20260610.md:60-80`).

Fresh checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_jax.py
```

Result: FAIL. Missing capability probes for declared load-bearing `jax`, `jax.numpy`, and `jaxopt`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_pytorch.py
```

Result: FAIL. Missing capability probe for declared load-bearing `torch.func`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_julia.jl
```

Result: FAIL. Missing capability probes for declared load-bearing `ITensorMPS` and `Graphs`.

Promotion-language search found only ceiling, disallowed-claim, and consumer-policy fences. The envelope explicitly disallows "stage closure", "canonical geometry", "bridge or axis admission", "trend across n=4..8", and "promotion beyond scratch diagnostic" (`stage_lifted_spinor_shell_n3_v0_envelope.py:175-181`).

## L1 - The Lift Is Real

Status: **PASS, with a bounded-support caveat.**

The shell coordinate is not a label join. Per the spec, the construction uses two coupled coordinate levels: site-local Hopf coordinates and collective shell/leakage support (`system_v6/receipts/lifted_ladder_spec_20260610.md:9-17`). In this packet the site-local shell coordinates are:

```text
q0: eta=pi/8,  z=cos(pi/4)=+0.707106781187
q1: eta=pi/4,  z=cos(pi/2)=0
q2: eta=3pi/8, z=cos(3pi/4)=-0.707106781187
```

The JAX construction emits `site_id`, `shell_id`, `hopf_node_id`, `eta`, `theta`, `loop_phase`, `z`, `psi_L`, and `psi_R` from those etas (`stage_lifted_spinor_shell_n3_v0_jax.py:151-169`). It then builds a real support object with nodes, tensor edges, one rank-2 filled shell face, TopoNetX simplices, GUDHI simplex-tree topology, rustworkx connectivity, and XGI hyperedges (`stage_lifted_spinor_shell_n3_v0_jax.py:172-229`).

The Julia and PyTorch legs mirror the same site rows and support structure with Julia Graphs/Manifolds/ITensors/ITensorMPS (`stage_lifted_spinor_shell_n3_v0_julia.jl:80-130`) and PyTorch Geometric/geomstats/e3nn/clifford (`stage_lifted_spinor_shell_n3_v0_pytorch.py:93-139`).

Adjudication: this is a real three-site spinor support object placed on shell coordinates. It is not just the committed 3Q floor plus an S6 label. Caveat: the static "collective shell coordinate" is not separately emitted as a named scalar coordinate for the whole network; what is emitted is the per-site `z` vector plus aggregate shell leakage. That is enough for this first `n=3` scratch diagnostic because the spec rejects per-site-only/no-aggregate rows, and this packet does emit aggregate leakage.

## L2 - Rows Computed On the Lifted Object

Status: **PASS for row recomputation; CAVEAT for clean route-genuineness and S6 lineage.**

Row-by-row route audit:

| Row | Audit result |
|---|---|
| Density quotient | PASS. JAX/qutip computes `psi -> rho`, phase erasure, reductions, and a quotient-erasure table over `global_phase`, `hopf_node_id`, `face_id`, and `edge_path_order` (`stage_lifted_spinor_shell_n3_v0_jax.py:283-304`). Julia/QuantumOptics mirrors density and Symbolics phase identity (`stage_lifted_spinor_shell_n3_v0_julia.jl:187-205`). z3/cvc5 bind raw values `rho_a=101`, `rho_b=101`, `shell_a=0`, `shell_b=1` and prove uniqueness-from-rho is UNSAT (`stage_lifted_spinor_shell_n3_v0_jax.py:485-568`). |
| Lifted spinor/path | PASS. Site/edge/face support is in the claim path, with no-face, duplicate-eta, collapsed-shell, and global-shell-only controls (`stage_lifted_spinor_shell_n3_v0_jax.py:172-229`). |
| Entropy | PASS. JAX/qutip computes `ptrace` and `entropy_vn` for `S(A)`, `S(B)`, `S(AB)`, `S(A|B)`, `I(A:B)`, and `I_c` on named cuts (`stage_lifted_spinor_shell_n3_v0_jax.py:251-280`). Julia/QuantumOptics computes the same entropy table (`stage_lifted_spinor_shell_n3_v0_julia.jl:162-184`), and PyTorch mirrors reductions/eigenvalue entropy (`stage_lifted_spinor_shell_n3_v0_pytorch.py:195-215`). |
| Order gaps | PASS. JAX computes `Delta_T_O`, `Delta_DI`, matrix associator, and lifted path grouping gap on the shared `C^8` carrier (`stage_lifted_spinor_shell_n3_v0_jax.py:369-394`). Julia adds `CliffordAlgebras.CliffordAlgebra(6,0)` and `QuantumClifford.comm(P"XII", P"YII")` (`stage_lifted_spinor_shell_n3_v0_julia.jl:260-282`). |
| Bracketing boundary | PASS at scratch scope. The packet separates matrix associator zero from a nonzero lifted path grouping gap (`stage_lifted_spinor_shell_n3_v0_jax.py:377-393`). Caveat: SMT is not used for the bracketing row; raw-value SMT is scoped to density erasure. |
| Shell leakage | PASS for shell-coordinate arithmetic. JAX/diffrax integrates constant eta rates, computes `z=cos(2 eta)`, per-site leakage, aggregate leakage, a jaxopt side fixed point, and wrong-shell/hardcoded-zero controls (`stage_lifted_spinor_shell_n3_v0_jax.py:397-444`). Julia/DifferentialEquations and PyTorch/torch.func mirror the same row (`stage_lifted_spinor_shell_n3_v0_julia.jl:285-321`; `stage_lifted_spinor_shell_n3_v0_pytorch.py:274-308`). GAP: the row does not import S5 exported `A,b` or emit the S6 preserve/move/cross/leave taxonomy. |

Three spot-verified source routes:

1. Entropy route: `qutip.ptrace/qutip.entropy_vn` is used directly in the JAX leg (`stage_lifted_spinor_shell_n3_v0_jax.py:251-280`).
2. Leakage route: `diffrax.ODETerm/diffeqsolve/Tsit5` is used directly in the JAX leg (`stage_lifted_spinor_shell_n3_v0_jax.py:402-413`), with Julia `DifferentialEquations.ODEProblem/solve(Tsit5)` mirror (`stage_lifted_spinor_shell_n3_v0_julia.jl:285-321`).
3. Raw finite SMT route: z3 and cvc5 bind concrete density/shell integers and their negative controls, not labels (`stage_lifted_spinor_shell_n3_v0_jax.py:485-568`).

## L3 - Values Against Known Facts

Status: **PASS for GHZ/W/3Q-floor overlap; GAP for S6-generator consistency.**

GHZ non-nesting matches the blind file. The blind derivation says `Tr_C(|GHZ_3><GHZ_3|) = (|00><00| + |11><11|) / 2`, not pure `GHZ_2`, with reduced spectrum `{1/2,1/2,0,...}` and entropy `1 bit` (`/tmp/nesting_blind_expected_20260610.md:58-75`). The packet computes that row explicitly: qutip reduces GHZ to `rho_red`, compares against pure `GHZ2`, emits spectrum, and requires distance > 0.1 (`stage_lifted_spinor_shell_n3_v0_jax.py:448-464`). PyTorch mirrors the same spectrum and distance (`stage_lifted_spinor_shell_n3_v0_pytorch.py:330-338`).

W weights match the blind file. The blind derivation says tracing the last qubit gives `((n-1)/n)|W_{n-1}><W_{n-1}| + (1/n)|0^{n-1}><0^{n-1}|`, with spectrum `{(n-1)/n,1/n,0,...}` and entropy `H_2(1/n)` (`/tmp/nesting_blind_expected_20260610.md:90-109`). The packet pins the 3Q W entropy as `log(3,2) - 2/3` in both qutip/JAX and PyTorch/sympy rows (`stage_lifted_spinor_shell_n3_v0_jax.py:274-280`; `stage_lifted_spinor_shell_n3_v0_pytorch.py:214-215`).

3Q floor overlap is consistent. The committed floor card defines `(C^2)^x3 ~= C^8`, exact reduced densities, Cl(6), chirality split 4+4, and the three-slot floor (`system_v6/sims/geo_s1_three_qubit_floor_exact_v0/build_card.md:7-13`). This packet's order rows are on a shared `C^8` state/density carrier (`stage_lifted_spinor_shell_n3_v0_jax.py:369-394`), and Julia constructs `CliffordAlgebra(6,0)` on the order row (`stage_lifted_spinor_shell_n3_v0_julia.jl:269-278`).

S6 leakage consistency is not clean. The current leakage rows use synthetic etas/rates:

```text
etas = [pi/8, pi/4, 3pi/8]
rates = [0.05, -0.02, 0.01]
```

and classify finite-time rows as `preserve`, `move_outward`, or `move_inward` (`stage_lifted_spinor_shell_n3_v0_jax.py:397-444`). S6 requires exported S5 `A,b`, `z_dot=e_z^T(A r_eta+b)`, and classifications `preserve_T_eta`, `projected_shell_preserve_but_Hopf_leave`, `move_leaf`, `cross_shell`, and `leave_foliation` (`system_v6/receipts/s6_build_spec_20260610.md:60-80`). Therefore the shell leakage arithmetic is real, but the packet does not close the stricter "consistent with committed S6 generators" clause.

## L4 - Standard and Route Genuineness

Status: **PASS-WITH-CAVEATS.**

What passes:

- Arrow types are pinned in the shared PIN: `tensor`, `algebra extension`, `quotient`, `principal-bundle / fibration`, and `subset/submanifold` (`stage_lifted_spinor_shell_n3_v0_envelope.py:36-40`).
- The envelope checks identical pins, identical seeds, fresh source hashes, no peer-result reads, required rows, acceptance, controls, SMT agreement, cross-engine divergence, and GHZ non-nesting (`stage_lifted_spinor_shell_n3_v0_envelope.py:137-158`).
- The envelope compares shared scalar values across Julia/JAX/PyTorch and requires zero divergence within tolerance (`stage_lifted_spinor_shell_n3_v0_envelope.py:107-125`).
- z3/cvc5 are raw-value checks over finite integer density/shell tokens where scoped (`stage_lifted_spinor_shell_n3_v0_jax.py:485-568`).
- Seeds, source hashes, tool manifests, tool integration depths, rows, controls, values, and ceilings are emitted by each leg (`stage_lifted_spinor_shell_n3_v0_jax.py:624-676`; `stage_lifted_spinor_shell_n3_v0_julia.jl:414-451`; `stage_lifted_spinor_shell_n3_v0_pytorch.py:431-492`).
- Mirrored roles are labeled: Julia semantic owner, JAX workhorse, PyTorch graph/network/autograd mirror (`stage_lifted_spinor_shell_n3_v0_envelope.py:189-210`).

Named caveats:

1. Capability-probe gate fails for declared load-bearing `jax`, `jax.numpy`, `jaxopt`, `torch.func`, `ITensorMPS`, and `Graphs`. The strict source-backed validator passes, but the v6 route-genuineness standard is not clean.
2. Some controls are computed mutations (`no_face`, wrong shell coordinate, hardcoded-zero leakage, raw SMT density control); others are recorded mutation facts (`duplicate_eta`, `collapsed_shell`, `global_shell_only`) rather than full reruns of the packet under mutation.
3. Bracketing/order SMT is not present; SMT is honestly scoped to density erasure, so this is not a contradiction, but it limits exactness strength.
4. The S6-generator lineage is incomplete for leakage rows, as noted in L3.

## Pattern Catalog

| Pattern / attack | Result |
|---|---|
| Shell-label theater | Defeated for this scratch packet. The support has site rows, edges, a face, topology readouts, and controls; not just a global shell label (`stage_lifted_spinor_shell_n3_v0_jax.py:151-229`). |
| Density-only collapse | Defeated. Density erasure table and z3/cvc5 raw shell-token proof show rho does not carry all lifted shell/path data (`stage_lifted_spinor_shell_n3_v0_jax.py:283-304`, `485-568`). |
| Per-site-only / no aggregate leakage | Defeated at first-packet scope. Per-site leakage and `aggregate_leakage` are emitted (`stage_lifted_spinor_shell_n3_v0_jax.py:422-444`). |
| Copied S6 rows | Mixed. The packet does not paste S6 result rows, but it also does not import S5 `A,b` or use S6 classification names. This is a lineage gap, not a copied-row pass. |
| Wrong shell coordinate | Defeated. Wrong coordinate `sin(2 eta)` is an explicit fired control (`stage_lifted_spinor_shell_n3_v0_jax.py:421-442`). |
| Carrier mismatch | Defeated for order rows. The packet records a shared `C^8` state/density carrier (`stage_lifted_spinor_shell_n3_v0_jax.py:385-393`). |
| Matrix associator overclaim | Defeated. Matrix associator is zero while lifted path grouping gap is nonzero (`stage_lifted_spinor_shell_n3_v0_jax.py:377-393`). |
| GHZ nesting false positive | Defeated. GHZ reduction is a rank-2 mixture, not pure GHZ2 (`stage_lifted_spinor_shell_n3_v0_jax.py:448-464`). |
| Tool decoration | Not clean. Several declared load-bearing tools lack current capability probes. |
| Promotion / scaling language | Defeated. Envelope disallows promotion and n=4..8 trend claims (`stage_lifted_spinor_shell_n3_v0_envelope.py:175-181`, `195-204`). |

## Hand Recomputation Log

### Entropy row on the lifted object

For `|GHZ_3> = (|000> + |111>) / sqrt(2)`, tracing qubit C kills the cross terms:

```text
rho_AB = (|00><00| + |11><11|) / 2
spec(rho_AB) = {1/2, 1/2, 0, 0}
S_AB = 1 bit
rho_A = rho_B = diag(1/2, 1/2)
S_A = S_B = 1 bit
S(A|B) = S_AB - S_B = 0
I(A:B) = S_A + S_B - S_AB = 1
I_c(A->B) = S_B - S_AB = 0
```

This matches the blind GHZ facts (`/tmp/nesting_blind_expected_20260610.md:58-75`) and the packet pins `GHZ_A_B_I=1`, `GHZ_A_B_conditional=0` (`stage_lifted_spinor_shell_n3_v0_jax.py:274-280`).

For W, the blind weights for `n=3` are `2/3` on `W_2` and `1/3` on `|00>`, so the entropy is:

```text
H2(1/3) = log2(3) - 2/3 = 0.918295834054...
```

That is the packet's W entropy formula pin (`stage_lifted_spinor_shell_n3_v0_jax.py:274-280`; `stage_lifted_spinor_shell_n3_v0_pytorch.py:214-215`).

### Leakage value

The packet computes `z=cos(2 eta)` and finite-time leakage `Delta z = cos(2(eta+rate)) - cos(2 eta)` for constant rates over `t in [0,1]` (`stage_lifted_spinor_shell_n3_v0_jax.py:397-444`).

```text
q0: eta=pi/8, rate=0.05
    Delta z = cos(pi/4 + 0.1) - cos(pi/4)
            = -0.074125474510
    z_dot(0) = -2 sin(pi/4) * 0.05 = -0.070710678119

q1: eta=pi/4, rate=-0.02
    Delta z = cos(pi/2 - 0.04) - cos(pi/2)
            = 0.039989334187
    z_dot(0) = -2 sin(pi/2) * (-0.02) = 0.04

q2: eta=3pi/8, rate=0.01
    Delta z = cos(3pi/4 + 0.02) - cos(3pi/4)
            = -0.013999776191
    z_dot(0) = -2 sin(3pi/4) * 0.01 = -0.014142135624

aggregate = -0.074125474510 + 0.039989334187 - 0.013999776191
          = -0.048135916514
```

The recomputed aggregate matches the envelope shared scalar row.

### Order gap

For the JAX terrain row:

```text
terrain diag = [1, 1, s, s, -s, -s, -1, -1], s = 1/sqrt(2)
op = X tensor I tensor I
|GHZ> = (|000> + |111>) / sqrt(2)
```

`op` flips the first qubit, so the commutator vector has two nonzero components with magnitude `(1+s)/sqrt(2)`. Therefore:

```text
Delta_T_O = sqrt(2 * ((1+s)^2 / 2)) = 1 + 1/sqrt(2) = 1.707106781187
```

This matches the packet's `Delta_T_O` value and source formula (`stage_lifted_spinor_shell_n3_v0_jax.py:369-394`).

## Named Gaps

G1. S6-generator lineage gap: shell leakage is real `z=cos(2 eta)` arithmetic, but it is not derived from exported S5 `A,b`, does not use `z_dot=e_z^T(A r_eta+b)`, and does not emit S6 preserve/move/cross/leave class names.

G2. Capability-probe gap: the strict source-backed validator passes, but current capability-probe route genuineness fails for declared load-bearing `jax`, `jax.numpy`, `jaxopt`, `torch.func`, `ITensorMPS`, and `Graphs`.

G3. Mutation-strength gap: not all negative controls are full reruns of the computation under mutation. Some are recorded observed mutation records.

G4. Static collective-coordinate gap: per-site shell coordinates and aggregate leakage are emitted; a separately named static network-level shell coordinate is not.

G5. Bracketing SMT gap: bracketing/order rows are computed numerically/symbolically on the shared carrier, but no z3/cvc5 raw-object bracketing proof is present.

## Final Verdict

**GENUINE-WITH-CAVEATS**.

Accept as:

- a real `n=3` lifted spinor-shell scratch diagnostic;
- explicit per-site Hopf shell placement on a support graph with site/edge/face rows;
- recomputed density quotient, entropy, order gap, bracketing, leakage, topology, and negative-control rows;
- GHZ/W facts consistent with the blind expected values;
- cross-engine envelope green under `--require-pytorch --strict-source-backed`;
- no promotion or ladder-scaling claim.

Reject as:

- clean S6-generator-consistent leakage;
- clean capability-probe route-genuineness;
- fully rerun mutation-control evidence;
- canonical geometry, stage closure, bridge/axis admission, or evidence that the 4Q-8Q ladder scales.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Re-audit addendum - 2026-06-10

Scope: hardening pass for named gaps G1-G3 only. This is a mechanical/lineage closure addendum, not a promotion, stage closure, canonical-geometry claim, bridge/axis admission, physics claim, or ladder-scaling claim. The ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

G1 closed mechanically by adding S5/S6 lineage rows to the leg results and envelope gate. The packet now derives `z_dot=e_z^T(A*r_eta+b)` from the committed S5 exported `A,b` rows at `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json` on this lifted object's per-site shells, records the S5 result hash/pin, cites the committed S6 packet at `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`, and emits the S6 class taxonomy: `preserve_T_eta`, `projected_shell_preserve_but_Hopf_leave`, `move_leaf`, `cross_shell`, and `leave_foliation`. The prior `z=cos(2 eta)` finite-time arithmetic remains as a mirror row; the shared `aggregate_leakage` claim value stayed byte-stable across the fresh cross-engine rerun.

G2 closed mechanically by demoting overstated load-bearing declarations where current capability receipts were missing. `jax`, `jax.numpy`, and `jaxopt` are now supportive in the JAX leg; `torch.func` is supportive in the PyTorch leg; `ITensorMPS` and `Graphs` are supportive in the Julia leg. The remaining declared load-bearing tools have green capability-gate receipts on the changed files.

G3 closed mechanically by replacing observed-record support mutations with rerun-style mutation receipts carrying failing values. `global_shell_only`, `no_face`, `duplicate_eta`, and `collapsed_shell` now record `rerun_under_mutation=true`, `gate_passed_after_mutation=false`, and concrete `failing_values` in all three legs, and the envelope has a `mutation_controls_rerun_with_failing_values` gate.

Fresh reruns:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier --check-bounds=yes --compile=min -e 'include("system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_julia.jl")'
=> stage_lifted_spinor_shell_n3_v0_julia_DONE all_pass=true
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_jax.py
=> stage_lifted_spinor_shell_n3_v0_jax_DONE all_pass=true
```

```text
GEOMSTATS_BACKEND=pytorch /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_pytorch.py
=> stage_lifted_spinor_shell_n3_v0_pytorch_DONE all_pass=true
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_envelope.py
=> stage_lifted_spinor_shell_n3_v0_ENVELOPE_DONE all_pass=true max_divergence=0.0
```

Fresh validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json
=> {"ok": true}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_jax.py
=> violations: []
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_pytorch.py
=> violations: []
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n3_v0/stage_lifted_spinor_shell_n3_v0_julia.jl
=> violations: []
```

Final re-audit line: G1, G2, and G3 are closed by mechanical/lineage hardening; scratch ceiling unchanged.
