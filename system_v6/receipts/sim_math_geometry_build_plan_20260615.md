# Sim Math and Geometry Build Plan 2026-06-15

```yaml
receipt_kind: math_geometry_build_plan
status: plan_only
claim_ceiling: no admission, no completion, no bridge, no physics
purpose: replace nickname/jargon planning with explicit finite objects, maps, quotients, geometry, controls, and sim order
```

This document answers the actual build question:

```text
What finite mathematical objects are being simulated first?
What maps and quotients define them?
What geometry is induced?
What stronger carriers are forced versus merely installed?
What order makes the sims real instead of decorative?
```

Project labels are not used as evidence here. A label only counts when it is tied to a finite set, map, invariant, quotient, update rule, or control.

## 1. The Root Object Is a Finite Distinguishability System

The base sim object is:

```text
D = (S, P, C, Adm_C, Comp, U, R)
```

where:

```text
S       finite support set of candidate states/configurations
P       finite probe/readout family
C       finite constraint family
Adm_C   admissibility predicate over S
Comp    explicit composition/bracketing rule when states or maps compose
U       update or restriction rule, if evolution is part of the packet
R       receipt data: source hash, result hash, controls, blocked consumers
```

The first quotient is:

```text
x ~_P y  iff  p(x) = p(y) for every p in P
Q_P(S) = S / ~_P
```

This is the first working form of identity. Identity is not primitive; it is induced by the probes that fail to distinguish.

The first admissible object is:

```text
M(C) = (S_C, C, P, ~_P, Adm_C, Comp, U, G, R)
S_C = { x in S : Adm_C(x) = true }
```

`G` is not assumed. It is induced after the survivor set exists.

Typical induced geometry:

```text
G_t = (S_t, E_t)
E_t = { (x,y) in S_t x S_t : relation_t(x,y) = true }
```

For bit-ring fixtures:

```text
E_t = { (x,y) : HammingDistance(x,y) = 1 and x,y in S_t }
```

For quotient geometry:

```text
E_t^Q = { ([x],[y]) : exists x' in [x], y' in [y] with (x',y') in E_t }
```

The ratchet step is:

```text
S_0 = S
S_{t+1} = { x in S_t : c_{t+1}(x; S_t, P_t, G_t) = true }
Q_t = S_t / ~_{P_t}
G_t = induced geometry on S_t or Q_t
```

The key rule is that `G_t` is recomputed after the carve. It is not relabeled.

## 2. The Three Root Tests

The same distinguishability principle must be tested in three places.

### 2.1 Element Quotient

```text
x ~_P y iff all active probes agree
```

A sim must report:

```text
|S|
|P|
classes Q_P(S)
class sizes
which probes merge or split which states
```

Control:

```text
Remove one probe p from P.
If a claimed distinction survives unchanged when p was supposed to separate it, p was not load-bearing.
```

### 2.2 Order Sensitivity

For restrictions or updates `A,B : Pow(S) -> Pow(S)`:

```text
AB(S) = B(A(S))
BA(S) = A(B(S))
```

Order sensitivity exists only if:

```text
AB(S) != BA(S)
```

or if a declared readout differs:

```text
r(AB(S)) != r(BA(S))
```

Important nuance: fixed set intersections commute. To get true order sensitivity in a finite survivor process, at least one constraint often needs to read the current survivor set:

```text
c(x; S_t) = true iff f(x) >= mean_{y in S_t} f(y)
```

Then applying `A` before `B` can change the threshold used by `B`, and vice versa.

### 2.3 Bracketing Sensitivity

When there is an operation `*`, bracketing is tested by:

```text
Assoc(a,b,c) = (a*b)*c - a*(b*c)
```

A bracket-sensitive carrier is needed only when some probe can distinguish:

```text
p((a*b)*c) != p(a*(b*c))
```

Quaternionic associativity and octonion nonassociativity must stay separate:

```text
H: Assoc(a,b,c) = 0 for all tested triples
O: exists a,b,c with Assoc(a,b,c) != 0
```

Nonassociativity is not a root shortcut. It is root-adjacent pressure at the grouping level and must show what breaks when bracket sensitivity is erased.

## 3. Minimal Survivable Structure

The "least strong thing that survives" is a concrete comparison test.

Let representations be:

```text
R0 = quotient-only classes
R1 = state functional omega over earned probe algebra
R2 = density operator rho with omega(A)=Tr(rho A)
R3 = spinor lift psi with rho=psi psi^dagger
R4 = richer carrier such as quaternion/Clifford/etc.
```

Define a preorder:

```text
R_i <= R_j
```

to mean:

```text
every distinction preserved by R_i under the active probes is also preserved by R_j
```

A representation survives if it passes the active constraints:

```text
Surv = { R_i : constraints and controls pass for R_i }
```

The minimal survivors are:

```text
MinSurv = { R_i in Surv : no R_j in Surv with R_j < R_i }
```

A stronger representation is forced only when:

```text
R_i fails a named active or future probe
and
R_j preserves the distinction
and
all weaker surviving alternatives fail the same probe
```

Otherwise the stronger structure is installed/supportive, not forced.

This is the exact function of:

```text
system_v7/sims/finite_distinguishability_quotient_forced_or_installed_carrier_v0
system_v7/sims/weakest_structure_ladder_gate_v0
```

## 4. Density Matrices Are Earned Readouts, Not the Root

After finite probes exist, the standard finite quantum readout is:

```text
H = C^2
rho >= 0
Tr(rho) = 1
p_A(rho) = Tr(A rho)
```

Probe quotient:

```text
rho ~_P sigma iff Tr(A rho) = Tr(A sigma) for every A in P
```

For Pauli probes:

```text
rho = 1/2 (I + r_x sigma_x + r_y sigma_y + r_z sigma_z)
r_i = Tr(rho sigma_i)
```

Density matrices enter when the finite probe algebra is earned. They are not the first primitive because they already assume a carrier, linear observables, trace, positivity, and normalization.

Control:

```text
If two carriers differ only by information the active probes never read,
then density/readout is enough for that packet.
If a later probe splits them, density was an erasing quotient and the lift may be forced.
```

## 5. Spinor/Hopf Geometry: Exact Finite Version

The spinor carrier is:

```text
psi in C^2
||psi|| = 1
```

The density quotient is:

```text
rho(psi) = psi psi^dagger
```

The Hopf-coordinate spinor used in the source docs is:

```text
psi(phi, chi; eta) =
  ( exp(i(phi+chi)) cos(eta),
    exp(i(phi-chi)) sin(eta) )
```

The density/Bloch readout is:

```text
r_x = sin(2 eta) cos(2 chi)
r_y = - sin(2 eta) sin(2 chi)   # sign depends on sigma_y convention
r_z = cos(2 eta)
```

Global fiber phase `phi` cancels from `rho`.

Therefore:

```text
psi(phi, chi; eta) and psi(phi', chi; eta)
```

can be distinct as lifted spinors but identical under density/Bloch probes.

This is the math behind:

```text
public quotient erases fiber/phase information
lifted/frame-relative probe can split the quotient later
```

Control:

```text
Use density-only probes: phi must be invisible.
Add a phase-sensitive or lifted-frame probe: phi classes must split.
Remove the lifted probe: split must disappear.
```

## 6. Ring-Checkerboard as a Finite Support, Not a Metaphor

The finite support should be written as a product set:

```text
S_ring = Sheet x Eta x Phi x Chi
```

Current finite table fixture:

```text
Sheet = {L, R}
Eta   = {eta_0, eta_1, eta_2}
Phi   = {0,1,2,3}
Chi   = {0,1,2,3}
|S_ring| = 2 * 3 * 4 * 4 = 96
```

Each element is:

```text
x = (s, k, i, j)
```

with:

```text
s = sheet
k = shell / eta index
i = phi index
j = chi index
```

Three coordinate presentations are maps out of the same finite support:

```text
flat_chart(x)       = finite checkerboard/grid coordinate
shell_chart(x)      = shell or eta coordinate plus local chart
ring_chart(x)       = ring/fiber coordinate table
```

The consistency test is not "these are the same because we named them together." It is:

```text
support_count(flat) = support_count(shell) = support_count(ring)
probe_rows(flat(x)) = probe_rows(shell(x)) = probe_rows(ring(x)) for declared probes
quotient classes agree under the declared probe family
adjacency/readout invariants agree where they are supposed to
```

Required negative controls:

```text
erase shell k
erase fiber/phase i
shuffle labels while preserving cardinality
change adjacency while preserving cardinality
inject flat/shell/ring disagreement
compare density probes against phase-sensitive probes
```

This is what:

```text
system_v7/sims/finite_ring_checkerboard_support_three_presentation_consistency_v0
```

must become. Current result is a useful finite table fixture, not an admitted support theorem.

## 7. Entropy Co-Ratchet: Explicit Functions

The current entropy floor fixture uses:

```text
S = {0,1}^6
```

with ring adjacency:

```text
edges = { (i, i+1 mod 6) : i=0..5 }
```

A local equality constraint:

```text
c_eq,k(x) = true iff x_k = x_{k+1 mod N}
```

A local xor constraint:

```text
c_xor,k(x) = true iff x_k != x_{k+1 mod N}
```

A state-dependent threshold constraint:

```text
a(x) = number of aligned ring edges in x
c_mean(x; S_t) = true iff a(x) >= mean_{y in S_t} a(y)
```

This gives real order sensitivity only when the second constraint sees the survivor set left by the first.

Typed entropy/readout functions:

```text
H_capacity(S_t) = log2 |S_t|
H_quotient(S_t,P) = log2 |S_t / ~_P|
H_block(S_t) = log2 number of distinct checkerboard block rows
```

For deterministic update `f : S -> S`, basin entropy:

```text
B = terminal basin partition induced by f
p_b = |b| / |S|
H_basin = - sum_b p_b log2(p_b)
```

Blocked until earned:

```text
von_neumann_entropy(rho) = -Tr(rho log rho)     # requires density rho
cut_entropy(rho_A)       = -Tr(rho_A log rho_A) # requires a cut and partial trace
fiber_residual           # requires Hopf/lift layer
```

The co-ratchet requirement is:

```text
S_t changes -> G_t recomputed -> readout family E_t recomputed
```

Not:

```text
compute entropy once and narrate geometry afterward
```

This is what:

```text
system_v7/sims/entropy_geometry_coratchet_floor_v0
```

currently starts. It still needs audit authority, stronger independent legs, and better source/result fields.

## 8. Qubit Tower / Inverse-Limit Object

For `n` qubits:

```text
H_n = (C^2)^(tensor n)
dim H_n = 2^n
rho_A = density matrix on subsystem A
```

Probe quotient on subsystem `A`:

```text
rho_A ~_P sigma_A iff Tr(P rho_A) = Tr(P sigma_A) for every P in P_A
```

Partial trace compatibility:

```text
Tr_{A\B}(rho_A) ~_B rho_B
```

The finite inverse-limit-like object through depth `N` is:

```text
X_{<=N} =
{ (rho_A, G_A) for every nonempty A subset [N] :
    rho_A in X_A,
    Tr_{A\B}(rho_A) ~_B rho_B for every B subset A,
    G_A = InducedGeometry(X_A) }
```

Extension fibers:

```text
F_n(rho_B) = { rho_A in X_A : Tr_{A\B}(rho_A) ~_B rho_B }
```

Cut lattice count:

```text
number of nontrivial bipartitions for n qubits = 2^(n-1) - 1
```

Examples:

```text
1q: 0 cuts
2q: 1 cut
3q: 3 cuts
4q: 7 cuts
8q: 127 cuts
```

Schmidt strata per cut:

```text
rank tuple = (rank across cut_1, rank across cut_2, ...)
```

The current tower:

```text
system_v7/sims/finite_probe_quotient_inverse_limit_tower_1q_through_4q
```

earned a real scratch tower through 4q, but not completion. Open issues: full-negative roster, gate scanner bug, stronger boundary states, exact 4q forecast, and fresh-context audit.

## 9. QCA / Hopfield Memory Fixture

Current fixture support:

```text
S = {0,1}^4
```

Ring majority update:

```text
f(x)_i = 1 iff x_{i-1} + x_i + x_{i+1} >= 2
```

Named memory states:

```text
m_0 = 0000
m_1 = 1111
```

Open diagonal transition:

```text
T[x,y] = (1-p)/|S| + p * 1{ y = f(x) }
```

Steady state:

```text
pi T = pi
sum_y pi_y = 1
```

Readouts:

```text
basin assignment entropy
diagonal von-Neumann/Shannon entropy of pi
fidelity to named memory states = sum_{x in {m_0,m_1}} pi_x
mutual information across cut {0,1}|{2,3}
false-memory rate
```

Blocked readout:

```text
coherent information
```

because the current channel is diagonal/classical and no non-diagonal CPTP channel or purification is earned.

This is:

```text
system_v7/sims/quantum_hopfield_qca_entropy_information_v0
```

It is not yet a quantum Hopfield sim. It is a finite diagonal open-channel memory-basin fixture.

## 10. Geometry Layers as Actual Objects

The layer list should be read as mathematical objects, not names.

```text
L0  root constraint on distinguishability
L1  finite quotient S/~_P
L2  density-rank strata and partial traces
L3  projective/spinor surface CP^(2^n-1), local S^3 -> S^2 skeleton
L4  local Weyl factors for product states
L5  higher-rung shells and Schmidt strata, not naive product tori
L6  metric/adjacency restricted to survivors
L7  connection A, curvature F=dA, holonomy, lift-erasure controls
L8  cut lattice
L9  Schmidt strata per cut
L10 entropy/readout availability per cut
L11 channel/order maps over already-built blocks
L12 regions discovered from observables, not installed by label
L13 runtime readout deltas after nesting and depth exist
L14 finite runner/QCA trajectories
L15 Clifford/chirality projectors
```

Deferred exceptional layers need licensing objects:

```text
G2:      7D real readout space W, pinned 3-form phi, preservation/closure tests
SU(3):   stabilizer inside licensed G2
Spin(7): 8D extension and Cayley form
Spin(8): explicit triality maps
F4:      27D Jordan target J3(O)
```

No layer is complete until the finite set, maps, controls, and receipts for that layer pass.

## 11. Current Sim Order from the Math

The correct order is:

```text
1. Fix definedness/name-math gate scope so ordinary math keys are not treated as primitive overclaims.
2. Normalize weakest-structure / forced-or-installed results.
3. Harden S/~_P quotient floor.
4. Harden 1q->4q inverse-limit tower.
5. Harden finite ring support S_ring and its three coordinate presentations.
6. Rebuild entropy co-ratchet on pinned support.
7. Extend spinor quotient discriminator from finite bins toward explicit Hopf table only where needed.
8. Harden QCA/Hopfield memory basin fixture.
9. Extract specs for overview-only targets before coding.
10. Build same-carrier geometry micro-legos.
11. Only then build downstream channel/order/region/axis candidates.
```

## 12. Exact Next Packet

The next packet should be:

```text
finite_ring_checkerboard_support_three_presentation_consistency_v0
```

because other current targets need a pinned finite support.

Required source object:

```text
S_ring = {L,R} x {eta_0,eta_1,eta_2} x Z_4 x Z_4
```

Required maps:

```text
flat_chart      : S_ring -> flat grid coordinates
shell_chart     : S_ring -> shell coordinates
ring_chart      : S_ring -> ring/fiber coordinates
density_probe   : S_ring -> Bloch/density row, phi-blind
phase_probe     : S_ring -> lifted phase/fiber row, phi-sensitive
adjacency_flat  : S_ring x S_ring -> {0,1}
adjacency_ring  : S_ring x S_ring -> {0,1}
```

Required equalities/invariants:

```text
|domain(flat_chart)| = |domain(shell_chart)| = |domain(ring_chart)| = 96
Q_density(flat) = Q_density(shell) = Q_density(ring)
phi erased under density probes
phi split under phase-sensitive probes
declared adjacency invariants agree
```

Required breaking controls:

```text
remove eta shell -> shell-sensitive classes merge
remove phi/fiber -> phase-sensitive classes merge
shuffle labels -> coordinate agreement fails unless invariant-only claim
change adjacency only -> adjacency readout fails while cardinality remains
inject presentation mismatch -> consistency gate fails
```

Required result fields:

```text
sim_id
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
source target path/hash
support table hash
presentation hashes
probe family
quotient classes
controls
demotion condition
blocked consumers
engine mode
```

This packet should not mention downstream labels except in `blocked_consumers`.

## 13. What Not To Do

Do not write:

```text
the manifold is built
the engine is real
Axis0 is open/closed
the physics emerges
terrain regions exist
the support is admitted
spinor is forced
density is enough
```

unless the result contains the finite object and the control that makes the sentence true.

Write:

```text
Under probe family P, quotient Q has k classes.
Removing probe p merges classes a and b.
Adding lifted probe l splits class c.
Applying A before B changes survivor set/readout r.
Geometry G_t was recomputed after the carve.
Density entropy is blocked because no rho/cut is earned.
The stronger carrier is installed but not forced because the weaker object passed the same probes.
```

That is the difference between doing the sims and narrating around them.
