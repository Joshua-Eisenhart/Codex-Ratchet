# Weld 2 Nonassociative Carrier Integration Mine - 2026-06-10

Status: read-lane mine only. No build, no sim, no queue mutation.

Ceiling: this receipt can specify a bounded future weld packet, but it does not promote any source packet above its own `scratch_diagnostic` / `formal_scout` ceiling and does not resolve the carrier choice points.

Binding absence rule: `system_v6/README.md:43-49` requires grep-quoted absence/novelty checks and a distinction between "math not on file" and "sim/receipt not yet built." The mine below treats the math as partly on file and the M(C,t) nonassociative weld packet as not yet built.

## A tower-on-disk inventory

### A1. `assoc_weakening_lattice_classifier`

What it computes:

- The audit says the packet is "genuine as a scratch diagnostic / finite structure-constant classifier harness" and explicitly not admitted/canonical; the files set `classification: scratch_diagnostic`, `promotion_allowed: false`, and `formal_admission_allowed: false` (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:17-19`).
- Octonion associativity failure is computed at the finite basis triple `(e1,e2,e4)`: `(e1 e2)e4 = e7`, `e1(e2 e4) = -e7`, residual `2 e7` (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:23-28`).
- Sedenion alternativity failure is computed for a concrete vector witness with residual support `26 e10 - 10 e11 + 2 e12 - 22 e13 + 18 e14` and max residual `26` (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:30-35`).
- The Artin seat is computed, not assumed: `find_artin_basis_pairs` checks generated subalgebras for every basis pair (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:37-38`).
- SMT cells derive the decisive facts: O associativity violation SAT, H associativity control UNSAT, S alternativity violation SAT, H alternativity control UNSAT (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:54-59`).
- The envelope pins the bracket convention as "explicit left/right parenthesized products over C[k,i,j]" and the proof tag as generated Cayley-Dickson structure constants plus Julia Z3 associator control (`system_v6/sims/assoc_weakening_lattice_classifier/results/assoc_weakening_lattice_classifier_envelope_results.json:24-35`).
- Classification matrix: `O` has `associativity: false`, `alternativity: true`, `artin_diassociativity_basis_pairs: true`, `moufang: true`, `flexibility: true`; `S` has `associativity: false`, `alternativity: false`, `artin...: true`, `moufang: false`; `K` kills the lattice as a closed bad-control algebra (`system_v6/sims/assoc_weakening_lattice_classifier/results/assoc_weakening_lattice_classifier_envelope_results.json:69-108`).
- Claim ceiling: "finite structure-constant classifier harness only; scratch diagnostic, not canonical algebra admission" (`system_v6/sims/assoc_weakening_lattice_classifier/results/assoc_weakening_lattice_classifier_envelope_results.json:37-47`).

Finite objects importable by a weld packet:

- The committed result carries classification rows and witness data, but this packet's `canon_runtime.artifact_path` is null (`system_v6/sims/assoc_weakening_lattice_classifier/results/assoc_weakening_lattice_classifier_envelope_results.json:24-35`). A weld should import from committed source/result paths, not pretend there is a standalone artifact under this sim.
- The reusable object is the finite structure-constant convention: left/right parenthesized products over `C[k,i,j]` plus the O/S/H/K witness rows and controls.

### A2. `g2_forced_vs_installed_discriminator`

What it computes:

- The object distinguishes bare root constraints from installed carrier constraints: bare roots are "finite multiplication table" plus "nonzero commutator/order-sensitivity witness"; installed constraint is "7 anticommuting imaginary units with Fano/Cayley-Dickson closure (Cl(6)/3-qubit-floor family)" (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:2-13`).
- Claim ceiling: "scratch diagnostic only: G2 forced-vs-installed discriminator, no promotion or canonical admission"; classification is `scratch_diagnostic` (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:37-44`).
- Derivation dimensions are engine-stable: H has nullity/dim Der `3`, M2R has `3`, O has `14`, and corrupted O falls to `3` in JAX (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:110-147`), Julia (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:149-185`), and PyTorch (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:187-223`).
- Crossover proofs preserve the forced/installed split: H and M2R bare-root SAT, O seven-unit closure SAT, H seven-unit closure UNSAT, erased closure control SAT (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:54-90`).
- Decision: `forced_by_root: false`, `installed_by_carrier_constraint: true`, verdict `INSTALLED_NOT_FORCED` (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:92-108`).

Finite objects importable by a weld packet:

- Derivation-dimension table: H=3, M2R=3, O=14, O_corrupted=3 across JAX/Julia/PyTorch (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:110-223`).
- Installed seven-unit/Fano/Cayley-Dickson closure predicates and their erased/corrupted controls (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:46-53`, `system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:54-90`).

### A3. `pg32_sedenion_incidence`

What it computes:

- Ceiling: scratch diagnostic for "sedenion structure-constant incidence, plane alternativity split, and two-term zero-divisor graph only; no canonical promotion"; classification `scratch_diagnostic` (`system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:18-29`).
- Construction: line extraction from table products, canonical oriented octonion table, seven octonion triples, and sedenion rule `(a,b)(c,d)=(ac-conj(d)b, da+b conj(c))` (`system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:30-70`).
- The audit confirms the sedenion table is built from seven oriented octonion triples via `cd_double(octonion_table())`, not hard-coded as a static 16x16 product list (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:76-78`).
- Incidence count: 35 lines over points 1..15, every pair exactly one line (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:79-89`).
- Plane split: 15 total planes, 8 genuine octonion planes, 7 closed non-alternative sedenion planes; non-alternative spot witness `(1,2,12)` has residual `-2 e15` (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:91-99`).
- Zero divisor structure: `(e1 + e10)(e5 + e14) = 0` by term cancellation (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:100-108`); ordered zero-divisor pair count 84, component count 7, each component size 6 (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:110-114`).
- Controls: octonion restriction has 7 lines, 0 pair violations, 0 ordered zero-divisor pairs; scrambled signed-entry control has 37 lines and 6 pair-axiom violations (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:116-124`).
- Engine values agree on line count 35, plane count 15, genuine octonion planes 8, non-alt planes 7, ordered zero divisor pairs 84, zero-divisor components 7, and octonion zero-divisor pair count 0 (`system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:203-240`).

Finite objects importable by a weld packet:

- Seven oriented octonion triples and the CD sedenion construction rule (`system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:30-70`).
- The 35-line PG(3,2) incidence, 15-plane split, and two-term zero-divisor graph summary (`system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:203-240`).
- Octonion restriction control lines and zero-divisor absence (`system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:73-120`).

### A4. Older B1/B3 associator results

What they compute:

- The branch doc carries a hard ceiling: "scratch/formal scout evidence only"; it does not admit final M(C), M(C+NA), PEPS3D, Axis0, bridge, physics, gravity, or consciousness (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:1-3`, `system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:187-198`).
- Core readout: `alpha(A,B,C; psi) = ((A*B)*C)psi - (A*(B*C))psi`, where `*` is compose-then-project-back-into-admissible-surface; the nonassociativity lives in constraint return/cell gluing, not raw matrix multiplication (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:21-28`).
- Three-input/three-qubit minimum: edge tests order/noncommutation, face tests holonomy/loop defect, 3-cell tests associator/bracketing defect; three inputs/three qubits are required (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:29-38`).
- B1 values: product gap 2, spinor gap 2, density gap 0, raw matrix associativity gap 0, density sign gap 0, spinor sign gap 2 (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:60-70`).
- B1 carrier lesson: "`rho=|psi><psi|` erases this associator witness"; carrier must preserve finite spinor-network sign/bracket information, density-only quotient is not enough (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:72-78`).
- B2 basin: associativity-required keeps `{H}`; nonassociativity-not-required keeps `{H,O}`; sedenions remain excluded by zero divisors/norm failure, not associativity alone (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:104-126`).
- B3 separates H/M2C as noncommutative associative rows, O as alternative nonassociative without finite zero-product witness, J3(O) as formally real nonassociative Jordan observable, S as explicit zero-divisor graveyard, and R/C as commutative controls (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:152-172`).
- The lifted-bracketing result allows only finite 3-qubit spinor-cell bracketing, density-only erasure, quaternion/alternativity controls, and JAX/Julia agreement (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:41-47`).
- It blocks final M(C), octonion primitive carrier admission, Axis0, bridge, physics, and formal admission (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:56-80`).
- It explicitly states the carrier boundary: octonion coordinates are diagnostic, not primitive; the carrier remains a finite spinor network cell (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:83-107`).
- Its finite map is `alpha_O : (psi in (C^2)^3, x,y,z in O_basis) -> lifted spinor/component-probe delta between psi*((xy)z) and psi*(x(yz))` (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:125-133`).
- Its density-erasure control says left/right products are `e7` and `-e7`, normalized spinors differ by sign, and `rho=|psi><psi|` is unchanged (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:137-148`).
- Its collapse controls cover repeated-input alternativity, quaternion associative subalgebra, and raw matrix composition associativity (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:149-214`).

### A5. Standalone finite carrier artifact on disk

- `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` is a concrete import candidate: it contains the octonion algebra, basis labels `1,e1,...,e7`, bracket convention `left`, dimension 8, shape `[8,8,8]`, table version `algebra_structure_constants_v1`, proof tag, and derivation source (`system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:786-819`).
- It has Z3 verdicts for octonion closure over 64 basis products and 512 bound structure constants (`system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:820-833`).
- It has an octonion nonassociative basis associator SAT witness over 512 checked triples (`system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:846-860`), continuing to the basis triple `(e1,e2,e4)` and noncommutativity witness (`system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:860-893`).
- It has quaternion controls: no nonzero basis associator and closed 4-dim structure constants (`system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:901-918`).

## B floor delta analysis

The committed M(C,t) packet is a geometric/front-door dynamic admissibility packet over a finite C^2 spinor support. The nonassociative weld changes specific fields; it does not require rebuilding the tower.

Current floor fields:

- The reconciled object is `M(C,t) = (S_t, C_t, Probe_t, Val_t, ~_t, Q_t, Adm_t, E_t, Poss_t, H_t, R_t, Var_t, U_t, Ctrl_t, Rec_t)` (`system_v6/receipts/mct_reconciled_spec_20260609.md:12-43`).
- `S_t` is finite support, `C_t` active constraints, `Probe_t` finite probes, `~_t` probe-induced equivalence, `Q_t` quotient classes, `U_t` finite update composition, and `Ctrl_t/Rec_t` controls/receipts (`system_v6/receipts/mct_reconciled_spec_20260609.md:25-41`).
- The convergence table already adopts finite support, finite probes, probe equivalence, finite admissibility, relation data, five-operation update vocabulary, order sensitivity, SMT finite tables, reindexing, and folding (`system_v6/receipts/mct_reconciled_spec_20260609.md:45-59`).
- The current build card pins the carrier chart as `psi_s(phi_i, chi_j; eta_k) = (e^{i(phi_i+chi_j)} cos(eta_k), e^{i(phi_i-chi_j)} sin(eta_k))`, unit norm in C^2, with a 384-row grid (`system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:23-32`).
- Current probes are `P_density`, `P_shell`, `P_loop`, `P_order`, `P_phase`, and readout-only Axis0-gradient rows, with computed support hash and presentation IDs (`system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:29-32`).
- Current five operations are compression, expansion, warping, folding, and reindexing as measured behaviors (`system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:44-58`).

Field deltas for the weld:

- `S_t`: current `psi in C^2` 384-row support cannot by itself carry the B1 three-input associator floor. The weld needs a finite support extension, not a replacement by doctrine prose: either `S_t x O_basis^3` for direct O operation triples, or the B1 floor `psi in (C^2)^3` crossed with finite `x,y,z in O_basis` (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:115-133`). The existing C^2 chart rows can survive as a projection/control lane, but the associator witness requires three spinor sites or an explicit octonion-carrier support.
- `C_t`: add an installed carrier constraint row for seven anticommuting imaginary units/Fano-CD closure, with G2 derivation-dimension check as a carrier constraint, not a bare-root consequence (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:2-13`, `system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:92-108`).
- `Probe_t/Val_t`: current density/shell/loop/order/phase rows survive only if their domain is lifted or projected consistently. Add bracketing-sensitive rows: `P_assoc_vec`, `P_assoc_norm`, `P_assoc_component_probe`, `P_bracket_side`, `P_density_erasure`, `P_g2_dim_der`, `P_g2_closure`, and branch-only `P_zero_divisor` / `P_pg32_incidence` if sedenion is active.
- `~_t/Q_t`: the quotient must be computed at the carrier/lifted-spinor level before density quotienting. B1 says density-only erases the witness (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:72-78`), and the lifted result records density gap 0 while spinor gap is 2 (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:137-148`). Therefore `rho`-only quotient is a negative/erasure control, not the main weld quotient.
- `U_t`: composition-order tests must extend from binary sequence sensitivity to ternary bracketing sensitivity. The whole-physics ledger separates `ab != ba` from `(ab)c != a(bc)` (`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:553-559`), and the sequential spinor source says nonassociativity needs a triple operation (`/Users/joshuaeisenhart/wiki/concepts/sequential-universe-spinor-network-physics-model.md:197-223`).
- `H_t/R_t/Var_t`: preserve carrier-choice branches, killed controls, and density-erasure ledger. Do not hide octonion-direct, Cl(6)/3-qubit, sedenion, or split-O as "chosen" by a single packet.
- `Ctrl_t`: add H/quaternion associativity, O alternativity repeated-input collapse, density-only erasure, raw matrix associativity, drop-bracketing, corrupted O/Fano, sedenion zero-divisor, and label/probe shuffle controls.

Implication: the weld is a new bounded M(C,t) packet variant that imports the current M(C,t) field contract and adds one load-bearing associator operation. It should not rebuild terrain, flux, Axis0, Xi, bridge, or physics layers.

## C bracketing measurement spec

Source-grounded doctrine:

- Associativity is not primitive. The equality `(ab)c = a(bc)` is allowed only when the active finite probe family cannot distinguish `((ab)c)` from `(a(bc))` under `~_M` (`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:541-551`).
- Sequence sensitivity and bracketing sensitivity are separate tests: `ab != ba` is noncommutation; `(ab)c != a(bc)` is nonassociativity (`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:553-559`).
- Nonassociativity is an observable/probe-side fork, not a new root constraint; O remains live when associativity is not required and observable/Jordan side is primary (`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:561-572`).
- Three sites are the minimum floor: `psi in (C^2)^3`, complex dimension 8, real dimension 16; three sites can show path/bracketing order; the associator becomes a possible coordinate/readout (`/Users/joshuaeisenhart/wiki/concepts/sequential-universe-spinor-network-physics-model.md:184-223`).

Finite map:

```text
alpha_O(psi, x, y, z) =
  psi * ((x*y)*z) - psi * (x*(y*z))
```

Use the exact B1/lifted form as the source lock: `alpha_O : (psi in (C^2)^3, x,y,z in O_basis) -> lifted spinor/component-probe delta between psi*((xy)z) and psi*(x(yz))` (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:125-133`). For direct octonion carrier branch, the algebraic core is the structure-constant associator `((x*y)*z) - (x*(y*z))`, with the O witness `(e1,e2,e4)` residual `2 e7` (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:23-28`).

Probe family:

- `P_assoc_vec`: signed residual vector in the O basis or lifted spinor coordinate lane.
- `P_assoc_norm`: norm/bin of residual.
- `P_assoc_component`: selected component-probe row, source-compatible with the B1 component probe.
- `P_bracket_side`: left/right parenthesization label when preserved by the quotient key.
- `P_density_erasure`: density-only readout, expected to erase the sign witness for B1.
- `P_g2_dim_der` and `P_g2_closure`: carrier constraint rows, expected H/M2R=3 and O=14 under installed closure.
- `P_alt_control`: repeated-input alternativity collapse for O.
- Optional branch probes: `P_pg32_line`, `P_pg32_plane_split`, `P_zero_divisor_pair` for sedenion branch.

Controls:

- Density-only erasure must collapse the B1 witness while full spinor/carrier probes see it (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:72-78`; `system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:137-148`).
- Quaternion/H associative subalgebra must collapse (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:180-214`).
- O repeated-input alternativity must collapse (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:149-179`).
- Raw matrix composition must remain associative and therefore not be the claim (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:211-214`).
- Drop-bracketing control already exists in the v1 envelope and flips quotient coupling: `drop_bracketing_control.all_engines_flip: true`, `quotient_changed: true` (`system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json:2969-2998`); the later negative-control table repeats `drop_bracketing.all_engines_flip: true` and quotient changes in every engine (`system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json:3729-3750`).
- The v1 quotient key already includes `bracketing_visible_in_key: true`, an associator norm 2, bracket label/readout, `cl6_dim: 64`, and octonion nonzero components (`system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json:3790-3821`). This is scratch fuel, not admission.
- Corrupted O/G2 control must reduce the O derivation dimension from 14 to 3 (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:130-147`).
- Sedenion branch controls must preserve zero-divisor structure and not promote S as normed division (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:100-124`; `system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:115-126`).

Kill conditions:

- Kill the weld claim if full carrier/lifted-spinor probes fail to see a nonzero O associator for the pinned witness.
- Kill if density-only quotient does not erase the sign witness in the B1 control.
- Kill if H/quaternion associative or O alternativity controls fail to collapse.
- Kill if raw matrix associativity is accidentally used as positive evidence.
- Kill if `drop_bracketing` does not change the quotient when bracketing rows are declared load-bearing.
- Kill if G2 is reported as forced by bare root constraints rather than installed by the carrier constraint.
- Kill if sedenion zero divisors are smoothed into admissible normed carrier status.
- Kill if the packet claims final M(C), primitive octonion carrier admission, Axis0, bridge, or physics.

## D carrier choice points (preserved)

Do not resolve these in the mine. A future packet can run one branch as the main bounded object and keep the others in `Var_t`.

| Choice | Standing source pins | Standing exclusions / cautions | Preserved status |
|---|---|---|---|
| (a) Octonion algebra directly via structure constants | O associator witness `(e1,e2,e4)` residual `2 e7` (`system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:23-28`); on-disk O structure constants artifact with dim 8, basis labels, left bracket convention (`system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:786-819`); O derivation dimension 14 under installed closure (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:130-147`). | B1/lifted boundary says octonion coordinates are diagnostic, not primitive; carrier remains finite spinor network unless later gate admits load-bearing O (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:83-107`). | Live branch; strongest finite algebra object on disk, but not admitted as primitive carrier. |
| (b) Cl(6)/3-qubit floor | G2 packet's installed constraint is tied to "Cl(6)/3-qubit-floor family" (`system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:12-13`); lifted B1 finite map uses `psi in (C^2)^3` (`system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:125-133`); sequential source says three spinor sites are the minimum (`/Users/joshuaeisenhart/wiki/concepts/sequential-universe-spinor-network-physics-model.md:184-223`). | Current M(C,t) packet uses a C^2 chart, not the three-spinor floor (`system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:23-32`). This requires support extension. | Live branch; likely weld-friendly because it respects the current "spinor network carrier first" caution, but not resolved here. |
| (c) Sedenion level with zero divisors | PG(3,2) incidence, 15 planes, 7 non-alt sedenion planes, 84 ordered zero-divisor pairs, 7 components (`system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:79-114`). | B2 says S is excluded by zero divisors/norm failure, not by associativity alone (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:115-126`); B3 names S as explicit zero-divisor graveyard row (`system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:152-172`). | Preserve as constraint/graveyard or side-branch discriminator, not default admissible carrier. |
| (d) Split-octonion / split-G2 variants | Current ladder says carrier discriminators have DONE compact G2/lattice/PG(3,2) and NEXT includes `split-O/split-G2` (`system_v6/README.md:67-73`). Existing maps mark split-O/split-G2 missing as a fixture and preserve it as a variant (`system_v6/receipts/nonassoc_math_map_20260609.md:35-36`, `system_v6/receipts/nonassoc_math_map_20260609.md:115-124`). | Absence searches found no committed split-O/split-G2 packet result under the target weld terms; see section F. | Live queued branch, not part of the first weld unless selected explicitly. |

## E sim shape

Bounded future packet shape, not a build:

```text
packet_id: mct_nonassoc_weld_packet_v0
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
main_claim:
  A finite M(C,t) packet can compute one load-bearing bracketing-sensitive
  associator operation over a source-pinned finite carrier support, with
  density-erasure, quaternion/alternativity, G2-installed, and drop-bracketing
  controls.
```

Finite object:

- Start from the committed M(C,t) tuple fields (`system_v6/receipts/mct_reconciled_spec_20260609.md:12-43`).
- Main support is one bounded branch, not all branches:
  - Option B-friendly support: `S_t = {(psi, x, y, z, bracket) : psi in finite (C^2)^3 witness set, x,y,z in O_basis bounded triples}`.
  - Direct-O support branch: `S_t = {x,y,z in O_basis}` plus a projection/lift row to the spinor floor.
- Recommended bounded triple set for first packet: the positive O witness `(e1,e2,e4)`, quaternion control `(e1,e2,e3)`, repeated-input alternativity control `(e1,e1,e4)`, and a small deterministic basis sweep. A full `8^3=512` basis sweep can be a verification sidecar if cheap, but the packet remains one object/one claim.
- Import finite O structure constants from `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` or regenerate under the exact same table/version/hash policy. Import G2 dimension facts and sedenion incidence only as branch/control rows, not as a tower rebuild.

Probe families:

- Surviving current rows: `P_density`, `P_order`, `P_phase`, and relation/update rows survive when lifted to the new support; `P_shell`, `P_loop`, and Axis0 readout rows are projection-only unless the three-spinor branch defines an explicit shell/loop projection.
- New rows: `P_assoc_vec`, `P_assoc_norm`, `P_assoc_component`, `P_bracket_side`, `P_density_erasure`, `P_g2_dim_der`, `P_g2_closure`, `P_alt_control`, and optional branch probes `P_pg32_line`, `P_zero_divisor_pair`.

Operations:

- Keep the five current measured operations: compression, expansion, warping, folding, reindexing (`system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:44-58`).
- Add one sixth operation for this weld packet only: `associator_bracketing`.
- `associator_bracketing` applies the ternary pair of composites `((x*y)*z)` and `(x*(y*z))`, records the residual, then updates `Probe_t`, `~_t`, `Q_t`, `H_t`, and `R_t` according to whether bracketing rows are active.
- The binary order tests from current M(C,t) remain separate from ternary bracketing tests.

Controls:

- Full carrier/lifted-spinor positive O witness nonzero.
- Density quotient erasure.
- H/quaternion associative collapse.
- O alternativity repeated-input collapse.
- Raw matrix composition associative collapse.
- Drop-bracketing quotient flip.
- G2 installed-vs-forced control: H/M2R bare-root SAT but not G2 closure, O dim Der 14, corrupted O dim Der 3.
- Sedenion zero-divisor branch marked graveyard/control unless explicitly selected as the branch under test.
- Label/probe shuffle must not fake bracketing evidence.

Kill conditions:

- Any listed control fails.
- The packet computes only density rows and therefore cannot see the associator.
- The packet conflates order sensitivity with bracketing sensitivity.
- The packet claims G2 is root-forced.
- The packet treats octonion primitive carrier admission as earned.
- The packet bundles split-O, sedenion, Cl(6), direct-O, and M(C,t) terrain into one tower rebuild.

Ceiling:

- `scratch_diagnostic`, no canonical carrier admission, no final M(C), no Axis0, no bridge, no physics. This is one bounded weld packet per the "MINE FIRST" workflow and carrier-discriminator ladder (`system_v6/README.md:51-73`).

## F absence verdicts

Absence rule target: distinguish source math from built packet.

Verdict F1: the source math is not absent. Associator, bracketing quotient, G2 carrier constraint, and sedenion zero-divisor structures are on file in the cited packets above.

Verdict F2: the exact M(C,t) nonassociative weld packet is not built in the searched surfaces.

Grep quote:

```text
$ rg -n -i --glob '!system_v6/receipts/weld2_nonassoc_integration_mine_20260610.md' 'weld2_nonassoc|nonassociative carrier integration|M\(C,t\).*bracketing-sensitive|bracketing-sensitive.*M\(C,t\)|M\(C,t\).*nonassociative carrier|nonassociative carrier.*M\(C,t\)' system_v6/receipts system_v6/sims system_v5/READ\ ONLY\ Reference\ Docs 'READ ONLY Legacy core_docs' ~/wiki/raw
(no matches)
```

Verdict F3: octonion/M(C,t) and "associator as measured manifold operation" target phrases are not on file as a completed weld. This is a sim/receipt-not-yet-built absence, not a math absence.

Grep quote:

```text
$ rg -n -i --glob '!system_v6/receipts/weld2_nonassoc_integration_mine_20260610.md' 'octonion.*M\(C,t\)|M\(C,t\).*octonion|associator.*measured manifold|measured manifold.*associator' system_v6/receipts system_v6/sims system_v5/READ\ ONLY\ Reference\ Docs 'READ ONLY Legacy core_docs' ~/wiki/raw
(no matches)
```

Verdict F4: sedenion/M(C,t) weld is not built. Sedenion math exists as PG(3,2)/zero-divisor scratch evidence; an M(C,t) sedenion weld does not.

Grep quote:

```text
$ rg -n -i --glob '!system_v6/receipts/weld2_nonassoc_integration_mine_20260610.md' 'sedenion.*M\(C,t\)|M\(C,t\).*sedenion|zero[- ]?divisor.*M\(C,t\)|M\(C,t\).*zero[- ]?divisor' system_v6/receipts system_v6/sims system_v5/READ\ ONLY\ Reference\ Docs 'READ ONLY Legacy core_docs' ~/wiki/raw
(no matches)
```

Verdict F5: split-O/split-G2 is on the ladder and in maps as a preserved future variant, but no completed split-O/split-G2 carrier packet is found in the target weld scope.

Grep quote:

```text
$ rg -n -i --glob '!system_v6/receipts/weld2_nonassoc_integration_mine_20260610.md' 'split[- ]?octonion|split[- ]?O|split[- ]?G2|split G2' system_v6 system_v5/READ\ ONLY\ Reference\ Docs 'READ ONLY Legacy core_docs' ~/wiki/raw
system_v6/README.md:71:D. Carrier discriminators - DONE: G2 installed, lattice seats, PG(3,2)/box-kites. NEXT: split-O/split-G2; Cl(8) triality; ring_checkerboard_support_graph_probe.
system_v6/receipts/math_geometry_test_map_20260609.md:36:| split `G2` | Build split-octonion table with indefinite norm; prove automorphism preserves split multiplication and `(3,4)` metric signature; compact-control must fail signature. | NO. | Solver sidecars ready; algebra engines used-unproven. | Missing split-octonion carrier, controls, and compact-vs-split discriminator. |
system_v6/receipts/nonassoc_math_map_20260609.md:35:| split octonions | Split branch tests signature/probe dependence, not just compact normed division. | Build split-O table and `(4,4)` norm; derive split `G2(2)` automorphism preserving indefinite form; compact-control fails signature. | NO | READY algebra/solver; definitions needed. | Missing split-O constants, metric signature controls, and split-vs-compact discriminator. |
system_v6/receipts/nonassoc_math_map_20260609.md:36:| split `G2` | Keeps `G2` variants alive; prevents compact `G2` collapse. | Prove derivation/stabilizer dimension for split-O and signature `(3,4)` action; compact-O control fails. | NO | READY once split-O fixture exists. | Needs split-O carrier first. |
system_v6/receipts/nonassoc_math_map_20260609.md:115:2. `split_octonion_split_g2_discriminator`: split-O constants, indefinite signature, split `G2(2)` derivations, compact-control failure. Depends on split-O foundations.
system_v6/receipts/nonassoc_math_map_20260609.md:124:| split octonions / split `G2` | Need canonical split-O multiplication/signature convention and compact-vs-split controls. |
system_v6/receipts/nonassoc_math_map_20260609.md:141:| Split forms | No split-O/split-`G2` fixture. | Build definitions first, then compact-vs-split discriminator. |
```

Verdict F6: there are nearby M(C,t) mining and nonassoc mapping receipts, but they are not this weld packet.

Grep quote:

```text
$ rg -n -i --glob '!system_v6/receipts/weld2_nonassoc_integration_mine_20260610.md' 'weld2_nonassoc|nonassoc.*integration|bracketing.*M\(C,t\)|octonion.*M\(C,t\)|M\(C,t\).*octonion|associator.*measured manifold' system_v6/receipts system_v6/sims system_v5/READ\ ONLY\ Reference\ Docs 'READ ONLY Legacy core_docs' ~/wiki/raw
system_v6/receipts/mct_mine_adjudication_20260610.md:65:| 1. Finite dynamic packet fields: support, constraints, probes, quotient, admissibility, relation/history/readout/variant/update/control/receipt fields | `M(C)` minimum packet shape is `S, C, P, ~_P, Adm_C, composition/bracketing, local readouts, controls, receipts` (`/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:98-131`). Reconciled `M(C,t)` adds `S_t, C_t, Probe_t, Val_t, ~_t, Q_t, Adm_t, E_t, Poss_t, H_t, R_t, Var_t, U_t, Ctrl_t, Rec_t` (`system_v6/receipts/mct_reconciled_spec_20260609.md:12-43`). | LANDED as source math/spec. NEEDS-BUILD as a v6 geometric result receipt. |
system_v6/receipts/nonassoc_math_map_20260609.md:140:| v5 row promotion | Still open: most v5 nonassoc rows are `scratch_diagnostic` / `formal_scout`, not admitted. | Each new sim needs `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, controls, and validator path. |
```

## G sources-read line

Sources read: `system_v6/README.md:43-73`; `system_v6/receipts/mct_reconciled_spec_20260609.md:1-115`; `system_v6/receipts/nonassoc_math_map_20260609.md:35-36,115-124,140-141`; `system_v6/receipts/math_geometry_test_map_20260609.md:36,98`; `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:1-90`; `system_v6/sims/assoc_weakening_lattice_classifier/audit_verdict.md:17-70`; `system_v6/sims/assoc_weakening_lattice_classifier/results/assoc_weakening_lattice_classifier_envelope_results.json:1-120`; `system_v6/sims/g2_forced_vs_installed_discriminator/results/g2_forced_vs_installed_discriminator_envelope_results.json:1-230`; `system_v6/sims/pg32_sedenion_incidence/audit_verdict.md:70-145`; `system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json:1-240`; `system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:1-205`; `system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json:35-225`; `system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json:2960-3000,3725-3840`; `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json:720-939`; `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/whole-physics-model-processing-ledger-2026-06-05.md:533-572`; `/Users/joshuaeisenhart/wiki/concepts/sequential-universe-spinor-network-physics-model.md:184-225`; grep surfaces `system_v6/receipts`, `system_v6/sims`, `system_v5/READ ONLY Reference Docs/`, `READ ONLY Legacy core_docs/`, and `~/wiki/raw`.
