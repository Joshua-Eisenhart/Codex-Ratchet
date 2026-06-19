# Fresh Audit Verdict: geo_s9_alternative_connections_v0

Verdict: GENUINE-WITH-CAVEATS.

This packet genuinely discriminates the four named alternatives against the committed Hopf connection battery. The structural result is supported: `C_same_c1_non_hopf_density` is the named topological co-survivor at `c1=1`, but it dies on curvature density, holonomy spectrum, and annular flux, so it is not gauge-equivalent to the committed connection under the tested gauge-invariant rows.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This is a four-alternative discriminator battery only. It is not a global uniqueness proof for all connections, not S9 closure, not formal admission, and not bridge/axis/physics evidence.

## Caveats

- G1: The top-level result declares `mode: RATCHETED` (`geo_s9_alternative_connections_v0.py:532-548`; result JSON lines 307 and 419-421). Read literally as a standalone geometry mode, that is overstrong. The canonical rule defines RATCHETED as sequential constraint application with induced geometry recomputed at each step (`geometry_sim_program_canonical_20260610.md:10-14`). This packet is a discriminator battery using ratchet/Stokes parents, not an induced-geometry ratchet sim by itself. Honest mode wording should be `discriminator_battery` or `ratchet-adjacent discriminator`, while preserving the explicit `engine_contract.mode=julia_canon_plus_jax_diagnostic`.
- G2: The envelope names a `jax` lane, but the scoped lane is really Python exact/SymPy + z3/cvc5. The result itself exposes this with `role_id: python_exact_smt_workhorse` and packages `sympy`, `z3`, `cvc5` (`geo_s9_alternative_connections_v0` result JSON lines 257-273; source lines 493-502). The math is not weakened, but the lane name should not be cited as an actual JAX computation.
- G3: I did not rerun the builder or validator because both write result files, and this audit was read-only except this verdict file. I recomputed the symbolic and solver rows in scratch commands and inspected the existing validator result.

## Source Anchors

- Alternative construction is explicit in source: committed `A = dphi + cos(2*eta)dchi`, flat `A = dphi`, rescaled `(1/2)cos(2*eta)`, same-flux `cos(2*eta) + (1/5)sin(2*eta)^2`, and random nonperiodic `eta + sqrt(2)/10` (`geo_s9_alternative_connections_v0.py:183-221`).
- The battery computes `curvature = diff(f, eta)`, `c1 = -(f(pi/2)-f(0))/2`, leaf holonomies `-2*pi*f(eta)`, annular flux `pi*(f(pi/6)-f(pi/4))`, and anchor matches for curvature, `c1`, holonomy, and Stokes (`geo_s9_alternative_connections_v0.py:225-245`).
- Gauge comparison is not a stored label alone: gauge-equivalence requires validity plus curvature and leaf-holonomy matches, then stores curvature-density and leaf-holonomy booleans (`geo_s9_alternative_connections_v0.py:258-304`).
- Parent S2 pins the committed form: target lifted holonomy `h(eta) = -2*pi*cos(2*eta)`, curvature `F = -2*sin(2*eta) d eta wedge d chi`, physical integral `-2*pi`, and `c1=1` (`geo_s2_connection_flux_foliation_v0` result JSON lines 152-164).
- Parent S2 byte anchors include `eta=pi/6` with lifted holonomy `-pi` and `eta=pi/4` with lifted holonomy `0` (`geo_s2_connection_flux_foliation_v0` result JSON lines 1309-1327).
- Parent two-shell Stokes anchor stores the annulus `eta=pi/6` to `eta=pi/4`, coefficient gap `1/2`, physical-period flux `pi/2`, and boundary holonomy gap `pi/2` (`ratchet_s2_two_shell_flux_v0` result JSON lines 745-760).

## Recomputations

Scratch SymPy recomputation with the Makefile interpreter:

```text
committed_hopf: F=-2*sin(2*eta), c1=1, hol(pi/6,pi/4)=(-pi,0), annular_flux=pi/2, twentieths=10
A_flat_dphi: F=0, c1=0, hol=(0,0), annular_flux=0
B_half_cos: F=-sin(2*eta), c1=1/2, hol=(-pi/2,0), annular_flux=pi/4
C_same_c1_non_hopf_density: F=-2*sin(2*eta)+2*sin(4*eta)/5, c1=1, hol=(-13*pi/10,-2*pi/5), annular_flux=9*pi/20, twentieths=9
D_random_nonperiodic: F=1, c1=-pi/4, validity=false by packet construction
```

The same-flux candidate's full sampled lifted holonomy spectrum recomputed as:

```text
committed: [-2*pi, -sqrt(3)*pi, -pi, 0, pi, 2*pi]
C_same:   [-2*pi, -pi*(1/10 + sqrt(3)), -13*pi/10, -2*pi/5, 7*pi/10, 2*pi]
```

That proves both sides of the topology-vs-geometry split: `C_same_c1_non_hopf_density` survives the topological `c1=1` row, but its curvature-density delta is `2*sin(4*eta)/5`, its leaf holonomies differ from `[-pi, 0]`, and its annular flux is `9*pi/20` rather than `pi/2`.

Scratch solver recomputation:

```text
z3: real row unsat, erased flip sat
cvc5: real row unsat, erased flip sat
julia_z3: real row unsat, erased flip sat
```

This matches the stored SMT fields: real units `committed=10`, `anchor=10`; erased units `C_same_c1_non_hopf_density=9`, `anchor=10`; `real_verdict=unsat`, `erased_flip_verdict=sat` (`geo_s9_alternative_connections_v0` result JSON lines 160-217 and 422-473; Julia result lines 57-80).

## Per-Check Adjudication

- Q1 alternatives genuine: PASS. Flat, half-coefficient, same-c1 non-Hopf-density, and random nonperiodic control are all explicitly constructed. The subtle same-flux candidate is genuine as a same-total-flux but different-density alternative: recomputed `c1=1`, curvature delta `2*sin(4*eta)/5`, and holonomy spectrum mismatch. It is not gauge-equivalent under the packet's gauge-invariant comparison.
- Q2 battery: PASS. `F=dA`, `c1`, holonomy, annular flux/Stokes, and validity rows recompute. The committed anchors are byte-cited in source/result and parent S2/two-shell receipts. The same-flux candidate's integral row hits `c1=1`; its `9*pi/20` annular flux correctly misses the `pi/2` anchor.
- Q3 topology-vs-geometry split: PASS. Topological row: `chern_number_c1`. Named topological co-survivor: `C_same_c1_non_hopf_density`. Geometric committed-specific rows: curvature density, leaf holonomy spectrum, annular flux distribution. The committed connection is unique only among these four tested alternatives once the holonomy/Stokes data are required. It is not unique at the `c1` level.
- Q4 controls: PASS. Flat dies at curvature and Chern; rescaled dies at holonomy and also Chern; random control dies first at validity; same-flux dies at geometric rows. z3/cvc5/Julia Z3 erased flips all fire with `unsat/sat`.
- Q5 standard: PASS with G1/G2. Parent lineage is present and hash-bound for S2, quaternionic Hopf stack, quaternionic path transport, two-shell ratchet, and stack uniqueness map (`geo_s9_alternative_connections_v0` result JSON lines 324-384). Julia leg is real enough for its scoped compact mirror (`geo_s9_alternative_connections_v0_julia_results.json:1-87`). Capability receipts and one-to-one tool calls are present (`geo_s9_alternative_connections_v0` result JSON lines 85-135 and 831-855). Versions and deterministic seeds are recorded (`geo_s9_alternative_connections_v0` result JSON lines 316-322 and 407-418). The result ceiling and blocked consumers are explicit (`geo_s9_alternative_connections_v0` result JSON lines 55-64 and 388-392).

## Verdict

GENUINE-WITH-CAVEATS.

The connection discriminator is valid for these four alternatives. The packet correctly establishes that the committed Hopf connection is unique within the tested set given the committed holonomy and annular-flux data, while naming `C_same_c1_non_hopf_density` as the only topological `c1=1` co-survivor. The uniqueness-map implication must stay scoped to these four alternatives and the tested battery rows.
