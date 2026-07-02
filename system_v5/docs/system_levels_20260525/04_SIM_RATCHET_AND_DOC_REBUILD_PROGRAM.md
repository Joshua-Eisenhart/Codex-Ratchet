# Sim Ratchet And Doc Rebuild Program

Status: execution plan for formal and informal sims, not a completed proof.

## 1. Purpose

The new docs must be rebuilt by ratchet, not by prose confidence. Each layer or
map enters the docs only after it has one of:

```text
formal_scout receipt
blocked-reason artifact
source-grounded math packet
negative/control failure that killed it
```

The docs should preserve candidate sketches, but only as sketches. They should
not canonize the 13-layer outline, the 64-row schedule, the IJK flux candidate,
or any Axis0/Holodeck/physics bridge until the required lower gates are present.

## 2. Formal Sim Ratchet

Each formal phase has the same admission grammar:

```text
domain
codomain or output object
finite carrier/probe/operator/path set
N01 order witness
PEPS3D carrier anchor from first carrier step
torch-native spinor state or spinor-derived density
quaternion map/invariant if quaternion language is used
negative/control condition
receipt path
blocked downstream consumers
```

### Phase 0: Contract And Substrate Guard

Goal:

```text
no NumPy claim-bearing path
no dense-state closure for nonclassical claims
no Bloch/Cartesian/Pauli chart promoted to root geometry
all sims classify blockers and downstream consumers
```

Stop condition:

```text
lint red
contract field missing
NumPy or .numpy() leak in claim-bearing path
helper green but no movement and no blocked-reason artifact
```

### Phase 1: Finite Probe/Effect Quotient

Goal:

```text
finite effect family E
response assignment p_i
probe-relative identity quotient
finite noncommuting order witness
single-probe and commuting controls fail correctly
```

Max-scale expectation before promotion:

```text
multiple finite probe families, not just one qubit SIC fixture
Weyl-Heisenberg d=2 and d=3 or stronger
contextuality/process-POVM candidates tested or explicitly blocked
```

### Phase 2: PEPS3D Seed Carrier

Goal:

```text
K_0 = finite PEPS3D spinor-network carrier
finite effect/probe indices attached to sites/bonds/faces/cells
carrier survives flattened, wrong-adjacency, scalar-projection, and zero-tensor controls
```

Stop condition:

```text
PEPS3D appears only as scalar label
PEPS3D added after stages instead of at first carrier step
no explicit site/cell anchor for local readouts
```

### Phase 3: Spinor/Hopf/Weyl Enforcement

Goal:

```text
psi_v in S^3 on finite PEPS3D carrier
rho_v = psi_v psi_v^dagger as readout
nested Hopf tori T_eta with finite shell indices
A_Hopf explicit
fiber/base loop controls
left/right Weyl sheet cover
```

Max-scale expectation:

```text
8, 16, 32, 64 site rows where feasible
PEPS3D 64-site local carrier row where feasible
no claim that MPS transport equals PEPS3D closure
```

### Phase 4: Terrain Generator And Placement

Goal:

```text
X_(tau,s) for tau in {Se, Ne, Ni, Si}
Y_ell for ell in {fiber, base}
placement tuple (s, ell, tau, X, Y, token, sign)
16 placement design space tested with controls
```

Controls:

```text
wrong sheet
fiber/base erased
terrain-family shuffle
operator/terrain collapse
commuting-only replacement
```

### Phase 5: Operator Substage Cell Embedding

Goal:

```text
64 cells keyed by (engine, loop, terrain, operator)
each cell has local PEPS3D-carried spinor/Hopf state
each cell has channel/tensor action
each cell has order witness and negative control
Fe source/runtime mismatch repaired or blocked
```

Stop condition:

```text
only 16 macro-stage sites plus 4 row labels
operator rows not attached to local state/action
IGT or hexagram labels substituted for geometry
```

### Phase 6: PEPS/PEPS3D Closure Pressure

Goal:

```text
MPS transport separated from PEPS sheet and PEPS3D volume
local/subdense environment contractions tested
contraction-order boundary tested
gauge/normalization/tensor-topology controls
```

Claim ceiling:

```text
formal_scout until full PEPS3D environment theorem or explicit finite-size
closure contract exists
```

### Phase 7: Flux Candidate

Goal:

```text
J_flux = i J_i + j J_j + k J_k
literal quaternion algebra gate
spinor -> unit quaternion -> relative product or equivalent map
terrain/axis/operator schedule attached
scalar-only and j/k-erased controls fail correctly
```

Blocked until:

```text
carrier, terrain placement, substage cell, and PEPS3D boundary gates are
source-conformant enough for the exact flux consumer being tested
```

### Phase 8: Xi/Phi0/Axis0

Goal:

```text
Xi : geometry/history/flux -> rho_AB or equivalent cut object
Phi0 candidate family named and component-ablation tested
Axis0 zero semantics explicitly tested
terrain-square polarity and owner i-scalar genealogy preserved as separate inputs
```

Stop condition:

```text
Axis0 collapsed to i scalar
one entropy metric called final
flux component treated as Axis0
cut state chosen without controls
```

### Phase 9: Holodeck/FEP/Physics

Goal:

```text
finite predictive world carrier
finite cue/effect family
finite reconstruction candidate
finite noncommuting history update
finite action/path comparison
physics quantities mapped explicitly from admitted carrier/readout objects
```

Claim ceiling:

```text
candidate architecture or formal scout until physics map is proved with lower
gates and independent controls
```

## 3. Informal Sim Lane

The informal lane may explore aggressively, especially in `system_v5/grok_sim/`
or other isolated scratch surfaces, but it must not write formal claims into
`formal_scouts` or current docs without an audit gate.

Useful informal work:

```text
try weird carrier encodings
stress Axis0 zero interpretations
try IJK flux coefficient laws
try Holodeck/FEP recall-space toy worlds
find failure modes in stage/substage schedules
produce candidate fixtures for formal sims
```

Required boundary:

```text
informal success = fuel
informal failure = fuel
informal output != admission
informal output must name what formal gate it wants to challenge
```

## 4. Doc Ratchet

Docs should update in this order:

```text
1. record the source/result path
2. state exact claim ceiling
3. add the map/invariant/evidence
4. list controls and failures
5. name downstream consumers still blocked
6. only then revise diagrams or prose summaries
```

No doc should say "full manifold layer" unless the layer has:

```text
domain
map/invariant
finite PEPS3D carrier anchor
spinor or spinor-derived state
order witness
controls
receipt or explicit blocker
```

## 5. Current Next Moves

Immediate admissible work:

```text
repair Fe operator source/runtime mismatch
build the finite PEPS3D spinor-network seed from finite effect responses
embed one complete terrain/operator substage cell with controls
scale the substage-cell embedding to the 64-cell schedule only after one cell is clean
write blocked-reason artifacts for flux/Axis0/Holodeck if lower gates are not ready
```

Do not spend the next cycle proving Axis0, flux, or physics directly unless the
lower carrier and substage gates are already in the receipt chain.

