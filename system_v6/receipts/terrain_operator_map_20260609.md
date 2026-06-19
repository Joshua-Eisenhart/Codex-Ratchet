# Terrain / Operator Map v0

Scope: terrain/operator planning receipt for `/Users/joshuaeisenhart/Codex-Ratchet`.
Status ceiling: source-grounded map plus live v4/v5 inventory. Existing rows are `tool_lego_fit_probe`, `scratch_diagnostic`, capability receipt, classical baseline, or legacy/reference unless the row says otherwise. No row is admitted as final `M(C)`, QIT engine, bridge, Axis0 closure, physics, PEPS3D closure, or canonical manifold.

Binding doctrine: root identity is probe-relative: `a=a iff a~b`. The three levels here are:

| level | expression | decisive equality question |
|---|---|---|
| elements | density quotient | Are two element/state representatives indistinguishable under the active probe quotient? |
| order | noncommutation | Are ordered histories indistinguishable: `Phi_T(O(rho)) ~ O(Phi_T(rho))`? |
| grouping | nonassociativity | Are grouped histories indistinguishable: `(ab)c ~ a(bc)`? |

Hard fence: `WIN/LOSE/win/lose` is currently a strategy/readout grammar. It is not an executable payoff, utility, selection, reward, or optimization criterion until a named functional is attached and tested. Every terrain row below keeps that fence explicit.

Sources read: `~/wiki/concepts/apple-axes-terrain-operator-math.md`; `~/wiki/concepts/terrain-laws-and-loop-geometry.md`; `~/wiki/concepts/engine-math-reference.md`; `~/wiki/concepts/igt-pattern-explicit-math-reference.md`; `~/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md`; `~/wiki/concepts/axes-0-6-and-constraint-manifold-explicit-atlas.md`; advisory `~/wiki/concepts/i-ching-axes-rosetta.md`; repo reference docs `system_v5/READ ONLY Reference Docs/operator math explicit.md`, `terrain math.md`, `terrain rosetta strong math.md`; live inventory under `system_v5/` and `system_v4/`.

Engine shorthand: algebra/dynamics capability gaps should not be re-flagged generically. Capability receipts exist as of 2026-06-09 under `system_v4/probes/a2_state/sim_results/`: `julia_carrier_algebra_capability_results.json`, `jax_algebra_capability_results.json`, `torch_ga_capability_results.json`, `kingdon_capability_results.json`, `julia_dynamics_capability_results.json`, `jax_dynamics_capability_results.json`, `pytorch_capability_results.json`, and `qutip_capability_results.json` all report `all_pass=true`. This is capability readiness only, not promotion of terrain/operator rows.

## Existing Terrain / Operator Inventory

| family | source/result files found | current result status |
|---|---|---|
| 4 base operators | `system_v5/READ ONLY Reference Docs/operator math explicit.md`; `system_v4/probes/sim_engine_4_operators.py`; `system_v5/julia_carrier/ax6op_julia_results.json` | exact source formulas exist; v4 sim is a classical-baseline implementation; v5 `ax6op` is bounded finite-map receipt, `promotion_allowed=false` |
| 8 terrain generator laws / 16 placements | `system_v5/READ ONLY Reference Docs/terrain math.md`; `terrain rosetta strong math.md`; `system_v4/probes/sim_engine_8_terrains.py`; `system_v5/julia_carrier/wb_axis3_terrains_julia_results.json` | formulas exist; v5 terrain probe is `tool_lego_fit_probe`, `promotion_allowed=false`; `all_pass=false` because the requested pure-zero control honestly fails for Ni/Si fixed points |
| Axis-6 precedence/order gap | `system_v5/julia_carrier/disc_axis6_order_gap_julia_results.json`; `system_v5/ops/formal_scouts/results/disc_axis6_order_gap_results.json`; `system_v5/julia_carrier/ax6_julia_results.json`; `system_v5/julia_carrier/ax6op_julia_results.json` | strongest receipt is `scratch_diagnostic`: 3/8 sparse order gaps nonzero, commuting controls collapse, all-16-cells-live demoted to `PARTIAL`, `promotion_allowed=false` |
| Axis-4 loop/order class | `system_v5/julia_carrier/ax4_julia_results.json`; `system_v4/probes/sim_axis4_deductive_inductive.py`; `system_v4/probes/ax4_loop_ordering_evidence.py` | bounded finite-map receipt; trajectory/order split evidence only, not layer-complete |
| 64 addressing / engine grammar | `system_v5/julia_carrier/eng_64_hexagram_julia_results.json`; `eng_yinyang_julia_results.json`; `system_v4/probes/test_engine_dual_loop_grammar.py`; `system_v4/docs/generate_64_runtime_engine_table.py` | `eng_64` passes finite-map checks with 64 stages but only `n_distinct=16`; this is honest degeneracy, not 64 dynamically distinct stages |
| Carnot/Szilard finite engine probes | `system_v5/julia_carrier/carnot_szilard_qit_engine_julia_results.json`; `eng_carnot_axiswired_julia_results.json`; `eng_szilard_axiswired_julia_results.json` | all are finite-map/candidate probes with `promotion_allowed=false`; useful engine-readiness evidence, not final QIT engine |
| low-level N01/order quotient | `system_v5/ops/formal_scouts/results/three_engine_foundation_r1_n01_noncommutation_order_quotient_results.json`; `foundation_r1_n01_noncommutation_order_quotient_{julia,jax,pytorch}_results.json`; `r2_admissible_operations_commutation_order_results.json` | scratch diagnostics for order/noncommutation and operation commutation; no downstream claim |

## A. The 8 Operators

Conventions:

- State: `rho = [[a, u-iv], [u+iv, d]]`, `a,d,u,v in R`, `a,d>=0`, `a+d=1`, `u^2+v^2<=ad`.
- Bloch form: `rho = 1/2(I + x sigma_x + y sigma_y + z sigma_z)`, so `x=2u`, `y=2v`, `z=a-d`.
- Base terrain/channel placeholder: `Phi_T` is the chosen terrain channel or finite-time terrain flow.
- Polarity: `+` means operator-first execution, `Phi_T(O(rho))`; `-` means terrain-first execution, `O(Phi_T(rho))`. Polarity is an order-level object, not extra operator math.

| operator | exact base map on `rho` | +/- operational meaning | decisive bounded test | exists-in-v5? | engine readiness | gap |
|---|---|---|---|---|---|---|
| `Ti+` | Base `Ti = D_z`: `(1-q1)rho + q1(P0 rho P0 + P1 rho P1)` with `P0=1/2(I+sigma_z)`, `P1=1/2(I-sigma_z)`. Matrix result: `[[a,(1-q1)(u-iv)],[(1-q1)(u+iv),d]]`. Generator `L_Ti(rho)=(kappa1/2)(sigma_z rho sigma_z-rho)`. Bloch map `(lambda1 x, lambda1 y, z)`. | `Phi_T(Ti(rho))`: z-dephase first, then terrain. | Pinned `rho`, chosen `Phi_T`: compute `Delta_Ti,T = Phi_T(Ti(rho))-Ti(Phi_T(rho))`; positive only if nonzero against commuting controls. | Partial. Operator formula exists; `ax6op_julia_results.json`; `disc_axis6_order_gap_julia_results.json` includes `TiSe`, `TiNe`, both collapse to numerical zero in that sparse receipt. | READY at capability level: Julia/JAX/PyTorch/GA and solver receipts exist. | Need full signed-operator matrix receipt; current sparse Axis-6 result does not make Ti live. |
| `Ti-` | Same base `Ti = D_z`. | `Ti(Phi_T(rho))`: terrain first, then z-dephase. | Same order-gap pair as `Ti+`, but store both ordered outputs and exact norm. | Partial, same artifacts. | READY. | Need one receipt that records both `+` and `-` outputs for all terrains and controls. |
| `Te+` | Base `Te = D_x`: `(1-q2)rho + q2(Q+ rho Q+ + Q- rho Q-)`, `Q+=1/2(I+sigma_x)`, `Q-=1/2(I-sigma_x)`. Matrix result: `[[(1-q2)a+q2/2, u-i(1-q2)v], [u+i(1-q2)v, (1-q2)d+q2/2]]`. Generator `L_Te(rho)=(kappa2/2)(sigma_x rho sigma_x-rho)`. Bloch map `(x, lambda2 y, lambda2 z)`. | `Phi_T(Te(rho))`: x-dephase first, then terrain. | `Delta_Te,T = Phi_T(Te(rho))-Te(Phi_T(rho))`; commuting control should be zero. | Partial. Formula exists; sparse Axis-6 has `TeNi`, `TeSi`, both collapse to numerical zero. | READY. | Need full matrix; sparse receipt does not make Te live. |
| `Te-` | Same base `Te = D_x`. | `Te(Phi_T(rho))`: terrain first, then x-dephase. | Same order-gap pair, with trace/Frobenius norm and Choi/control row. | Partial. | READY. | Need polarity-composition closure test. |
| `Fi+` | Base `Fi = R_x`: `rho -> U_x(theta) rho U_x(theta)^dagger`, `U_x(theta)=exp(-i theta sigma_x/2)=[[cos(theta/2),-i sin(theta/2)],[-i sin(theta/2),cos(theta/2)]]`. Generator `L_Fi(rho)=-i[(omega3/2)sigma_x,rho]`. Bloch map `R_x(theta)r`. | `Phi_T(Fi(rho))`: x-rotation first, then terrain. | `Delta_Fi,T = Phi_T(Fi(rho))-Fi(Phi_T(rho))`; unitary purity control plus commuting same-axis control. | Partial. Formula exists; sparse Axis-6 has `FiNe` live with max gap `0.03923482275359014`, `FiSe` collapsed. | READY. | Need full terrain sweep; current evidence is one live Fi row. |
| `Fi-` | Same base `Fi = R_x`. | `Fi(Phi_T(rho))`: terrain first, then x-rotation. | Same order-gap pair; record whether polarity changes observable, entropy, and trace distance. | Partial. | READY. | Need signed-output receipt, not only max gap row. |
| `Fe+` | Base `Fe = R_z`: `rho -> U_z(phi) rho U_z(phi)^dagger`, `U_z(phi)=exp(-i phi sigma_z/2)=diag(exp(-i phi/2), exp(i phi/2))`. Generator `L_Fe(rho)=-i[(omega4/2)sigma_z,rho]`. Bloch map `R_z(phi)r`. | `Phi_T(Fe(rho))`: z-rotation first, then terrain. | `Delta_Fe,T = Phi_T(Fe(rho))-Fe(Phi_T(rho))`; unitary purity control plus same-axis commuting control. | Partial. Sparse Axis-6 has `FeNi` max gap `0.037818755966536215`, `FeSi` max gap `0.04072789104088517`. | READY. | Need all-terrain `Fe` sweep and SMT/solver confirmation. |
| `Fe-` | Same base `Fe = R_z`. | `Fe(Phi_T(rho))`: terrain first, then z-rotation. | Same order-gap pair; require zero under erased-axis/layer controls. | Partial. | READY. | Need full polarity composition matrix and closure classifier. |

## B. Operator Algebra

The 8 signed operators are not 8 independent base maps. They are 4 base Bloch maps crossed with 2 Axis-6 precedence polarities after choosing a terrain/channel context.

| base pair | commutator status as Bloch maps | reason / control |
|---|---|---|
| `Ti, Te` | zero for unital dephasing matrices | `diag(lambda_z,lambda_z,1)` and `diag(1,lambda_x,lambda_x)` commute. |
| `Ti, Fi` | generally nonzero | z-dephasing does not commute with x-rotation unless dephasing is identity or the probe is degenerate. |
| `Ti, Fe` | zero / commuting control | z-dephasing commutes with z-rotation. |
| `Te, Fi` | zero / commuting control | x-dephasing commutes with x-rotation. |
| `Te, Fe` | generally nonzero | x-dephasing does not commute with z-rotation except degenerate controls. |
| `Fi, Fe` | generally nonzero | rotations about x and z do not commute; BCH/commutator tests should detect this. |

| algebra question | current read | decisive bounded test | exists-in-v5? | gap |
|---|---|---|---|---|
| What do the 4 base maps generate? | A semigroup/group hybrid on one-qubit CPTP maps: `Ti/Te` are dissipative CPTP dephasings/semigroup elements; `Fi/Fe` are unitary rotations/group elements. The generated object is a subsemigroup of qubit CPTP channels containing a unitary subgroup and non-invertible dissipative contractions. | Generate words up to bounded length over `{Ti,Te,Fi,Fe}` on a pinned and a generic set of `rho`; classify distinct superoperators, invertible/unitary/CPTP, entropy/purity behavior, and commutation classes. | Partial: `ax6op_julia_results.json`, `foundation_qit_operator_composition_mcp_*_results.json`, `r2_admissible_operations_commutation_order_results.json`. | Need one consolidated operator semigroup receipt with exact word-depth and canonical collapse rules. |
| Do dissipative maps invert? | Physically no as CPTP inverse in the dephasing/contraction regime; as linear maps they are invertible only away from complete dephasing and the inverse is generally not CPTP. | Choi/CP test on candidate inverse; expect inverse fails CP except trivial/unitary cases. | Partial through operator/Kraus completeness receipts, not inverse-classifier. | Need explicit inverse CP-failure receipt. |
| Does `+/-` close under composition? | Not as an 8-element algebra by itself. `+/-` is a precedence relation between an operator and a selected terrain channel. Composing signed tokens produces words over operator and terrain maps; it does not remain in `{Ti±,Te±,Fi±,Fe±}` unless a quotient/collapse rule is added. | Compose all signed pairs under fixed terrain `Phi_T`; ask whether each composite equals one of the 8 signed maps under probe quotient. Include nondegenerate and commuting controls. | NO as one receipt. | Need polarity-composition closure test before any finite signed group claim. |
| Is there a known finite structure, e.g. signed/hyperoctahedral? | Candidate only. The count `4 x +/- = 8` resembles signed choices, but the maps are CPTP/unitary channels with continuous parameters and semigroup behavior, not a finite group unless parameters/quotients are fixed. | Fix discrete parameters, compute multiplication table modulo probe equivalence; check associativity, inverses, closure, identity. If continuous parameters are live, finite-group claim is killed. | NO. | Needs a finite quotient definition first. |
| Full 8x8 order-gap matrix | Not yet. Current Axis-6 discriminator is sparse over eight op-terrain couplings, not full signed-operator x signed-operator composition. | On pinned `rho`, compute `||A_i^+(A_j^-(rho))-A_j^-(A_i^+(rho))||` or the agreed signed-word equivalent for all 64 cells; classify zero/nonzero; add commuting controls and SMT/cvc5 on noncommuting pairs. | NO as one receipt. Existing `disc_axis6_order_gap` is closest but reports 3/8 sparse live rows. | Highest operator-algebra gap: one full 8x8 receipt. |

## C. The 8 Terrains

Terrain source distinction:

- 4 terrain families/topologies: `Se`, `Ne`, `Ni`, `Si`.
- 8 terrain laws: family crossed with sheet/type: `(Se,L)`, `(Se,R)`, `(Ne,L)`, `(Ne,R)`, `(Ni,L)`, `(Ni,R)`, `(Si,L)`, `(Si,R)`.
- 16 placements: each terrain law crossed with loop path `inner/fiber` or `outer/base`.

Loop/source formulas:

- Spinor carrier: `psi_s(phi,chi;eta)=(e^{i(phi+chi)} cos eta, e^{i(phi-chi)} sin eta)^T`, `s in {L,R}`.
- Density: `rho_s=psi_s psi_s^dagger = [[cos^2 eta, e^{2i chi} cos eta sin eta], [e^{-2i chi} cos eta sin eta, sin^2 eta]]`.
- Hopf connection: `A=dphi+cos(2eta)dchi`.
- Inner/fiber loop: `gamma_in^s(u)=psi_s(phi0+u,chi0;eta0)`, density-stationary.
- Outer/base loop: `gamma_out^s(u)=psi_s(phi0-cos(2eta0)u,chi0+u;eta0)`, density-traversing.
- Sheet Hamiltonians: `H_L=+H0`, `H_R=-H0`.
- Terrain channel: `Phi_tau^s(t)=exp(t X_tau^s)`.

| terrain | topology / exact generator on `rho` | variant meaning | readout grammar fence | decisive bounded test | exists-in-v5? | engine readiness | gap |
|---|---|---|---|---|---|---|
| `Se-in` / Funnel | Open dissipative outward/direct family. `X_{Se,L}(rho)=lambda_{Se,L} sum_{j=x,y,z} D[sigma_j](rho)-i eps_{Se,L}[H_L,rho]`; apple source also gives `dot rho=sum_k D[L_k^{Se,in}](rho)-i eps[H0,rho]`. | Type 1 / left sheet / flux IN; `H_L=+H0`. Loop placement is separate (`inner` or `outer`). | `Se=LoseWin` is chart/readout grammar only; no payoff/selection criterion. | Verify CPTP finite channel, Choi PSD, trace preservation, distinct superoperator from Ne/Ni/Si; then test inner density stationary vs outer density traversing under same `X`. | Partial: `wb_axis3_terrains_julia_results.json`; `terrain math.md`; v4 `sim_engine_8_terrains.py` classical baseline. | READY. | Need source-exact `X_{Se,L}` finite-time receipt tied to loop placement and readout token, not generic `sigma_x` proxy only. |
| `Se-out` / Cannon | `X_{Se,R}(rho)=lambda_{Se,R} sum_j D[sigma_j](rho)-i eps_{Se,R}[H_R,rho]`; apple source writes plus-sign Hamiltonian form because `H_R=-H0` flips sign in the sheet convention. | Type 2 / right sheet / flux OUT; `H_R=-H0`. | `Se=LoseWin` readout only; Type2 label row `loseWIN` does not define reward. | Same as `Se-in`, plus L/R handedness discriminator under `H_L` vs `H_R`. | Partial. | READY. | Need paired L/R Se receipt with same seed and handedness controls. |
| `Ne-in` / Vortex | Hamiltonian tangential circulation/direct. `X_{Ne,L}(rho)=-i[H_L,rho]` or with weak dissipator `-i[H0,rho]+eps sum_k D[L_k](rho)` in apple source. | Type 1 / left / flux IN. | `Ne=WinLose` readout only; no win-max functional. | Verify unitary/Hamiltonian circulation or declared weak dissipator; test purity preservation when pure Hamiltonian; order/axis distinctness against Se/Ni/Si. | Partial: terrain finite-map probe has distinct channel distances; source docs preserve weak-dissipator ambiguity. | READY. | Need settle pure Hamiltonian vs weak-dissipator source variant for the executable row. |
| `Ne-out` / Spiral | `X_{Ne,R}(rho)=-i[H_R,rho]` or source `+i[H0,rho]+eps sum_k D[...]` under sign convention. | Type 2 / right / flux OUT. | `Ne=WinLose` readout only. | Same as `Ne-in`, plus sign/handedness control. | Partial. | READY. | Need source-locked sign convention receipt. |
| `Ni-in` / Pit | Dissipative contraction/attractor conjugated/open. `X_{Ni,L}(rho)=gamma_{Ni,L}D[sigma_-](rho)-i eps_{Ni,L}[H_L,rho]`; apple source `D[L^{Ni,in}](rho)-i eps[H0,rho]`. | Type 1 / left / flux IN; lowering/attractor side. | `Ni=LoseLose` readout only; no loss-minimization criterion. | Amplitude-damping CPTP/Choi test; fixed-point control must be chosen carefully because `|0><0|` can be fixed. Use sensitive-state control, not pure-zero universal pass. | Partial: `wb_axis3_terrains_julia_results.json` explicitly reports pure-zero control failure for Ni fixed point but sensitive-state control passes. | READY. | Need exact `sigma_-` convention alignment: wiki `terrain math.md` and v4 implementation disagree in comments/conventions; normalize before stronger sim. |
| `Ni-out` / Source | `X_{Ni,R}(rho)=gamma_{Ni,R}D[sigma_+](rho)-i eps_{Ni,R}[H_R,rho]`. | Type 2 / right / flux OUT; raising/source side. | `Ni=LoseLose` readout only. | Same as `Ni-in`, with `sigma_+` and sheet sign control. | Partial. | READY. | Need paired lowering/raising sign-convention receipt. |
| `Si-in` / Hill | Stratified/retention family: commuting Hamiltonian plus invariant projectors. `X_{Si,L}(rho)=-i[omega_L m_L.sigma,rho]+kappa_L(P_+^L rho P_+^L+P_-^L rho P_-^L-rho)`; apple source uses `-i[H_C^in,rho]+sum_j kappa_j(P_j rho P_j-1/2(P_j rho+rho P_j))`, `[H_C,P_j]=0`. | Type 1 / left / flux IN; invariant strata. | `Si=WinWin` readout only; no utility/payoff promotion. | Verify projectors complete/orthogonal, `[H_C,P_j]=0`, CPTP, fixed-strata behavior; choose non-fixed sensitive states for positive controls. | Partial; terrain probe notes pure-zero control also fixed for Si z-dephasing. | READY. | Need exact projector frame receipt and non-fixed controls. |
| `Si-out` / Citadel | Right-sheet version: `X_{Si,R}(rho)=-i[omega_R m_R.sigma,rho]+kappa_R(P_+^R rho P_+^R+P_-^R rho P_-^R-rho)` with right projector frame and `H_R`. | Type 2 / right / flux OUT. | `Si=WinWin` readout only. | Same as `Si-in`, plus right projector-frame sign/rotation control. | Partial. | READY. | Need right/left projector-frame normalization. |

## D. Terrain x Operator Composition

Axis-6 is the owner's order axis at the terrain/operator layer. It is not pair-readout order and not the four-step loop order.

| composition surface | exact math | decisive test | exists? | gap |
|---|---|---|---|---|
| Axis-6 precedence | `Delta_{T,O}(rho)=Phi_T(O(rho))-O(Phi_T(rho))`. Source also gives left/right primitive action `L_A(rho)=A rho`, `R_A(rho)=rho A`, and Liouville separation `I tensor A` vs `A^T tensor I`. | For each terrain/operator pair, compute nonzero precedence gap on pinned nondegenerate `rho`; require commuting/erased-axis controls collapse. For stronger claim, add SMT/solver UNSAT for swapped-precedence equivalence under noncommuting constants. | YES partial. `disc_axis6_order_gap_julia_results.json` is a `scratch_diagnostic`: `FiNe`, `FeNi`, `FeSi` live; commuting rows collapse; erased layer live count 0; all-16-cells-live is `PARTIAL`. | Need all `8 terrains x 8 signed operators = 64` precedence matrix as one result, with pinned-rho and generic-state variants. |
| Terrain-specific precedence table | Source token table gives examples: `TiSe=Se-in(Ti(rho))`, `SeTi=Ti(Se-out(rho))`, `NeTi=Ti(Ne-in(rho))`, `TiNe=Ne-out(Ti(rho))`, etc. | Parse all source token rows and verify every ordered token maps to the source composition exactly; then test whether the two orders differ on `rho`. | YES for static source extraction; runtime partial via `eng_64` and `ax6`. | Need source-locked token parser plus dynamic precedence measurement. |
| Commuting control | Same-axis/erased-layer controls should give `||Delta||~0`. | Replace terrain axis by paired operator axis; confirm live count goes to 0. | YES in `disc_axis6_order_gap`: max axis-matched control gap about `2.26e-16`. | Need same control in full 64 matrix. |
| Sparse live result | Current live rows are not all cells. | Accept only rows with measured nonzero gap; classify collapsed rows honestly. | YES: 3/8 live in sparse discriminator. | Do not claim all 16/64 live until full matrix proves it. |

## E. Seat On The Nested Geometry

| object | what is defined in owner sources | what remains undefined / needs foundation |
|---|---|---|
| carrier | `H=C^2`, density space `D(C^2)`, spinor carrier `S^3`, Hopf projection to `S^2`, Hopf tori `T_eta`, left/right Weyl sheets. | How this one-qubit carrier lifts to every proposed nested torus/rung without erasing phase/path data. |
| density quotient | `rho=psi psi^dagger`; fiber phase `phi` is density-blind, while base loop changes off-diagonal phase through `chi`. | Whether density-only probes are sufficient for 720-degree/spinor-order claims. Sources warn density can erase lifted phase/path information. |
| operators | `Ti/Te/Fi/Fe` act on `rho` as CPTP dephasings and unitaries. | Whether the same operators act per torus rung, on channel space, or on a larger foliation object is not fully defined in the named sources. |
| terrains | Terrain is the generator `X_{tau,s}`; loop is `Y_in` or `Y_out`; placement is `(X_{tau,s},Y_l)`. | The binding from terrain generator to nested foliation class beyond the local qubit/Hopf packet is not yet an admitted sim object. |
| loops | `inner/fiber` is density-stationary; `outer/base` is density-traversing. Four loop placements are left-fiber, left-base, right-fiber, right-base. | Whether Type1/Type2, flux IN/OUT, and engine-family labels are fully reducible to loop geometry is still a discriminator target, not closed doctrine. |
| engine grammar | Type1 outer deductive / inner inductive; Type2 outer inductive / inner deductive; `eng_64` enumerates 64 stages. | `eng_64` has only 16 distinct fingerprints in the current receipt. Runtime visitation/full distinctness is not established. |

## F. Structural Questions Worth Tests

These are candidate questions, not doctrine.

| candidate question | why it matters | decisive bounded test | current status |
|---|---|---|---|
| Does `{Ti,Te,Fi,Fe} x {+,-}` generate a known finite structure? | Prevents false finite-group claims from a count match. | Fix discrete parameters and probe quotient; compute multiplication table, identity, inverses, closure, associativity. If continuous parameters remain live or dissipative inverses fail CP, finite group claim is killed. | Open. |
| Is terrain `4 x +/-` isomorphic to operator `4 x +/-` as order structures? | The count `8` can mislead; terrains are generator/sheet laws, operators are channel maps plus precedence. | Build two signed order graphs; compare adjacency/commutator matrices and quotient invariants. Require mismatch reporting, not label matching. | Open. |
| Does the order-gap matrix reproduce nested-ratchet order gaps when operators are rung maps? | Tests whether local Axis-6 is the same order mechanism as higher nested geometry. | Replace `O` with candidate rung maps; compute `Delta` across adjacent rungs; compare zero/nonzero pattern to base operator matrix and controls. | Open; foundations needed for rung maps. |
| Is Axis-4 loop order independent from Axis-6 precedence? | Source explicitly separates four-step loop order from operator/terrain precedence. | Orthogonality/discriminator: vary Axis-4 with fixed Axis-6 and vary Axis-6 with fixed Axis-4; both should have independent observables if distinct. | Partial via `ax4_julia_results.json`, `ax6_julia_results.json`, `eng_64_hexagram_julia_results.json`; no one consolidated independence receipt. |
| Does win/lose grammar ever become executable? | The owner fence says not yet. | Attach a named functional, e.g. trace-distance, entropy, coherent information, work proxy; prove labels predict a measured sign under controls. | Open; do not presume. |

## Highest-Leverage Sims In Dependency Order

1. `source_locked_operator_base_packet`: exact `Ti/Te/Fi/Fe` maps, Kraus/unitary/generator forms, Bloch maps, Choi/TP/purity/entropy checks, and corrected naming. Depends on `operator math explicit.md`.
2. `terrain_generator_sheet_packet`: exact 8 `X_{tau,s}` generators, projector/jump conventions, L/R Hamiltonian sign, CP/TP/Choi checks, sensitive-state controls. Depends on `terrain math.md` convention lock.
3. `terrain_operator_precedence_64_matrix`: full `8 terrains x 8 signed operators` order-gap matrix on pinned and generic `rho`; commuting and erased-axis controls; SMT/cvc5 for noncommuting pairs. Depends on 1-2.
4. `polarity_closure_semigroup_probe`: word-depth bounded closure table for `{Ti,Te,Fi,Fe}` and signed precedence words under fixed terrain contexts; CP inverse test for dissipative maps. Depends on 1 and 3.
5. `nested_geometry_binding_probe`: test how operator/terrain maps ride Hopf torus rungs and whether density-only readout erases spinor/path order. Depends on source-locked loop and terrain packets.

## Foundations Needed Before Sims

| foundation | why needed |
|---|---|
| `sigma_+ / sigma_-` convention lock | Wiki `terrain math.md` and v4 implementation comments use opposite-looking matrix conventions. Need one owner-approved convention before Ni/Pit and Ni/Source receipts. |
| pure Hamiltonian vs weak dissipator for `Ne` | Sources contain both pure `-i[H,rho]` and weak-dissipator variants. The executable terrain row must choose or preserve both as live alternatives. |
| projector frame for `Si` | Need exact `m_L`, `m_R`, `P_j`, and commuting Hamiltonian frame before source-exact Hill/Citadel sims. |
| terrain/channel finite-time policy | Source gives generators `X`; sims need `Phi=e^{tX}` or bounded Euler/RK convention with fixed `t`. |
| loop-placement binding | Terrain law `X` and loop path `Y` are separate. Need explicit policy for when a sim tests terrain law alone vs placement `(X,Y)`. |
| nested torus/rung lift | Operators currently act on local `rho`; the map does not yet define per-rung action across the larger nested geometry. |
| executable win/lose functional | Required before any payoff/selection claim. Until then win/lose remains readout grammar only. |

## Engine Gaps

| gap | current state | next action |
|---|---|---|
| Algebra/dynamics engine capability | Capability receipts exist; `julia_carrier_algebra`, `jax_algebra`, `torch_ga`, `kingdon`, `julia_dynamics`, `jax_dynamics`, `pytorch`, and `qutip` under `system_v4/probes/a2_state/sim_results/` report `all_pass=true`. | Reuse these receipts; do not re-flag generic engine readiness. |
| Operator naming drift | Owner math says `Ti/Te` are dephasing and `Fi/Fe` are rotations. Some probe internals use drifted `gradient/spectral` labels. | New operator packet should source-lock labels and treat old drift as legacy/diagnostic only. |
| Terrain generator exactness | Existing terrain probe is useful but not a full source-exact 8-generator receipt; it also honestly fails a pure-zero control. | Build exact generator receipt with sensitive controls and convention lock. |
| Axis-6 full matrix | Existing `disc_axis6_order_gap` is strong but sparse: 3/8 live rows, all-16-live `PARTIAL`. | Build the full 64 signed terrain/operator matrix as one receipt. |
| Runtime distinctness | `eng_64` enumerates 64 stages but `n_distinct=16` fingerprints. | Separate address enumeration from dynamic distinctness; run stronger schedule visitation/distinctness tests only after operator/terrain packets are source-locked. |
| Nested geometry binding | Source defines Hopf/S3 one-qubit local carrier and placements; not the full per-rung operator/terrain action. | Build rung-map foundations before nested-ratchet reproduction claims. |
| Win/lose promotion | Explicitly fenced as readout grammar, not payoff. | Only promote with named functional and controls. |

## Addendum 2 (owner correction, 2026-06-09): THREE distinct +/- — never collapse

There are THREE different +/- polarities, deliberately given different vocabulary so they do not collapse (owner): 
- Axis 0 +/-: correlation-RESPONSE polarity under perturbation — allostatic (diversity spreads) vs homeostatic (damped); actual DOF = signed response functional on rho_AB (AXIS0_SPEC_OPTIONS: testable options, bridge-level open).
- Axis 3 +/-: loop PLACEMENT — Hopf fiber loop gamma_in (density-stationary) vs lifted base loop gamma_out (density-traversing); actual DOF = which torus loop carries transport (source: core_docs Axis 3 math).
- Axis 6 +/-: composition ORDER — Phi_T(O(rho)) vs O(Phi_T(rho)); actual DOF = measured order gap.
Terrain8 = Topology4 x Flux2 (atlas) uses the Axis-3-adjacent flux orientation; the operator +/- in section A is Axis-6 precedence. Section B/F rows that blur these are corrected by this addendum.
DERIVED TEST FAMILY (owner: "the 0-6 axes are nearly defined by their distinction from each other; the dofs have to dig into the actual dofs"): pairwise independence discriminators 0-vs-3, 0-vs-6, 3-vs-6 — vary one polarity with others pinned; each must move ONLY its own observable; every polarity implemented as its actual DOF (measured response sign / actual loop transport / actual composition gap), never a label flag.
