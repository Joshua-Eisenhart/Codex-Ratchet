# Manifold Geometry-Layer Stack — Noncommutative Order Ratchet (2026-05-28)

Status: active **working** program registry. This is the authoritative layer list, per-layer
minimum standard, and stacking gate. It is not a proof, not a completed stack, not a ratchet
result, not a G-structure selection, not Axis0/flux/FEP/physics admission, and not final
manifold admission. The noncommutative-order ratchet is the **hypothesis under test** (it only
becomes real if the pairwise/subset/stack tests below survive), not an established result.

## Corrected Program

```text
make the geometry layers as independent working legos
prove each has real finite action and controls
then test admissible nesting/order
then let the surviving order become the ratchet
```

`A then B != B then A`, and **the surviving order is the ratchet** — irreversible survivor
structure that accumulates because order matters. The "correct order" is the order that
**survives** the finite noncommutative tests, not the order that sounds natural from labels.

**G-structures are support / compatibility structures, not the center.** Axis0, flux, FEP, and
physics are **downstream** — they do not drive the layer build and remain blocked consumers.

## Individual Geometry Layers To Sim First

Each row needs its own full sim (parent-complete), not a label row.

```text
R0  root finite carrier/probe layer
      F01 finite carrier/probe/operator/path set
      N01 noncommuting/order-sensitive operation/control

L0  finite response/effect/path quotient
      what distinctions survive finite probes?

L1  spinor/density carrier
      torch-native spinors and spinor-derived density states

L2  S3 spinor carrier
      unit spinor / quaternionic carrier, NOT a Bloch-sphere substitution

L3  S2 projective / Hopf base
      projective base surface and quotient geometry

L4  Hopf fibration S3 -> S2 with U(1) fiber
      fiber/base split, phase, connection, holonomy

L5  nested Hopf tori / torus leaf family
      a real manifold geometry layer/sublayer, not just a side scout

L6  connection / holonomy geometry
      Berry / Wilczek-Zee-style holonomy, loop order, curvature, path memory

L7  Weyl spinor bundle
      left Weyl and right Weyl separately, then combined

L8  chirality orientation cover
      L/R sheet, gamma5 / Pin / Spin / reflection controls

L9  Clifford / quaternion module layer
      Cl3 / Cl6 action, rotors, geometric product, quaternion maps

L10 terrain / channel / generator layer
      finite local flow/channel law on the carrier

L11 operator-substage local cell layer
      allowed local operators as PEPS3D-carried cell/channel actions

L12 entropy / cut / communication layer
      QIT readouts over cuts/channels/paths; never scalar entropy as primary

L13 gluing / groupoid / dynamic transition layer
      compatibility of local patches, transitions, survivor dynamics
```

## Standalone Support Sims (needed before stacking, NOT the stack)

Stacking depends on these, but they are support/compatibility structure, not stack layers.

```text
G-structure candidates (support lattice; tested LAST, not winner-picked):
  U(1), SU(2)/Spin(3)/Sp(1), SO/Spin/Pin, Spin^c,
  SU(3)/Calabi-Yau-like, G2, Spin(7), Clifford module structures,
  possible hybrid reduction chain

carrier/tool structures:
  MPS view, PEPS2D view, PEPS3D finite K=(V,E,F,C) view,
  spinor-network payloads, contraction/readout tools,
  graph/hypergraph/cell-complex topology

entropy families:
  von Neumann, Renyi, mutual information, conditional entropy,
  coherent information, log negativity, path entropy,
  shell/cut entropy, holonomy/order-sensitive readouts
```

These are not a "G2 vs Spin7 vs SU3 winner" bake-off. They are the support lattice and toolset
that the surviving geometry stack must be carried by; G-structure admissibility is the LAST step.

## Minimum Standard For Each Individual Layer

A layer is not ready for stacking until its receipt has:

```text
finite_map: domain -> codomain_or_output
F01 witness
N01 witness
torch-native spinor or spinor-derived density
PEPS3D K=(V,E,F,C) anchor where manifold geometry is claimed
MPS / PEPS2D / PEPS3D comparison where relevant
8 / 16 / 32 / 64 qubit-site stress or explicit resource blocker
tool manifest with load-bearing tools, not decorative imports
non-vacuous ablation_outcome_delta
QIT entropy/readouts as derived outputs
negative controls
blocked consumers
fresh rerun result
```

Realness enforcement: each parent-complete layer receipt must clear
`scripts/validate_layer_distinctness.py` (zero HARD) — no cross-layer signature identity, no
fabricated/vacuous tool ablations, no vacuous scale ladder, no fenced-away real controls. The
tool ablations must be real removed-and-re-run deltas (numeric) or genuine present->absent
certificates (proof/topology/geometry), not hardcoded passes. This is what makes a later order
test a real test rather than a relabel artifact.

## What Allows Stacking

Stacking opens for a pair only when both parent layers have:

```text
same carrier, or an explicit finite projection P between carriers
compatible spinor payloads / spinor-derived densities
compatible PEPS3D site/bond/face/cell anchors
preserved phase, chirality, shell, and Hopf metadata
compatible cuts / readout provenance
an N01 order gap inside EACH parent
controls proving the gap collapses when order/phase/chirality/carrier is erased
tool receipts showing the interface is real
```

First stacking test is pairwise only:

```text
Layer A then Layer B   vs   Layer B then Layer A
```

```text
A∘B == B∘A                      -> no ratchet at that pair
A∘B != B∘A and controls collapse -> real order pressure at that pair
```

Only after pairwise tests: small subsets, then the larger geometry stack. The correct order is
the surviving order, not the label-natural one.

## Mapping Existing Sims Onto The New Numbering (nothing discarded)

The prior compressed L0-L8 shorthand is renumbered into R0+L0-L13. The previous `L7 Hopf` row
compressed five real layers; the previous `L2 Weyl` row split into two.

| New layer | Source / existing sim | State |
|---|---|---|
| R0 root finite carrier/probe | F01/N01 harness root; no dedicated sim | **build** |
| L0 finite response/effect/path quotient | old L0 response/effect/path quotient | sim exists, in progress |
| L1 spinor/density carrier | old L1 boundary/environment (partial) | needs dedicated carrier sim |
| L2 S3 spinor carrier (no Bloch substitution) | geometry scout S3_spinor_carrier (input) | **build** — current carriers use Bloch reductions in places (e.g. pyg features); a genuine S3/quaternionic carrier sim is required |
| L3 S2 projective/Hopf base | old L7 Hopf (compressed); scout S2_Hopf_base_surface | **build** |
| L4 Hopf fibration S3->S2 U(1) | old L7 Hopf (compressed); scout Hopf_fibration_S3_to_S2 | **build** |
| L5 nested Hopf tori / torus leaf | scout Nested_Hopf_tori (was side scout) | **build — restored as a layer** |
| L6 connection/holonomy geometry | old L7 Hopf (compressed) | **build** |
| L7 Weyl spinor bundle | old L2 Weyl (gamma5 carrier) | partial — gamma5 left/right Weyl built; FSN+bond4 receipts pass gate |
| L8 chirality orientation cover | old L2 chirality (gamma5/sheet controls) | partial — sheet_collapsed now load-bearing; needs Pin/Spin/reflection controls |
| L9 Clifford/quaternion module | old L3 Clifford/quaternion | sim exists |
| L10 terrain/channel/generator | old L4 | sim exists |
| L11 operator-substage local cell | old L5 | sim exists |
| L12 entropy/cut/communication | old L6 | sim exists |
| L13 gluing/groupoid/dynamic | old L8 | sim exists |

Main build gap: **R0 root and the Hopf region (new L2-L6) — S3 carrier, S2 base, Hopf
fibration, nested Hopf tori, connection/holonomy** — plus completing Weyl/chirality (L7/L8). The
downstream layers (L9-L13) have existing sims that must be re-checked against the minimum
standard and the realness gate, not assumed complete.

## Construction Dependency (build order is forced, not bookkeeping)

```text
finite probes/effects
-> finite PEPS3D-carried spinor network
-> nested Hopf torus / shell / loop geometry
-> left/right Weyl sheet cover
-> terrain generator
-> operator substage
```

The layer below terrain is the **Weyl-Hopf-loop carrier**: the row number is secondary to the
construction dependency. Build bottom-up: R0 -> L1 -> L2..L6 (Hopf region) -> L7/L8 (Weyl) ->
L9 (Clifford) -> L10 (terrain) -> L11 (operator substage) -> L12 -> L13.

Below-terrain carrier objects each layer must actually sim (not label):
```text
K=(V,E,F,C);  psi_v in S^3 subset C^2;  T_eta_k = {(e^{i phi} cos eta_k, e^{i chi} sin eta_k)}
pi_H(psi) = psi^dag sigma psi in S^2;   A_Hopf = d phi + cos(2 eta) d chi
rho_{v,L,k}=psi_{v,L,k} psi_{v,L,k}^dag;  rho_{v,R,k}=...;  H_L=+H0, H_R=-H0
```

## Terrain Layer Standard (L10) — terrains are GKSL vector fields, not labels

A terrain generator is indexed `X_{tau,s,ell,k} : rho_{v,s,k} -> rho_dot`, with v=site/cell,
k=shell/Hopf-torus index, s=L/R Weyl sheet, ell=loop field (fiber/base, in/out),
tau=terrain family (the 8 generators: Funnel/Vortex/Pit/Hill_L, Cannon/Spiral/Source/Citadel_R),
each in GKSL form `X = -i[H_s, rho] + sum_k D[L_k](rho)`, `D[A](rho)=A rho A^dag - 1/2{A^dag A, rho}`.

```text
finite-time channel:  Phi^t_{a,s} = exp(t X_{a,s})
terrain basin:        B_{a,s}(eps,T) = { rho0 : d(Phi^T(rho0), A_{a,s}) < eps }, A_{a,s} DISCOVERED
fixed point:          X(rho*) = 0 ; period-p cycle nontrivial only if shorter periods fail
program:              many seeds rho0^(m) -> Phi^T -> cluster/invariant/basin test
parent basins:        B_L = union_a B_{a,L},  B_R = union_a B_{a,R}
terrain sub-basin:    d(A_{a,s},A_{b,s})>delta AND erasing the generator terms collapses B_{a,s}
readouts:             S, I(A:B), S(A|B), I_c, log-negativity MEASURE the dynamics; they do not define it
order test (after basins exist):  Delta_{a,b,s}(rho)=|| Phi_a Phi_b rho - Phi_b Phi_a rho ||_1
ratchet schedule:     d(Phi_D(rho), Phi_I(rho)) > delta with work/readout change + wrong-order controls failing
```

## Dependency-Forcing Discipline (the terrain-from-manifold test)

A layer is real-as-part-of-the-manifold only if **erasing the layer-below geometry collapses it**.
Beyond the per-layer realness gate, each geometry layer's controls MUST include manifold-erasure
controls that destroy or merge its signature:

```text
erase Hopf connection A_Hopf;  collapse nested-torus index k;  erase loop field ell;
merge L/R Weyl sheets;  set H_L = H_R;  swap sigma_- <-> sigma_+;
make all terrain generators identical;  scramble terrain-family assignment;
remove finite PEPS3D site/cell anchor
```

If the layer still "works" after these, the sim proved only that some hand-written channels run --
NOT that the geometric constraint manifold forces the structure. The forcing map to sim is
`G : (K, psi_v, T_eta_k, A_Hopf, Y_ell, s) -> {X_{tau,s,ell,k}}` and its question is whether the
lower geometry forces/constrains the terrain generators or they are chosen by hand.

## Parallel Compute

Heavy parallel work (many-seed terrain basin sweeps, independent per-layer scaffolds) may use the
Workflow fan-out or the owner-cleared codex2 TUI (codex 5.5). Fabrication risk stands: every
agent/codex-produced sim is verified by reading its code AND running it through both gates
(validate_formal_scout_results + validate_layer_distinctness) before it counts.

## Status Discipline

```text
authoritative layer registry:        this doc (R0 + L0-L13) + construction dependency above
parent-complete + double-gate-passing: R0 (root) DONE; L1 (spinor/density carrier) DONE
gamma5 partial:                       L7/L8 (Weyl bundle / chirality cover) -- FSN+bond4 receipts pass; not yet full L7/L8 sims
nested_hopf_tori restored as layer:   yes (L5; sim to build)
main build gap (bottom-up next):      L2 S3 carrier -> L3 S2 base -> L4 Hopf fibration -> L5 nested Hopf tori -> L6 connection/holonomy
L9-L13 existing sims:                 unverified to the minimum standard + dependency-forcing
dependency-forcing controls:          required per layer; not yet added to L2-L13
G-structure role:                     support lattice, tested LAST, not a driver
Axis0 / flux / FEP / physics:         downstream blocked consumers, not drivers
order tests / pairwise / stack:       none yet (gated behind parent-complete + realness gate + dependency-forcing)
noncommutative ratchet:               HYPOTHESIS under test, not established
```
