# Lifted ladder spec prep - stage_lifted_spinor_shell_ladder_3q_to_8q

Status: read-lane spec only, not a build. This file adjudicates the stronger Hermes-named object: for `n=3..8`, the `n`-qubit spinor/network carrier placed on shell / nested-Hopf-torus support, then rerun through the stage rows. No sim, result JSON, queue mutation, promotion, or runner action is implied.

Ceiling for future packets: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not claim stage closure, canonical geometry, bridge/axis admission, physics, runtime closure, or full constraint-manifold completion.

## Owner-source answer: what "lift nQ on shells" means

The admissible lift is not a single density table with a decorative shell label. It is a spinor/tensor-network carrier placed over the nested Hopf torus cell support, with two coupled coordinate levels:

1. Per-site / per-node support: each local spinor site is placed at a Hopf-torus coordinate node carrying `eta`, loop phase, and derived `psi_L` / `psi_R`. The older TopoNetX bridge builds nested torus rings, stores node-local `q`, `psi_L`, and `psi_R`, adds within-ring and inter-ring edges, and adds rank-2 shell faces between adjacent torus levels (`system_v4/probes/toponetx_torus_bridge.py:38-97`). The geometry engine also says the real geometry state is Weyl spinors evolving on nested Hopf tori, with transport through a cell complex and density/entropy derived rather than primary (`system_v4/probes/engine_geometric.py:5-17`).
2. Collective shell support: a whole network slice has a shell/leaf coordinate for leakage, preservation, and terrain/operator rows. The shell coordinate is `z=cos(2 eta)`, and S6 defines leakage as `dz/dt` on `T_eta`, with leakage integrals as the restricted-mode flux layer (`system_v6/receipts/s6_build_spec_20260610.md:9-13`, `system_v6/receipts/s6_build_spec_20260610.md:60-80`).
3. Network support: the committed shell-indexed tensor-network support row proves a bounded chain where changing one shell tensor changes the network output and shell order is load-bearing (`system_v4/probes/sim_shell_indexed_tensor_network.py:8-17`, `system_v4/probes/sim_shell_indexed_tensor_network.py:53-79`). Its runner receipt records strict executable admission and a finite shell-indexed tensor-network ceiling (`system_v5/ops/lego_scaling/live_runner_shell_indexed_tensor_network_receipt_20260512T202830Z.json:21-26`).
4. Nested-shell topology: the connected Hopf-torus carrier packet builds two fixed-theta torus layers plus interlayer faces, compares TopoNetX and GUDHI topology readouts, and fences the result as a finite topology baseline rather than a full manifold (`system_v5/ops/lego_scaling/connected_hopf_torus_layer_carrier_packet_20260513T040900Z.json:5-17`, `system_v5/ops/lego_scaling/connected_hopf_torus_layer_carrier_packet_20260513T040900Z.json:37-56`).
5. Apple/testbed lineage: the current ring/checkerboard support packet explicitly points back to the apple pre-axes source slice and implements `n nested rings x n discrete steps per ring`, with inner/outer partitions, local nesting edges, parity, noncommuting order score, and density off-diagonal phase entering `phi0` (`system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl:42-48`, `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl:510-519`).

Adjudication: "lift to nQ on shells" means an `n`-site spinor network over explicit Hopf-torus support. Per-site coordinates carry local spinor/path data; edges/faces carry network and shell adjacency; the collective shell index is an observable/control coordinate used for leakage, preservation, and stage rows. A lone global shell index is too weak. A lone per-site Hopf coordinate with no collective shell leakage is also too weak.

## Existing machinery: lift directly vs new work

| Surface | Lifts directly | New for this spec |
|---|---|---|
| nQ carrier dimensions | Existing ladder packets give `(C^2)^n`, `C^(2^n)`, global-phase quotient `CP^(2^n-1)`, density real dimension `4^n-1`, Cl(2n), chirality split, and finite Pauli/string receipts for 3Q, 4Q, 5Q, and 6Q-8Q. The 3Q floor card defines the minimum carrier and exact `Cl(6)`/split rows (`system_v6/sims/geo_s1_three_qubit_floor_exact_v0/build_card.md:1-27`). The 6Q-8Q audit earns exact overbuild rows with dimensions 64/128/256 and density dims 4095/16383/65535 (`system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/audit_verdict.md:16-18`, `system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/audit_verdict.md:44-50`). | Attach those carriers to shell-network support per n; emit source-backed row IDs tying carrier basis sites to Hopf support nodes/faces. |
| Density quotient rows | Density-as-quotient doctrine is established: rho represents probe-indistinguishability on finite complex probe algebra, and rho erases lifted data (`system_v6/receipts/density_matrix_as_quotient_doctrine_20260610.md:5-12`). | Per-n shell-lifted density quotient: prove which shell/path/spinor data are erased by `rho`, which survive in reductions, and which are visible only on the lifted network. |
| 3Q reduced densities / entropy | 3Q exact reduced densities, entanglement entropies, tau, and Cl(6) floor survived hardening according to S8 adjudication (`system_v6/receipts/s8_s9_adjudication_20260610.md:11-22`). | S(A|B), I(A:B), and I_c remain missing as an S8-local table (`system_v6/receipts/s8_s9_adjudication_20260610.md:18`). Add those per bipartition and per shell-placement control. |
| S6 shell leakage machinery | S6 spec already defines `z_dot=e_z^T(A r_eta+b)`, preserve/move/cross/leave classes, leakage integrals, A/F/h/Phi action status, Matrix64 overlay, and loop-order gap on a shared carrier (`system_v6/receipts/s6_build_spec_20260610.md:60-126`). | Lift S6 from one-qubit/Bloch shell rows to nQ network rows: per-site leakage, aggregate shell leakage, entanglement-sensitive leakage, and controls for projection-induced false preservation. |
| Operators / terrain order gaps | S4/S5/Matrix64/S6 define operator, terrain, 64-cell, and loop-order reuse boundaries (`system_v6/receipts/s6_build_spec_20260610.md:24-54`, `system_v6/receipts/s6_build_spec_20260610.md:105-126`). | Define nQ operators as tensor/product/local-channel lifts with explicit support action. Reuse lower rows only as source rows, not as proof that the nQ network order gap is computed. |
| Shell topology / network support | TopoNetX/GUDHI connected layer carrier and shell-indexed tensor network establish finite topology and tensor-chain support rows (`system_v5/ops/lego_scaling/connected_hopf_torus_layer_carrier_packet_20260513T040900Z.json:37-56`, `system_v4/probes/sim_shell_indexed_tensor_network.py:65-79`). | Build nQ shell-network support objects with site, edge, face, and shell IDs, plus negative controls for no-face, duplicate-eta, and collapsed-shell false positives. |

## Bounded build sequence

First packet must be `n=3` on shells. Do not start at 8Q.

1. `geo_lifted_spinor_shell_ladder_3q_v0`: minimum floor on the geometry. Reuse the exact 3Q carrier facts, but create the first real lifted-shell object: three spinor sites on Hopf-torus support, explicit edge/face support, density quotient, lifted path rows, 3Q entropy rows including `S(A|B)`, `I(A:B)`, and `I_c`, operator/terrain order gaps, bracketing boundary, and shell leakage/preservation rows.
2. Audit `n=3` before scaling. The audit must attack shell-label theater, density-only collapse, per-site-only/no-aggregate leakage, and copied S6 rows.
3. Scale `n=4` and `n=5`: reuse 4Q/5Q carrier receipts as support, add shell placement and row table. Keep the minimum-floor statement at 3Q.
4. Scale `n=6`, `n=7`, `n=8`: use exact Pauli-label/stabilizer/sparse/tensor-network routes. No arbitrary dense-state or dense-operator enumeration.
5. Only after all n rows exist may a later packet compare trends across n. Trend comparison is not part of the first 3Q packet.

Suggested future packet IDs:

- `geo_lifted_spinor_shell_ladder_3q_v0`
- `geo_lifted_spinor_shell_ladder_4q_v0`
- `geo_lifted_spinor_shell_ladder_5q_v0`
- `geo_lifted_spinor_shell_ladder_678q_v0`
- optional final read-only audit: `lifted_spinor_shell_ladder_3q_to_8q_audit_v0`

## Per-stage-row concrete requirements

| Row | Concrete lifted meaning | Direct reuse | New receipt required | Load-bearing tooling |
|---|---|---|---|---|
| Density quotient | For each n, compute `psi -> rho=psi psi^dagger`, reduced densities on named cuts, and a quotient-erasure table over shell/path/support fields. | nQ carrier and rho quotient receipts; density doctrine. | Per-n proof that shell/path lift data are not silently present in rho; named reductions over shell-supported sites. | Julia/Symbolics or exact rational route for formulas; JAX/sympy for independent CAS; PyTorch exact tensor route for reductions; z3/cvc5 for finite quotient/control rows. |
| Lifted spinor/path | Place each site or tensor-network node at Hopf support coordinates and emit local `psi_L/psi_R`, edge path, face/shell membership, and collective shell coordinate. | TopoNetX bridge, connected Hopf torus carrier, shell-indexed network. | nQ site-edge-face table with support IDs and no-face/duplicate-eta/collapsed-shell controls. | TopoNetX load-bearing for cell support; GUDHI supportive/load-bearing for topology crosscheck; XGI/rustworkx supportive for hypergraph/dependency if used; Clifford load-bearing for spinor/chirality rows. |
| Operator/terrain order gaps | Lift local S4/S5 operators to named support sites or edges, then compare order on one shared nQ carrier. | S4/S5/Matrix64/S6 source rows. | Per-n `Delta_T,O`, `Delta_DI`, and shared-carrier controls; no label-only order gaps. | Julia/JAX exact Pauli or channel algebra; PyTorch tensor-native order action; z3/cvc5 for raw-object control gates where finite. |
| Entropy rows | For named cuts, compute `S(A)`, `S(B)`, `S(AB)`, `S(A|B)`, `I(A:B)`, and `I_c`; record shell placement and whether the row is density-only or lift-sensitive. | 3Q exact reduced density/entropy fixtures; 4Q/5Q/larger carrier rows. | The missing `S(A|B)`, `I(A:B)`, `I_c` table for 3Q first, then per n. | Sympy/Symbolics for exact named states; PyTorch/JAX for sparse/stabilizer tensor reductions at high n; quimb optional load-bearing for tensor-network contractions if introduced with controls. |
| Bracketing boundary | Preserve matrix associativity for nQ operators while testing whether site grouping/path lift changes labeled network action. | 3Q exact bracketing boundary and 6Q-8Q T01 rows. | Per-n row distinguishing matrix associator zero from network grouping/path-sensitive lifted rows. | Exact Pauli-label route; z3/cvc5 for corrupted controls; PyTorch exact integer mirror for high-n checks. |
| Shell leakage/preservation | Compute per-site and aggregate `z_dot`, finite-time shell class, leakage integrals, and purity/lift status on shell-supported nQ states. | S6 leakage spec and S5 exported `A,b` rows. | Per-n shell/network leakage table; distinguish density-shell preservation from pure Hopf preservation; negative controls for hardcoded leakage and wrong shell coordinate. | Julia/JAX for symbolic `z_dot` and exact integrals where possible; PyTorch for batched sparse/tensor leakage; TopoNetX/GUDHI for shell topology; z3/cvc5 for finite gates. |

## Resource bounds by n

| n | Exact carrier facts | Exact/computable shell-lift route | Not allowed as evidence |
|---:|---|---|---|
| 3 | Hilbert dim 8; density real dim 63; Cl(6); gamma split 4+4; max family 7; 3Q is the minimum floor. | Full named-state exact reductions, all required 3Q entropy rows, exact Pauli/operator rows, explicit shell support graph. | Calling existing 3Q floor "on shells" without support rows. |
| 4 | Hilbert dim 16; density real dim 255; Cl(8); gamma split 8+8; max family 9. | Exact Pauli-label/operator rows and bounded named-state shell reductions. | Arbitrary dense state sweeps treated as coverage. |
| 5 | Hilbert dim 32; density real dim 1023; Cl(10); gamma split 16+16; max family 11. | Sparse/named-state reductions; exact Pauli/stabilizer rows; bounded tensor-network shell support. | Moving the minimum floor from 3Q. |
| 6 | Hilbert dim 64; density real dim 4095; gamma count 12; split 32+32; max family 13 (`system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/audit_verdict.md:44-50`). | Exact Pauli-label scan, stabilizer/sparse reductions, shell graph/topology rows, bounded tensor-network contraction. | Full arbitrary dense-state enumeration or dense clique enumeration. |
| 7 | Hilbert dim 128; density real dim 16383; gamma count 14; split 64+64; max family 15. | Same as 6Q, with stronger sparse/tensor-network discipline. | Bare float resources as claim evidence. |
| 8 | Hilbert dim 256; density real dim 65535; gamma count 16; split 128+128; max family 17; next-family minimum dimension 512 (`system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/audit_verdict.md:46-50`). | Exactly computable: Pauli-label algebra over `4^8=65536` labels, constructive Clifford/stabilizer families, sparse named-state reductions, tensor-network contractions, and shell graph/topology rows. | Full dense arbitrary-state enumeration, full dense operator-family search, or all-state shell sampling. Resource/runtime floats are diagnostic nonclaims only. |

## Blind-derivable expectations

Keep these as audit expectations. Builders may only emit them as derived results, not as hand-entered verdicts.

1. `n=3` is the first admissible lifted-shell floor because it is the minimum three-slot/chirality carrier; scaling rows do not move that floor.
2. Density quotient rows will erase at least global phase and some lifted path/support distinctions; the shell-lift table must show what is erased rather than pretending rho carries all geometry.
3. Per-site Hopf placement should be visible in support/path rows before it is visible in reduced density rows.
4. A shell index with no node/edge/face support should fail the lift gate.
5. A support graph with no aggregate shell leakage should fail the S6-style shell gate.
6. Zero aggregate leakage can be symmetry cancellation, not pointwise shell preservation.
7. Pure Hopf preservation and projected density-shell preservation can diverge, especially for nonunitary rows.
8. `S(A|B)`, `I(A:B)`, and `I_c` should be exact for named 3Q controls and sparse/stabilizer-derived for larger n.
9. Operator order gaps and bracketing rows must be computed on one shared carrier; comparing spinor output to density output is a carrier-mismatch failure.
10. Matrix associativity remains zero for nQ matrix multiplication; any bracketing sensitivity must be explicitly a lifted site/path/grouping effect or an algebra-extension lane.
11. At 8Q, exact Pauli/stabilizer/tensor-network routes should survive; arbitrary dense enumeration should be fenced as infeasible and non-required.
12. Shell topology controls should reproduce known failures: no-face, duplicate-eta, disjoint-layer, and collapsed-shell controls must not pass as connected shell support.

## Build acceptance ledger

The future first packet (`n=3`) passes only if it emits all of these:

1. `P1_source_lineage`: cites 3Q carrier floor, density quotient doctrine, TopoNetX Hopf support, shell-indexed tensor network, connected Hopf-torus carrier, and S6 leakage rows.
2. `P2_support_object`: emits site, edge, face, shell, and network IDs; no single global shell label can satisfy this.
3. `P3_density_quotient`: computes rho and reductions, plus a quotient-erasure table over lifted shell/path data.
4. `P4_lifted_path`: emits local spinor/path rows on Hopf support with duplicate/collapsed/no-face controls.
5. `P5_entropy`: computes `S(A|B)`, `I(A:B)`, and `I_c` for required 3Q cuts and named controls.
6. `P6_order_gaps`: computes terrain/operator and loop-order gaps on one shared carrier.
7. `P7_bracketing_boundary`: separates matrix associativity from lifted network grouping/path effects.
8. `P8_shell_leakage`: computes per-site and aggregate leakage, finite-time class, and preservation/leaving status.
9. `P9_tooling`: every row has `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, source hashes, and explicit load-bearing vs supportive roles.
10. `P10_cross_engine_fatality`: Julia/JAX/PyTorch load-bearing rows agree, and disagreement fails.
11. `P11_negative_controls`: controls are executed mutations with observed failures, not declarative booleans.
12. `P12_ceiling`: scratch ceiling and no-promotion fields are present in every result.

## Negative controls

The future packets must include controls that can fail:

1. Global-shell-only lift: attach one shell label to the nQ state with no site/edge/face support; support gate fails.
2. Per-site-only lift: emit local Hopf coordinates but no aggregate shell leakage; shell gate fails.
3. Density-only collapse: claim shell/path preservation from rho alone; quotient-erasure gate fails.
4. Copied S6 leakage: paste one-qubit `z_dot` rows without nQ support/action; lineage/recompute gate fails.
5. Carrier mismatch: compute an order gap on spinors and compare to density output; shared-carrier gate fails.
6. Matrix associator overclaim: claim nonassociative matrix multiplication; bracketing boundary fails.
7. Shell topology theater: remove interlayer faces or duplicate eta while still claiming connected shell support; topology gate fails.
8. Wrong shell coordinate: use `z=eta` or `z=sin(2 eta)` in leakage rows; S6 inheritance gate fails.
9. 8Q dense-smuggling: use sampled dense states as if they cover the 8Q shell object; resource gate fails.
10. Tool decoration: list TopoNetX, GUDHI, Clifford, z3, cvc5, quimb, PyTorch, or JAX without a row where its API is load-bearing; tooling gate fails.

## Tooling answer by row

The owner's tooling challenge is load-bearing: each row must say which aligned package is doing real work.

- `TopoNetX`: load-bearing for cell complex support, node/edge/face incidence, shell adjacency, and connectedness.
- `GUDHI`: load-bearing or independent crosscheck for persistent/topology readouts on shell-layer fixtures.
- `CliffordAlgebras` / exact Clifford route: load-bearing for spinor/chirality/gamma rows where used.
- `Symbolics.jl` / `sympy`: load-bearing for exact density, entropy, quotient, and symbolic leakage formulas.
- `Z3` / `cvc5`: load-bearing only when asserting finite raw-object constraints or corrupted controls; not for label booleans.
- `PyTorch`: load-bearing for exact integer tensor mirrors, sparse reductions, batched operator/leakage rows, or tensor-network contractions; not for decorative float mirrors.
- `JAX`: load-bearing for vectorized exact/sparse scans, independent formula evaluation, and bounded batch checks.
- `quimb`: optional load-bearing for explicit tensor-network contraction at higher n if introduced with source hashes and controls.
- `rustworkx` / `XGI`: optional support/load-bearing for graph or hypergraph dependency rows if the packet uses non-cell-complex network structure.
- `geomstats` / `e3nn`: not default. Use only if a row specifically requires metric/equivariant geometry and includes a can-fail control.

## Final adjudication

The next admissible action is not a broad 3Q-8Q build. It is the first packet, `n=3` lifted onto shells, with the exact carrier floor placed on explicit nested-Hopf-torus support and with all row families recomputed on that support. Only after that packet and audit survive should 4Q-8Q be scaled under the overbuild discipline.
