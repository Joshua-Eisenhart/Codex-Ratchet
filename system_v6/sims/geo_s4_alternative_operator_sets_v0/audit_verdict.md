# Audit Verdict - geo_s4_alternative_operator_sets_v0

Auditor: codex2 fresh audit.  
Date: 2026-06-11.  
Scope: read-only audit of codex1 builder packet, except this `audit_verdict.md`. No git add, no commit.

## Verdict

VERDICT: `GENUINE-WITH-CAVEATS`.

The committed S4 operator set survival pattern is unique among the four tested alternatives in this packet. It is not a global S4 operator-alphabet uniqueness proof and does not exhaust CPTP/channel/operator space.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. The only supported uniqueness implication is: the committed `D_z,D_x,R_x,R_z` pattern is not shared by `A_y_frame`, `B_depolarizing`, `C_amplitude_damping`, or `D_random_hermitian` under this declared battery.

## Named Caveats

- G1: the null generator is deterministic and seed-insensitive. The Python source passes `SEED`, `SEED+1`, `SEED+2`, `SEED+3`, but `random_unitary_rotation(seed=...)` ignores the argument and always rotates around the fixed `[1,2,3]` axis. This does not break the null-death check, but it weakens any wording implying four independent random generators.
- G2: the envelope `engine_contract.mode` is `julia_jax_builder_packet`, which is not one of the current three-engine skill mode labels. The source-backed validator accepts it, but the audit treats it as an honest two-lane builder packet rather than a standard all-three or named two-engine mode.
- G3: the Julia sidecar is real for QuantumOptics/Z3 loading and independent survival-matrix/Z3 partition checking, but its `cptp_choi_positivity` row is hardcoded `true` in the Julia survival matrix. The per-channel Choi positivity evidence is Python/JAX load-bearing, not independently recomputed by Julia.
- G4: versions are recorded under `capability_receipts`, not a top-level `versions` object. This is adequate for audit traceability but should not be described as a top-level versions receipt.

## Source Quotes And Construction Check

Alternatives are real affine Bloch-channel candidates in source:

- Committed anchor and alternatives are constructed in `channel_sets()` at `geo_s4_alternative_operator_sets_v0.py:217-248`.
- Amplitude damping is represented by `root = sqrt(1-gamma)`, matrix diagonal `(root, root, 1-gamma)`, and shift `(0,0,gamma)` at `geo_s4_alternative_operator_sets_v0.py:197-199`. Recomputed Kraus-equivalent affine map for `E0=diag(1,sqrt(1-gamma))`, `E1=[[0,sqrt(gamma)],[0,0]]` at `gamma=0.3` matches the packet matrix and shift.
- Null generation rule is fixed deterministic Hermitian-generator rotation at `geo_s4_alternative_operator_sets_v0.py:202-214`; all four null slots call that function at `geo_s4_alternative_operator_sets_v0.py:243-248`.
- The battery compares shell, quotient mortality, N01/commutator, fixed-axis, and CPTP rows against `COMMITTED_EXPECTED` at `geo_s4_alternative_operator_sets_v0.py:436-477`.
- Choi positivity is computed from the normalized Choi matrix and `jax.numpy.linalg.eigvalsh` at `geo_s4_alternative_operator_sets_v0.py:385-433`.
- Parent anchor reproduction checks byte-exact affine rows, S3/S4 mode sweep shell rows, R_x quotient mortality, and N01 gap at `geo_s4_alternative_operator_sets_v0.py:501-523`.
- SMT proof routes bind computed counts and include erased controls at `geo_s4_alternative_operator_sets_v0.py:533-608`.
- Top-level result records two lanes, capability receipts, claim-path tools, survival matrix, controls, and ceiling at `geo_s4_alternative_operator_sets_v0.py:699-774`.

Julia leg source:

- Julia loads `QuantumOptics` and `Z3` at `geo_s4_alternative_operator_sets_v0_julia.jl:4-9`.
- Julia constructs the same alternative set families at `geo_s4_alternative_operator_sets_v0_julia.jl:87-115`.
- Julia compares survival rows at `geo_s4_alternative_operator_sets_v0_julia.jl:199-229`.

Uniqueness-map boundary:

- `stack_uniqueness_map_20260611.md:15-17` says the evidence does not support "the unique stack" and names S4 operator alphabets as still open.
- `stack_uniqueness_map_20260611.md:26` lists S4 operator alphabets/non-Pauli sets as a missing queue.
- `stack_uniqueness_map_20260611.md:84-90` restates that the stack is not proven unique.

## Recomputations

Commands run without rewriting packet results:

- Read-only Python import using `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` and `importlib`, with source module registered in `sys.modules`; recomputed `battery_for_set()` in memory.
- Read-only Julia capability probe: `/opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier -e 'using QuantumOptics, Z3, LinearAlgebra; ...'`.
- Source-backed envelope validator: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s4_alternative_operator_sets_v0/results/geo_s4_alternative_operator_sets_v0_envelope_results.json --require-source-backed`.

Recomputed facts:

- `A_y_frame` death: `survives=false`, first failure `z_probe_quotient_descent_mortality`, descended slots `[0,1]`, excluded slots `[2,3]`.
- `C_amplitude_damping` row check: shell, quotient, fixed-axis, and CPTP rows pass; `commutator_N01_structure=false`; `N01_order_gap=1`; first failure `commutator_N01_structure`.
- Committed anchor survival: all five row booleans true; `N01_order_gap=2`; `survives=true`.
- One Choi spectrum recomputed for `AD_z0`: `[-3.526590784103438e-17, 0.0, 0.15000000000000002, 0.8500000000000001]`, accepted positive within tolerance.
- Kraus-equivalent amplitude-damping affine check: `M_diag=[0.8366600265340756,0.8366600265340756,0.7]`, `c=[0,0,0.3]`, matches packet.
- Null generation check: all four seed calls return the same matrix; orthogonality residual `2.220446049250313e-16`; determinant `1.0`; first failure `shell_preservation_leakage`.
- Deliberate non-CPTP control: dies as expected; minimum normalized Choi eigenvalue `-0.05000000000000005`.
- z3 recompute: counts `{tested_sets:4,survivors:0,excluded:4}`, positive verdict `unsat`, erased-flip verdict `unsat`, erased flip detected.
- cvc5 recompute: counts `{tested_sets:4,survivors:0,excluded:4}`, positive verdict `unsat`, erased-flip verdict `unsat`, erased flip detected.
- Julia capability probe loaded Julia `1.12.6`, `QuantumOptics.SpinBasis(1//2)`, and `Z3`.
- Source-backed validator returned `ok=true`.

## Per-Question Adjudication

### Q1 Alternatives Genuine

Status: `GENUINE-WITH-CAVEATS`.

`A_y_frame`, `B_depolarizing`, and `C_amplitude_damping` are genuine channel constructions under the packet's affine Bloch representation. `C_amplitude_damping` is Kraus-equivalent to the standard amplitude damping channel at `gamma=0.3`, and its JAX Choi spectrum is positive within tolerance.

`D_random_hermitian` is a genuine unitary-channel null in the sense that the recomputed matrix is orthogonal with determinant `1.0`. Caveat G1 applies: it is fixed deterministic and seed-insensitive, so it is not four independent random generators.

### Q2 Like-For-Like Battery

Status: `GENUINE`.

The same five rows are applied against the committed pattern: shell preservation/leakage, z-probe quotient descent/mortality, N01/commutator structure, fixed axes, and CPTP/Choi positivity. The committed anchor reproduces parent pin, shell, quotient mortality, and N01 gap. The parent S3/S4 mode sweep anchor has `R_x` excluded on the z quotient and `D_z,D_x,R_z` descended; the packet reproduces that as committed descended slots `[0,1,3]`, excluded slot `[2]`.

Two battery rows recomputed for one alternative:

- `A_y_frame` shell signature recomputes as `["leak","leak","preserve","preserve"]`, matching committed shell row.
- `A_y_frame` quotient row recomputes as descended `[0,1]`, excluded `[2,3]`, killing it against the committed `[0,1,3]` / `[2]` pattern.

One Choi spectrum recomputed for `AD_z0` confirms positivity within tolerance, and the deliberate non-CPTP control fires.

### Q3 Survival Matrix And Headline

Status: `GENUINE`.

The survival matrix is:

- `A_y_frame`: dies at `z_probe_quotient_descent_mortality`.
- `B_depolarizing`: dies at `commutator_N01_structure`.
- `C_amplitude_damping`: dies at `commutator_N01_structure`.
- `D_random_hermitian`: dies at `shell_preservation_leakage`.
- Co-survivors named: `[]`.

One death recomputed: `A_y_frame` dies on quotient row. One survival recomputed: committed anchor survives all five rows. Teeth check passes: the null died somewhere, specifically `D_random_hermitian` at `shell_preservation_leakage`. Deliberate non-CPTP fail fires with negative normalized Choi eigenvalue.

Headline accepted with ceiling: the committed set's survival pattern is unique among these four tested alternatives. It is not unique over the untested S4 operator/channel space.

### Q4 Standard / Hygiene

Status: `GENUINE-WITH-CAVEATS`.

What passed:

- Mode/lanes are honest enough for a builder packet: Julia + JAX lanes are declared; PyTorch omission is explicit.
- Parent lineage is hash-bound to S4 parent, S3/S4 sweep, mirror packet, and uniqueness map.
- Real Julia leg exists for QuantumOptics/Z3 package loading and survival/Z3 sidecar, with `reads_peer_result=false`.
- z3 and cvc5 both run with erased flip controls.
- Capability receipts exist for Python, JAX, sympy, z3, cvc5, Julia, and QuantumOptics.
- Top-level claim-path tools and top-level `tool_calls` are one-to-one.
- No `fixture` wording was found in the packet directory.
- Seeds are recorded, with G1 caveat about seed-insensitive null generation.
- Anti-collapse is correct: no tested co-survivors are hidden, and global uniqueness is explicitly blocked by the uniqueness map.

What is caveated:

- G2: non-standard `engine_contract.mode`.
- G3: Julia Choi mirror overclaim; Choi positivity is Python/JAX load-bearing.
- G4: versions are capability receipts, not a top-level versions object.

## Final Ceiling

This audit closes the S4 gap row only for the tested alternatives in `geo_s4_alternative_operator_sets_v0`: `A_y_frame`, `B_depolarizing`, `C_amplitude_damping`, and `D_random_hermitian`.

It does not exhaust alternative S4 operator alphabets, non-Pauli channels, alternate probe quotients, alternate fixed-axis bases, or broader stack uniqueness.
