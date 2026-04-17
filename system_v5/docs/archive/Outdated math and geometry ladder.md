Here’s the cleanest current table I can give you.

**Math And Geometry Ladder**

| Layer | Object / Math | Used Now? | Status In Repo | Main Surfaces |
|---|---|---:|---|---|
| 0 | root constraints `F01_FINITUDE`, `N01_NONCOMMUTATION` | Yes | doctrine / admission layer, not a direct sim object | [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md) |
| 1 | admissible finite QIT math | Yes | live working basis | [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_0_1_2_QIT_MATH.md), [AXIS_3_4_5_6_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md) |
| 2 | complex Hilbert space / spinor state space | Yes | live working basis | [hopf_manifold.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/hopf_manifold.py) |
| 3 | density matrices `rho`, bipartite `rho_AB` candidates | Yes | heavily used; final Ax0 bridge target still open | [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py), [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) |
| 4 | Pauli matrices / SU(2) / Bloch machinery | Yes | live and foundational | [hopf_manifold.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/hopf_manifold.py), [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) |
| 5 | `S^3 = SU(2)` carrier | Yes | strongly simulated | [sim_L0_s3_valid.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L0_s3_valid.py) |
| 6 | Hopf map `S^3 -> S^2` | Yes | strongly simulated | [sim_L0_s3_valid.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L0_s3_valid.py), [hopf_manifold.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/hopf_manifold.py) |
| 7 | Bloch sphere `S^2` | Yes | downstream observable/projection layer | [sim_L0_s3_valid.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L0_s3_valid.py) |
| 8 | torus chart / Clifford torus / nested Hopf tori `T_eta` | Yes | real working geometry, not final primitive layer | [axis0_full_constraint_manifold_guardrail_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_constraint_manifold_guardrail_sim.py), [sim_weyl_geometry_ladder_audit.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_geometry_ladder_audit.py) |
| 9 | fiber loop vs base-lift loop | Yes | strongly simulated and operationally important | [sim_Ax3_density_path.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_Ax3_density_path.py), [axis0_full_constraint_manifold_guardrail_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_constraint_manifold_guardrail_sim.py) |
| 10 | left/right Weyl spinors `psi_L`, `psi_R` | Yes | live working geometry layer; stronger than before | [hopf_manifold.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/hopf_manifold.py), [sim_weyl_ambient_vs_engine_overlay.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_ambient_vs_engine_overlay.py) |
| 11 | left/right Weyl densities `rho_L`, `rho_R` | Yes | live runtime layer | [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py), [axis0_full_constraint_manifold_guardrail_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_constraint_manifold_guardrail_sim.py) |
| 12 | engine DOF / terrain / operator grammar | Yes | live executable engine | [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py), [sim_L6_master_engine.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L6_master_engine.py) |
| 13 | operator families `Ti, Fe, Te, Fi` / ordering / noncommutation | Yes | live and probed | [sim_Ax4_commutation.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_Ax4_commutation.py), [sim_Ax5_TF_kernel.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_Ax5_TF_kernel.py) |
| 14 | runtime history windows / history packets | Yes | live as probe/runtime surfaces | [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py), [QIT_GRAPH_RUNTIME_MODEL.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/QIT_GRAPH_RUNTIME_MODEL.md) |
| 15 | bridge families `Xi_ref`, `Xi_hist`, `Xi_shell`, direct `L|R` control | Yes | partially live; still open doctrinally | [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md), [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) |
| 16 | Ax0 kernels `-S(A|B)`, `I_c`, `I(A:B)` | Yes | live candidate family, not finally closed | [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md), [axis0_full_spectrum_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_full_spectrum_sim.py) |
| 17 | graph/runtime/history sidecars | Yes | aligned enough to start using; not the geometry itself | [QIT_GRAPH_RUNTIME_MODEL.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/QIT_GRAPH_RUNTIME_MODEL.md), [qit_graph_engine_alignment_probe.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/qit_graph_engine_alignment_probe.py) |

**Current Ratchet Order**
This is the best current ordering, mixing canon, working, and proposal layers carefully:

1. root constraints  
2. admissible finite math  
3. spinor/Hilbert carrier  
4. density/Pauli/SU(2) machinery  
5. `S^3` carrier  
6. Hopf reduction to `S^2`  
7. torus organization / nested Hopf tori  
8. left/right Weyl working layer  
9. engine DOF and terrain/operator grammar  
10. runtime/history surfaces  
11. bridge family `Xi : geometry/history -> rho_AB`  
12. Ax0 kernel on the resulting cut-state

**Most Important Caveat**
The repo still does **not** fully close these as one finished theorem:

- roots uniquely force the Weyl manifold
- nested Hopf tori are the final geometry
- the exact Ax0 bridge is solved

So the strong current read is:

- base math: live
- real geometry: live
- Weyl layer: live
- engine: live
- bridge to Ax0: still open

If you want, next I can turn this into a second table with just:

- `fully simulated`
- `partially simulated`
- `only proposed / not yet honestly simmed`



Yes, you’re right. I left out two central things:

1. the **math of the QIT engine itself**
2. the **math of the entropy being processed by that engine**

Here’s the cleaner version.

**QIT Engine Math**

| Layer | Math | What It Does | Live Where |
|---|---|---|---|
| carrier | Weyl spinors on `S^3 / SU(2)` | primary constrained state carrier | [ENGINE_KERNEL_MINIMAL.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/ENGINE_KERNEL_MINIMAL.md), [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) |
| reduced state | density matrices `rho_L`, `rho_R` | working state objects the engine updates | [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) |
| Lie/algebra basis | Pauli matrices `sigma_x, sigma_y, sigma_z` and `SU(2)` unitaries | generator basis for rotations and channels | [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py) |
| geometric charts | Hopf map, Bloch projection, torus coordinates, fiber action | connect spinor geometry to observable structure | [hopf_manifold.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/hopf_manifold.py) |
| operator dynamics | CPTP maps on `2x2` density matrices | actual engine actions per step | [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py) |
| engine grammar | 2 engine types x 2 loops x 8 macro-stages x 4 operators | runtime topology/order of the engine | [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) |

The actual operator math in the current engine is:

- `Ti`: projection / dephasing-style constraint map
- `Fe`: `U_z(phi)` unitary rotation
- `Te`: `sigma_x`-basis dephasing channel
- `Fi`: `U_x(theta)` unitary rotation

Those are explicit in [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py).

So the current engine is mathematically:
- a **Weyl-spinor-carried**
- **density-matrix-updating**
- **Pauli/SU(2)-based**
- **CPTP / unitary hybrid**
- **geometric runtime** on Hopf / torus structure.

**Entropy Math Being Processed**

There are really **two entropy layers** in the repo.

| Entropy Layer | Math | Role | Status |
|---|---|---|---|
| runtime engine entropy | coarse-grained local sheet entropy / negentropy proxies | used to drive and monitor engine behavior now | live runtime proxy |
| Ax0 bridge entropy | cut-state entropy families like `S(rho)`, `I(A:B)`, `S(A|B)`, `I_c` | candidate real Ax0 math after a bridge `Xi` into `rho_AB` | partially live, not finally closed |

The current runtime engine entropy math is mostly:

- `S(rho)` via von Neumann entropy on sheet densities
- `negentropy = log(2) - S(rho)`
- `delta_phi = negentropy(after) - negentropy(before)`
- `ga0_level` as a runtime control proxy
- torus/fiber coarse-graining as the mechanism shaping that proxy

That is live in:
- [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py)
- [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py)

Important nuance:
- this runtime entropy is **not yet the final Ax0 doctrine math**
- it is the current executable control/proxy layer

The current Ax0-facing entropy family, once a real bridge exists, is:

- von Neumann entropy:
  - `S(rho) = -Tr(rho log rho)`
- mutual information:
  - `I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)`
- conditional entropy:
  - `S(A|B) = S(rho_AB) - S(rho_B)`
- coherent information:
  - `I_c(A->B) = -S(A|B) = S(rho_B) - S(rho_AB)`

That ranking is explicit in [PROTO_RATCHET_ENTROPY_ALIGNMENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ENTROPY_ALIGNMENT.md).

Current best read from the repo:
- `I_c = -S(A|B)` is the strongest simple signed `Ax0` candidate
- `I(A:B)` is important, but diagnostic/companion
- `S(rho)` alone is too weak to be the real Ax0 kernel
- all of that is still downstream of the unresolved bridge `Xi`

**Order In The Ratchet**
If we include engine math and entropy math properly, the order is more like:

1. root constraints  
2. admissible finite math  
3. Weyl spinor carrier  
4. density matrices / Pauli / SU(2) base math  
5. `S^3` carrier  
6. Hopf / Bloch reduction  
7. nested Hopf-torus organization  
8. Weyl left/right working layer  
9. engine grammar and CPTP/unitary operator dynamics  
10. runtime entropy / negentropy / `ga0_level` proxy processing  
11. bridge family `Xi : geometry/history -> rho_AB`  
12. Ax0 cut-state entropy kernel (`I_c`, `S(A|B)`, `I(A:B)`, etc.)

So the clean answer is:

- **the QIT engine math is live**
  - Weyl spinors
  - density matrices
  - Pauli/SU(2)
  - CPTP maps and unitaries
  - Hopf/torus geometry
- **the entropy math is also live**
  - but split into:
    - current runtime proxy entropy
    - later Ax0 bridge/cut entropy family

And the missing closure is still:
- the exact bridge from the engine’s live geometry/history into the final bipartite cut-state that Ax0 should evaluate.

If you want, I can next make one **single unified table** with columns:

- `math object`
- `used in engine now`
- `used in Ax0 now`
- `runtime proxy vs final doctrine`
- `file refs`



Yes, those should have been listed explicitly. Here’s the missing core.

**Engine Math**

| Order | Math Object | Pure Math | Role In Engine | Status |
|---|---|---|---|---|
| 1 | Weyl spinor carrier | `psi_L, psi_R in C^2`, normalized on `S^3` | primary constrained state carrier | live |
| 2 | density matrices | `rho_L = psi_L psi_L^dagger`, `rho_R = psi_R psi_R^dagger` | actual runtime state objects updated by the engine | live |
| 3 | Pauli basis | `sigma_x, sigma_y, sigma_z` | algebraic basis for Bloch coordinates, Hamiltonians, projectors, channels | live |
| 4 | qubit state form | `rho = 1/2 (I + r·sigma)` | Bloch/density representation of each sheet | live |
| 5 | unitary generators | `U_x(theta)`, `U_z(phi)` | rotation-class operators | live |
| 6 | dissipative/CPTP maps | dephasing/projection channels | T-kernel / constraint class operators | live |
| 7 | operator family | `Ti, Fe, Te, Fi` | the 4 engine actions | live |
| 8 | engine grammar | `2 engine types x 2 loops x 8 macro-stages x 4 operator slots` | actual executable topology | live |
| 9 | geometric transport | `eta, theta1, theta2`, torus transport, fiber coarse-graining | moves runtime state on the simulated manifold | live |

Main files:
- [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py)
- [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py)
- [AXIS_3_4_5_6_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md)

**Current Operator Math**

| Operator | Math | Class |
|---|---|---|
| `Ti` | projection / dephasing toward computational basis | T / constraint |
| `Fe` | `rho -> U_z(phi) rho U_z(phi)^dagger` | F / rotation |
| `Te` | `sigma_x`-basis dephasing channel | T / dissipative |
| `Fi` | `rho -> U_x(theta) rho U_x(theta)^dagger` | F / rotation |

That’s explicit in [geometric_operators.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/geometric_operators.py).

**Entropy Math**

There are really **two entropy layers**.

| Order | Entropy Math | Pure Math | Role | Status |
|---|---|---|---|---|
| A | runtime entropy proxy | `S(rho)`, negentropy, `delta_phi` | local engine control / structure-gain bookkeeping | live proxy |
| B | torus entropy seat | `S(rho_bar(eta))` from orbit-averaged state | geometric Ax0 seat / latitude entropy | live geometry seat |
| C | runtime Ax0 control | `ga0_level` | executable engine control signal, not final Ax0 doctrine | live proxy |
| D | bipartite entropy family | `S(rho_AB)` | needed once bridge outputs a true cut-state | live family, not closed |
| E | mutual information | `I(A:B)` | companion / diagnostic correlation measure | live diagnostic |
| F | conditional entropy | `S(A|B)` | signed cut entropy | live candidate family |
| G | coherent information | `I_c(A>B) = -S(A|B)` | strongest simple signed Ax0 candidate | strongest working candidate |

Main files:
- [PROTO_RATCHET_ENTROPY_ALIGNMENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ENTROPY_ALIGNMENT.md)
- [AXIS_0_1_2_QIT_MATH.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS_0_1_2_QIT_MATH.md)
- [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py)

**Most Important Split**

| Thing | What It Is |
|---|---|
| `ga0_level`, negentropy, coarse-graining | runtime engine entropy/control math |
| `I(A:B)`, `S(A|B)`, `I_c` on `rho_AB` | real Ax0-facing cut-state entropy family |

So the current engine is already processing real entropy math, but:
- the **runtime engine** mostly processes entropy as a **proxy/control layer**
- the **final Ax0 math** still depends on the unresolved bridge `Xi : geometry/history -> rho_AB`

**Order In The Ratchet**
If we include the missing engine/entropy math, the current order is:

1. root constraints  
2. admissible finite math  
3. Weyl spinor carrier  
4. density matrices + Pauli/SU(2) base math  
5. `S^3` carrier  
6. Hopf / Bloch reduction  
7. nested Hopf-torus organization  
8. Weyl working layer  
9. QIT engine grammar and CPTP/unitary operator dynamics  
10. runtime entropy / negentropy / `ga0_level` processing  
11. bridge family `Xi : geometry/history -> rho_AB`  
12. Ax0 cut-state entropy kernel (`I_c`, `S(A|B)`, `I(A:B)`)

So the short answer is:
- **yes**, density matrices, Pauli math, operator channels, and entropy are base math in the live engine
- what is still open is not whether entropy math exists
- it is whether the runtime entropy/control layer and the final Ax0 cut-state layer are bridged correctly

If you want, I can make one final **master table** that merges:
- geometry
- engine math
- entropy math
- bridge math
all into one sheet.