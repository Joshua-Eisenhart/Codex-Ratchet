# QIT Engine, Geometry, Entropy, and Bridge Master Table

**Date:** 2026-03-30  
**Status:** Working support surface. This is not a doctrine rewrite. It is a compact controller/reference table that keeps the current ratchet order explicit and separates live runtime math from still-open bridge math.

---

## Purpose

This packet answers four questions in one place:

1. what math is already live in the QIT engine
2. what geometry is already live in the constraint-manifold ladder
3. what entropy math is being processed now
4. where the still-open bridge into `Axis 0` begins

Core separation rule:

- carrier / geometry is not the same thing as the engine
- engine runtime is not the same thing as the final `Axis 0` kernel
- runtime entropy/control math is not the same thing as the final cut-state entropy family

---

## Status Legend

| Label | Meaning |
|---|---|
| `live base` | already used as foundational math in current probes/runtime |
| `live geometry` | directly simulated as geometry, not just mentioned |
| `live engine` | actively used in executable engine runtime |
| `live proxy` | executable and useful, but not final doctrine by itself |
| `live candidate` | strong active candidate family, but not finally closed |
| `open bridge` | depends on the unresolved `Xi : geometry/history -> rho_AB` choice |
| `proposal pressure` | useful current proposal or rebinding pressure, not canon |

---

## Master Table

| Ratchet Order | Layer | Object / Math | Pure Math | Role In Stack | Used In Engine Now | Used In `Ax0` Now | Status | Primary Surfaces |
|---|---|---|---|---|---|---|---|---|
| 1 | root | root constraints | `F01_FINITUDE`, `N01_NONCOMMUTATION` | admissibility charter; forbids free infinitude and swap-by-default | indirect | no | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md` |
| 2 | admission | admissible finite math | finite Hilbert/operator/probe language | legal math family that can live on the constrained manifold | yes | indirect | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `AXIS_0_1_2_QIT_MATH.md`, `AXIS_3_4_5_6_QIT_MATH.md` |
| 3 | carrier | qubit Hilbert carrier | `H = C^2` | minimal spinor/state carrier | yes | indirect | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `hopf_manifold.py` |
| 4 | probes | observables / probes | `O = O^dagger`, `p_O(rho)=Tr(O rho)` | admissible readout and witness layer | yes | indirect | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `axis0_full_spectrum_sim.py` |
| 5 | state math | density matrices | `rho >= 0`, `Tr(rho)=1` | actual runtime state object for sheets, shells, and candidate cuts | yes | yes | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `engine_core.py`, `geometric_operators.py` |
| 6 | algebra | Pauli basis | `I`, `sigma_x`, `sigma_y`, `sigma_z`, `sigma_-`, `sigma_+` | Bloch coordinates, Hamiltonian basis, dissipative generators, noncommutation witness | yes | indirect | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `engine_core.py`, `geometric_operators.py` |
| 7 | algebra | Bloch/density form | `rho = 1/2 (I + r·sigma)` | converts spinor and density language into observable coordinates | yes | indirect | `live base` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `hopf_manifold.py` |
| 8 | algebra | unitary generators | `U_x(theta)`, `U_z(phi)` | engine rotation family for F-class operators | yes | indirect | `live engine` | `geometric_operators.py` |
| 9 | algebra | CPTP / dephasing maps | projection/dephasing channels on `2x2` densities | engine T-class operators and dissipative constraint dynamics | yes | indirect | `live engine` | `geometric_operators.py` |
| 10 | geometry | normalized spinor carrier | `S^3 = {psi in C^2 : ||psi|| = 1}` | direct carrier geometry for normalized spinors | yes | indirect | `live geometry` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `sim_L0_s3_valid.py`, `hopf_manifold.py` |
| 11 | geometry | Hopf map | `pi(psi)=psi^dagger sigma psi in S^2` | projects carrier geometry into Bloch sphere coordinates | yes | indirect | `live geometry` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `sim_L0_s3_valid.py`, `hopf_manifold.py` |
| 12 | geometry | Bloch sphere | `S^2` | observable/projected geometry downstream of the spinor carrier | yes | indirect | `live geometry` | `sim_L0_s3_valid.py`, `hopf_manifold.py` |
| 13 | geometry | density reduction from spinor | `rho(psi)=|psi><psi|` | bridge from spinor geometry to density-state math | yes | indirect | `live geometry` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `hopf_manifold.py` |
| 14 | geometry | Hopf chart | `psi(phi,chi;eta)` | local chart for carrier/torus parametrization | yes | indirect | `live geometry` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `hopf_manifold.py` |
| 15 | geometry | nested Hopf tori | `T_eta subset S^3`, including Clifford torus `T_{pi/4}` | strong current torus realization and latitude organization inside `S^3` | yes | seat only | `live geometry` | `AXIS0_GEOMETRIC_CONSTRAINT_MANIFOLD.md`, `axis0_full_constraint_manifold_guardrail_sim.py`, `sim_weyl_geometry_ladder_audit.py` |
| 16 | geometry | fiber/base loop split | `gamma_fiber`, `gamma_base`, horizontal condition `A(dot gamma_base)=0` | direct carrier-path split; strongest current geometry witness behind `Ax3` pressure | yes | indirect | `live geometry` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `sim_Ax3_density_path.py`, `axis0_full_constraint_manifold_guardrail_sim.py` |
| 17 | geometry | Weyl ambient sheets | `psi_L`, `psi_R` on the constrained carrier | left/right ambient sheet structure above direct carrier geometry | yes | indirect | `live geometry` + `proposal pressure` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `PROTO_RATCHET_WEYL_MANIFOLD_SHIFT_PROPOSAL.md`, `sim_weyl_ambient_vs_engine_overlay.py`, `sim_weyl_geometry_ladder_audit.py` |
| 18 | geometry/state | Weyl sheet densities | `rho_L = psi_L psi_L^dagger`, `rho_R = psi_R psi_R^dagger` | runtime sheet states for engine traversal and bridge experiments | yes | indirect | `live engine` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `engine_core.py` |
| 19 | engine | engine family grammar | `2 engine types x 2 loops x 8 macro-stages x 4 operator slots` | executable runtime topology for the current QIT engine | yes | no | `live engine` | `ENGINE_KERNEL_MINIMAL.md`, `engine_core.py`, `sim_L6_master_engine.py` |
| 20 | engine | operator family | `Ti`, `Fe`, `Te`, `Fi` | four runtime actions that traverse, constrain, rotate, and dephase engine states | yes | no | `live engine` | `geometric_operators.py`, `sim_Ax4_commutation.py`, `sim_Ax5_TF_kernel.py` |
| 21 | engine | current operator math | `Ti` projection/dephasing, `Fe` = `U_z(phi)`, `Te` = `sigma_x`-basis dephasing, `Fi` = `U_x(theta)` | concrete implementation of the operator family | yes | no | `live engine` | `geometric_operators.py` |
| 22 | engine | terrain / addressing scaffold | `16` macro-stages, `64` subcycle steps | structural runtime scaffold and address lattice for the engine | yes | no | `live engine` | `engine_core.py`, `sim_L6_master_engine.py`, `qit_graph_engine_alignment_probe.py` |
| 23 | entropy | single-state von Neumann entropy | `S(rho) = -Tr(rho log rho)` | mixedness measure used in runtime and candidate cut-state math | yes | yes | `live base` | `PROTO_RATCHET_ENTROPY_ALIGNMENT.md`, `engine_core.py` |
| 24 | entropy | runtime negentropy proxy | `log(2) - S(rho)` | executable local control / structure-gain proxy in the engine | yes | no | `live proxy` | `engine_core.py`, `geometric_operators.py` |
| 25 | entropy | runtime entropy deltas | `delta_phi`, shell deltas, bookkeeping deltas | tracks local state-change effects through the engine | yes | no | `live proxy` | `engine_core.py`, `axis0_full_spectrum_sim.py` |
| 26 | entropy | torus entropy seat | entropy of torus-orbit/coarse-grained states, including latitude dependence | current geometric seat for `Ax0` pressure without claiming final closure | indirect | seat only | `live proxy` | `AXIS0_GEOMETRIC_CONSTRAINT_MANIFOLD.md`, `axis0_full_constraint_manifold_guardrail_sim.py` |
| 27 | entropy | runtime `ga0` proxy | executable `ga0_level` control signal | live engine control proxy; not final `Ax0` doctrine | yes | no | `live proxy` | `engine_core.py` |
| 28 | bridge | direct local sheet coupling | raw local `L|R` / sheet-level coupling | control comparison only; too weak as final `Ax0` object | yes | comparison only | `live proxy` | `sim_weyl_ambient_vs_engine_overlay.py`, `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md` |
| 29 | bridge | bridge family | `Xi : geometry/history -> rho_AB` | maps geometry/history/runtime surfaces into a true bipartite cut-state candidate | no | yes | `open bridge` | `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`, `axis0_xi_strict_bakeoff_sim.py` |
| 30 | bridge | point-reference / shell / history bridges | `Xi_ref`, `Xi_shell`, `Xi_hist` and related shell/global forms | strongest current discriminators for building `rho_AB` from geometry/history | no | yes | `open bridge` | `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`, `axis0_xi_strict_bakeoff_sim.py` |
| 31 | cut state | bipartite cut-state family | `rho_AB`, `rho_A`, `rho_B` | required object family before `Axis 0` entropy kernels are meaningful | no | yes | `open bridge` | `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`, `axis0_full_spectrum_sim.py` |
| 32 | Ax0 family | mutual information | `I(A:B) = S(rho_A)+S(rho_B)-S(rho_AB)` | unsigned total-correlation guardrail and companion diagnostic | no | yes | `live candidate` | `PROTO_RATCHET_ENTROPY_ALIGNMENT.md`, `axis0_full_spectrum_sim.py` |
| 33 | Ax0 family | conditional entropy | `S(A|B)=S(rho_AB)-S(rho_B)` | signed cut entropy family | no | yes | `live candidate` | `PROTO_RATCHET_ENTROPY_ALIGNMENT.md`, `axis0_full_spectrum_sim.py` |
| 34 | Ax0 family | coherent information | `I_c(A>B)=-S(A|B)=S(rho_B)-S(rho_AB)` | strongest simple signed `Ax0` candidate in the current stack | no | yes | `live candidate` | `PROTO_RATCHET_ENTROPY_ALIGNMENT.md`, `axis0_full_spectrum_sim.py`, `axis0_xi_strict_bakeoff_sim.py` |
| 35 | probes | live probe suite | geometry, engine, bridge, and axis probes | executable witness layer for kill tests, support, and discriminators | yes | yes | `live engine` + `live geometry` | `sim_L0_s3_valid.py`, `sim_L6_master_engine.py`, `sim_Ax3_density_path.py`, `axis0_full_constraint_manifold_guardrail_sim.py`, `axis0_xi_strict_bakeoff_sim.py`, `sim_weyl_ambient_vs_engine_overlay.py`, `sim_Ax3_Ax4_rebinding_stress.py`, `sim_weyl_geometry_ladder_audit.py` |
| 36 | sidecar | graph/runtime sidecars | owner graph, runtime overlays, history packets | structure/alignment/audit layer around the engine; not the geometry itself | yes | no | `live proxy` | `QIT_GRAPH_RUNTIME_MODEL.md`, `qit_graph_engine_alignment_probe.py` |

---

## Current Best Ratchet Order

This is the clean current order if geometry, engine math, entropy math, and bridge math are all kept separate:

1. root constraints  
2. admissible finite math  
3. qubit / spinor / density / probe base math  
4. Pauli / Bloch / `SU(2)` algebra  
5. `S^3` carrier geometry  
6. Hopf / Bloch reduction  
7. nested Hopf-torus organization inside `S^3`  
8. fiber/base loop split  
9. Weyl ambient sheet structure  
10. engine family grammar and operator dynamics on that geometry  
11. runtime entropy / negentropy / `ga0` proxy processing  
12. bridge family `Xi : geometry/history -> rho_AB`  
13. cut-state entropy family for `Axis 0`  

---

## Key Split To Preserve

The strongest current separation is:

| Layer | What it is not |
|---|---|
| root constraints | not geometry |
| geometry | not the engine |
| engine runtime | not the final `Axis 0` kernel |
| runtime entropy/control proxies | not the final `Axis 0` cut-state family |
| nested Hopf tori | not yet proven to be the final outermost geometry |
| Weyl working layer | not yet fully canon as the terminal ambient manifold, but stronger than a mere toy overlay |

Short read:

- base QIT math is live
- real geometry is live
- Weyl ambient structure is live enough to matter
- the engine is live
- the main open gap is still the bridge into the true `Axis 0` cut-state family

---

## Primary Read Order From This Packet

1. `system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`
2. `system_v4/docs/ENGINE_KERNEL_MINIMAL.md`
3. `system_v4/docs/AXIS0_GEOMETRIC_CONSTRAINT_MANIFOLD.md`
4. `system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`
5. `system_v4/docs/PROTO_RATCHET_ENTROPY_ALIGNMENT.md`
6. `system_v4/docs/PROTO_RATCHET_WEYL_MANIFOLD_SHIFT_PROPOSAL.md`
7. `system_v4/docs/PROTO_RATCHET_WEYL_SIM_RESULTS_2026_03_30.md`
