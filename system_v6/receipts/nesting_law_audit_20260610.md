# Nesting-law Draft Math Audit - 2026-06-10

Scope caveat: the file present at `/tmp/nesting_law_draft_20260610.md` is a summary, not the full 19-layer prose. Line-exact quotation is therefore limited to the exposed summary/card claims. The audit below checks those claims against standard characteristic-zero algebra/topology and the repo evidence surfaces named in the card, especially `system_v6/receipts/geometry_sim_program_canonical_20260610.md` and the relevant `system_v6/sims/` result envelopes.

## F1-F3 adjudications

### F1. Zero-product edge case for "anticommutation is stricter noncommutation"

Verdict: confirmed and sharpened.

Derivation. Let `A,B` lie in an algebra over a field of characteristic not 2. Anticommutation is

```text
AB + BA = 0.
```

Noncommutation is

```text
[A,B] = AB - BA != 0.
```

If `AB + BA = 0` and also `AB = BA`, then `2AB = 0`, hence `AB = BA = 0`. Thus anticommutation alone does not imply noncommutation: a zero-product pair satisfies both `AB + BA = 0` and `AB = BA`.

The signed binary rung must be:

```text
AB + BA = 0 and AB != 0
```

equivalently `BA = -AB != 0`. Then

```text
[A,B] = AB - BA = AB - (-AB) = 2AB != 0.
```

So the implication "signed binary -> noncommuting binary" is valid only after excluding the zero-product edge case and excluding characteristic 2.

Ternary caveat. If the ternary comparison is anti-associativity, with

```text
L = (ab)c,  R = a(bc),  L = -R,
```

then `L = R = 0` is the ternary zero-product analogue: it satisfies `L = -R` and `L = R`. To imply nonassociativity, the test would need `L = -R` and `L != 0`. For the octonion-relevant signed ternary law, the object is not anti-associativity of `L,R` but the associator

```text
[a,b,c] = (ab)c - a(bc).
```

An alternating associator also needs a nonzero witness to be a signed nonassociative rung rather than a vacuous associative/zero case.

### F2. Anti-associativity is the wrong octonion signed ternary candidate

Verdict: confirmed, with the correction that the octonion signed ternary rung is alternativity of the associator, not anti-associativity of the products.

Anti-associativity as a universal law is

```text
(ab)c = -a(bc)  for all a,b,c.
```

This fails in any unital nonzero algebra over characteristic not 2. With `a=b=c=1`,

```text
(1*1)*1 = 1,
-1*(1*1) = -1,
```

so anti-associativity would require `1 = -1`.

It also contradicts octonion alternativity. In an alternative algebra,

```text
[a,a,b] = 0,  [a,b,a] = 0,  [b,a,a] = 0.
```

Hence `(aa)b = a(ab)`. Anti-associativity would demand `(aa)b = -a(ab)`, so `2a(ab)=0`. Over the octonions this is false for ordinary nonzero choices, and it is already false with the unit.

The correct octonion statement is:

```text
[a,b,c] is alternating:
[a_{sigma(1)},a_{sigma(2)},a_{sigma(3)}]
  = sign(sigma)[a_1,a_2,a_3],
```

with zero associator whenever two arguments coincide. This is the ternary signed obstruction law. It is the analogue of a signed binary obstruction because the sign lives on the obstruction tensor, not because the two bracketings are negatives of each other.

Receipt check. The present result surfaces support alternativity, not anti-associativity:

- `bloch_root_admissibility_discriminator_v0` reports octonion `t5_fano_zero_count = 42`, `t5_nonassoc_count = 168`, and zero associators on two-generated sets.
- `mct_nonassoc_weld_packet_v0` reports a repeated-argument alternativity-collapse residual of `0` and a full-sweep nonzero count of `168`.
- `assoc_weakening_lattice_classifier` classifies the octonion carrier at the alternativity rung and the sedenion carrier as failing alternativity.

Therefore anti-associativity should remain only a designed-kill/control row. It is not the octonion carrier law and not the signed ternary rung.

### F3. Mode/test conflation and missing nesting types

Verdict: confirmed and sharpened.

The draft-summary matrix line "free / restricted / quotiented / order-bracket" conflates a mode with a test family. The committed program's four modes are:

```text
FREE
RESTRICTED
QUOTIENTED
RATCHETED
```

The fourth mode is not "order/bracket pressure". It is ratcheted sequential constraint application with recomputed induced geometry:

```text
G_{t+1} = {x in G_t : C_{t+1}(x)}
```

followed by recomputation of induced metric, connection, holonomy, flux, measure, basins, and path-specific survivor geometry. Its signatures are narrowing, alteration, path specificity, and branch mortality.

Order/bracket pressure is a test family. It can and should run inside every mode:

- FREE: raw bracketing/order behavior before imposed restrictions.
- RESTRICTED: behavior after fixing a submanifold, slice, carrier subset, or admissible row.
- QUOTIENTED: behavior after erasing phase, bracket, path, or equivalence data.
- RATCHETED: behavior under sequential constraints with recomputed induced geometry.

The taxonomy is also incomplete. At minimum it is missing:

- refinement/limit nesting: finite ladders or finite probes converging to continuum invariants, including the F01 finite-refinement rows and the `L(N,1)` phase-resolution tower toward the Hopf/density quotient;
- group-action/orbit nesting: actions and orbit spaces such as the `S^1` Hopf phase action on `S^3`, finite `Z_N` phase actions giving lens spaces, and `SU(2)` acting on `S^3`.

It should also separate covering-space/group-quotient nesting from generic quotient nesting, because `SU(2) -> SO(3)` and `S^3 -> L(N,1)` are covering/quotient facts with their own invariants.

## Independent findings

### 1. Claim quoted: "Bloch sphere/ball foundation" or any order putting the Bloch ball before the spinor/Hopf layer

Verdict: wrong if used as a foundation claim.

Correction/math. The canonical order starts with the spinor/Hopf geometry:

```text
C^2 superset S^3 --Hopf/S^1 quotient--> S^2 ~= CP^1
```

The Bloch ball is the density-state body

```text
B^3 = D(C^2),
```

with pure-state boundary `S^2`. It is downstream of normalized spinors and phase erasure, not the root carrier. The correct dimension facts are:

```text
dim_R C^2 = 4,
dim_R S^3 = 3,
dim_R CP^1 = dim_R S^2 = 2,
dim_R B^3 = 3.
```

The committed/present evidence also separates the commuting and noncommuting probes: commuting `sigma_z` probes produce an affine dimension-1 interval/simplex `Delta_1`; the full noncommuting Pauli probes reconstruct affine dimension 3, the solid Bloch ball.

### 2. Claim quoted: "anticommutation is a stricter special case of noncommutation"

Verdict: false without the nonzero-product clause.

Correction/math. The correct binary rung is:

```text
noncommutation: [A,B] != 0
signed noncommutation: AB + BA = 0 and AB != 0
```

The second condition implies `[A,B] = 2AB != 0` over characteristic not 2. Without `AB != 0`, zero-product pairs are both commuting and anticommuting.

### 3. Claim quoted: "anti-associativity" as the sharpened ternary rung

Verdict: wrong candidate for the octonion carrier.

Correction/math. The octonion signed ternary rung is:

```text
[a,b,c] = (ab)c - a(bc) is alternating,
```

with at least one nonzero associator witness. Universal anti-associativity `(ab)c=-a(bc)` is killed by the unit and by repeated-argument alternativity. It is only a negative-control law.

### 4. Claim quoted: "nonassociativity placement = root-native in form, admission later"

Verdict: correct only with a strict split between relation type and admitted carrier.

Correction/math. The ternary obstruction

```text
[a,b,c] != 0
```

can be introduced as a root-level relation/test type. But octonion carrier admission is not root-level in the canonical program. It enters after the spinor/Hopf, connection/foliation, density, operator, terrain, stacked terrain, finite-refinement, and tensor/Clifford stages. A 19-layer order may mention ternary nonassociativity early as a test family, but it must not claim the octonion/G2 carrier is admitted before the S9 division-algebra/nonassociativity stage.

### 5. Claim quoted: "four-fibration ladder" if the real rung is omitted

Verdict: incomplete if it lists only complex, quaternionic, and octonionic Hopf maps.

Correction/math. The four division-algebra Hopf fibrations are:

```text
S^0 -> S^1  -> S^1
S^1 -> S^3  -> S^2
S^3 -> S^7  -> S^4
S^7 -> S^15 -> S^8
```

The base dimensions are `1,2,4,8`, and the fiber dimensions are `0,1,3,7`. Adams termination blocks a fifth normed-division-algebra Hopf rung. Sedenions are a failure boundary, not a fifth successful rung.

### 6. Claim quoted: "sedenions extend the ladder" or any sedenion row preserving the norm-law/fibration effect

Verdict: wrong.

Correction/math. Cayley-Dickson sedenions contain zero divisors and fail the norm-law and Hopf-fibration behavior needed by the R/C/H/O ladder. The evidence surface reports norm-law violation, image deviation, fiber-break deviation, and zero-divisor controls. Exact zero-divisor witnesses are convention-sensitive; the packet convention uses `(e1+e10)(e4+e13)=0`, while another translated convention can make `(e3+e10)(e6-e15)=0`. The invariant claim is failure of the norm/fiber law, not one universal index spelling.

### 7. Claim quoted: "octonions are anti-associative" or "all octonion triples are nonassociative"

Verdict: wrong.

Correction/math. Octonions are alternative, not anti-associative. In the imaginary basis triple sweep used by the receipts, there are:

```text
42 ordered Fano-line triples with zero associator,
168 ordered distinct triples with nonzero associator,
210 ordered distinct triples total.
```

Two-generated subalgebras are associative by Artin's theorem, which matches the zero residuals on two-generated sets. The correct new quality is a nonzero alternating associator with associative two-generator shadows.

### 8. Claim quoted: "G2 is forced by the root constraints"

Verdict: overclaim if stated as forced by the bare root.

Correction/math. `G2` is `Aut(O)` and appears once the octonion/Fano multiplication carrier is installed. The present discriminator classifies `G2` as installed-not-forced: lower carriers such as `H` also satisfy weaker root probes but have different derivation dimensions. The corrected claim is:

```text
octonion/Fano carrier installed -> automorphism group G2,
bare root constraints alone do not force G2.
```

### 9. Claim quoted: "SU(2) -> SO(3)" if assigned as an ordinary quotient or Hopf arrow

Verdict: arrow type must be corrected.

Correction/math. `SU(2) ~= S^3` double-covers `SO(3)`:

```text
SU(2) -> SO(3) is a 2:1 Lie-group covering.
```

A spinor path needs `4*pi` for return, while the density/SO(3) action returns after `2*pi`. This is not the same arrow type as the Hopf fibration `S^1 -> S^3 -> S^2`, though both start from `S^3`.

### 10. Claim quoted: "S^3 -> S^2 -> B^3" if all arrows are written as the same nesting type

Verdict: wrong arrow typing.

Correction/math. The correct chain is heterogeneous:

```text
C^2 superset S^3                 normalization/submanifold
S^3 -> S^2 ~= CP^1               principal S^1 bundle / Hopf quotient
S^2 subset boundary(B^3)          boundary inclusion into convex density body
B^3 = D(C^2)                     convex mixed-state body
```

The Hopf quotient erases continuous phase; the boundary inclusion does not erase phase, because that erasure already happened upstream.

### 11. Claim quoted: "T_eta torus area" if written without the chart double-cover correction

Verdict: potentially wrong unless the double cover is accounted for.

Correction/math. In the Hopf coordinates of the committed program, the `(phi,chi)` chart double-covers `T_eta`. The corrected torus area is:

```text
Area(T_eta) = 2*pi^2*sin(2*eta),
```

with the Clifford torus at `eta = pi/4`. A naive rectangular chart integral gives twice this value if the double cover is not divided out.

### 12. Claim quoted: "4-question sim matrix: free / restricted / quotiented / order-bracket"

Verdict: wrong mode list.

Correction/math. The correct mode list is:

```text
FREE, RESTRICTED, QUOTIENTED, RATCHETED.
```

Order/bracket pressure is a test family to be applied within modes. The ratcheted mode is sequential constraint nesting with induced-geometry recomputation.

### 13. Claim quoted: "taxonomy subset/quotient/convex/bundle/foliation/dynamical/tensor/algebra-extension"

Verdict: incomplete.

Correction/math. The list misses refinement/limit nesting and group-action/orbit nesting. It should also split covering-space/group-quotient arrows from generic quotient arrows. These are not decorative additions: F01 finite-refinement probes, the lens-space tower `S^3/Z_N = L(N,1)`, the `S^1` phase action, and `SU(2)` action/cover facts require them.

### 14. Claim quoted: any one-line chain assigning `L(N,1) -> CP^1` as a plain subset or ordinary limit arrow

Verdict: wrong if so typed.

Correction/math. `L(N,1)` is the free finite quotient

```text
L(N,1) = S^3 / Z_N
```

where `Z_N` acts inside the Hopf phase direction. The map to `CP^1 ~= S^2` is still a circle-bundle projection after quotienting by the finite subgroup of the phase circle; it is not a subset inclusion. As `N` changes, the tower is a refinement/residual-phase-resolution family, not a single monotone inclusion chain.

### 15. Claim quoted: any layer that places operator/terrain/order cells before density geometry

Verdict: dependency error.

Correction/math. The canonical dependency is:

```text
spinor/Hopf -> density/Bloch -> operator actions -> terrain generators
             -> stacked terrain/operator/Hopf order cells.
```

Pauli and channel actions require the density/Bloch representation they act on. The 64 terrain/operator/Hopf cells require both the terrain generators and the operator/Hopf placement choices. They cannot be root layers.

### 16. Claim quoted: any layer treating finite discretization as only a quotient

Verdict: incomplete.

Correction/math. Finite discretization contains at least two distinct mathematical effects:

```text
finite quotient/resolution: T_eta^{N,N}, Z_N phase quotients, checkerboard parity;
refinement/limit behavior: N -> infinity convergence to continuum invariants.
```

The F01 rows and finite phase lens results make the limit/refinement type load-bearing. It should not be collapsed into plain quotient nesting.

### 17. Claim quoted: any layer treating `(C^2)^3`, `Cl(6)`, and reduced densities as the same nesting type

Verdict: wrong if collapsed.

Correction/math. The three-spinor/Clifford floor has several different maps:

```text
(C^2)^3 has complex dimension 8;
Cl(6) ~= M_8(C) is an algebra representation fact;
partial trace/reduced densities are tensor-factor erasure maps;
entropy rows are functions of reduced density spectra.
```

Tensor product, algebra representation, and quotient/erasure by partial trace are different arrow types.

### 18. Claim quoted: any chain using "simplex vs ball" without dimension separation

Verdict: must be sharpened.

Correction/math. A commuting qubit measurement family sees a classical one-dimensional simplex/interval:

```text
Delta_1, affine dimension 1.
```

The noncommuting Pauli family sees the full solid Bloch ball:

```text
B^3, affine dimension 3.
```

The boundary sphere `S^2` is the pure-state quotient image, not the mixed-state body.

### 19. Claim quoted: any order treating G-structures, incidence geometry, or OP2 as upstream of octonion/Fano installation

Verdict: dependency error unless explicitly marked as an external comparison/control.

Correction/math. The committed program order is:

```text
R/C/H/O + Fano constants + alternativity/nonassociativity
  -> G2 = Aut(O), SU(3) = Stab_G2(u), G2/SU(3) = S^6,
     Spin(7), Spin(8), J3(O), F4, OP2, split-G2, PG(3,2).
```

Those structures depend on the octonion/Fano carrier or on deliberately separate finite/split controls. They are not independent root layers.

### 20. Claim quoted: any 19-layer total order not refining the committed program order

Verdict: wrong unless justified by an independent receipt.

Correction/math. Any expanded 19-layer order must refine this partial order:

```text
S1  spinor/Hopf/free geometry
S2  connection, flux, foliation, torus geometry
S3  density and observable geometry
S4  operator algebra and Bloch actions
S5  terrain/channel generators and flows
S6  stacked terrain/operator/Hopf order cells
S7  finite discretization and refinement limits
S8  multi-spinor, reduced-density, Clifford floor
S9  division-algebra and nonassociativity tower
S10 G-structure, homogeneous-space, incidence extensions
S11 constraint manifold over the verified stack
```

An expanded chain can subdivide these stages, but it must not reverse their dependencies.

## Corrected ladder statement

Final form:

```text
1. Binary root:
   [A,B] = AB - BA != 0.

2. Signed binary:
   AB + BA = 0 and AB != 0.
   Over characteristic not 2 this implies [A,B] = 2AB != 0.
   Zero-product pairs are excluded.

3. Ternary root:
   [a,b,c] = (ab)c - a(bc) != 0
   for at least one triple.

4. Signed ternary:
   The associator is alternating:
   [a_{sigma(1)},a_{sigma(2)},a_{sigma(3)}]
     = sign(sigma)[a_1,a_2,a_3],
   with [a,a,b] = [a,b,a] = [b,a,a] = 0,
   and with at least one nonzero associator witness.

   This is the octonion rung. Universal anti-associativity
   (ab)c = -a(bc) is rejected as a designed-kill control law.
```

## Corrected taxonomy list

```text
1. Subset/submanifold nesting
   Example: S^3 subset C^2 after normalization.

2. Boundary/interior nesting
   Example: S^2 = boundary(B^3) for pure states inside the density body.

3. Quotient/equivalence nesting
   Example: phase erasure from normalized spinors to density/pure-state rays.

4. Principal bundle/fibration nesting
   Example: S^1 -> S^3 -> S^2 and the R/C/H/O Hopf ladder.

5. Covering-space and finite group quotient nesting
   Example: SU(2) -> SO(3), S^3 -> L(N,1) = S^3/Z_N.

6. Foliation/leaf nesting
   Example: Hopf tori T_eta and fiber leaves.

7. Refinement/limit nesting
   Example: F01 finite probes, T_eta^{N,N}, and lens/phase-resolution towers as N -> infinity.

8. Group-action/orbit/stabilizer nesting
   Example: S^1 phase orbits on S^3, Z_N phase actions, SU(2) actions, SU(3)=Stab_G2(u).

9. Convex/density-state nesting
   Example: D(C^2)=B^3, classical Delta_1 slices, CPTP images.

10. Dynamical/flow/semigroup nesting
    Example: Hamiltonian/unitary flows, dissipative GKSL-like generators, basins.

11. Ratcheted sequential-induced-geometry nesting
    Example: G_{t+1}={x in G_t:C_{t+1}(x)} with recomputed induced metric/connection/holonomy/measure.

12. Tensor/product and marginal-erasure nesting
    Example: (C^2)^3, reduced densities, partial traces.

13. Algebra-representation nesting
    Example: Cl(6) ~= M_8(C), Pauli algebra, operator algebras.

14. Algebra-extension/carrier-boundary nesting
    Example: R -> C -> H -> O as successful normed carriers, sedenions as failure/control boundary.

15. G-structure and homogeneous-space nesting
    Example: G2=Aut(O), G2/SU(3)=S^6, Spin(7), Spin(8), F4/OP2 rows.

16. Incidence/combinatorial nesting
    Example: Fano lines, PG(3,2), finite support/checkerboard structures.
```
