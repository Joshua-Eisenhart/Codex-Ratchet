# Constraint, Axiom, And Current Sim Audit

Date: 2026-05-23

Status: audit/control packet only. This is not formal admission evidence.

## Evidence Roles

This packet separates source roles:

- `repo_local_primary`: durable repo docs and read-only reference tables.
- `sidequest_numbered_grok_sim_iter_223`: useful enumeration/gate proposal from `system_v5/grok_sim`, advisory only.
- `clean_rebuild_20260523`: current clean runnable evidence surface created after contamination was identified.
- `formal_scouts`: current broad formal estate, dirty and contaminated until quarantined or rebuilt.

Machine receipt:

```text
system_v5/ops/constraint_audit_20260523/results/constraint_axiom_registry_enforcement_audit_results.json
system_v5/ops/constraint_audit_20260523/results/constraint_axiom_torch_gate_pack_results.json
```

Fresh command:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/constraint_audit_20260523/sim_constraint_axiom_registry_enforcement_audit.py
```

Result: `all_pass = true` for the registry-enforcement audit itself.

Torch-native gate-pack result: `all_pass = true`, `uses_numpy = false`.

## Root Constraints

| Code | Name | Enforceable statement | Enforcement |
|---|---|---|---|
| F01 | Finitude | All carriers, probes, operators, paths, registries, and witnesses are finite. | Every runnable sim must report finite carrier dimensions, finite registries/path counts, finite witnesses, and terminate. Reject continuum or completed-infinity primitives. |
| N01 | Noncommutation | Composition is order-sensitive in general; AB and BA cannot be swapped by default. | Every order claim needs a noncommuting order gap plus a commuting negative control that collapses. |

## Read-Only Extended Axioms

These come from `Formal constraints and geometry .md`, not from the sidequest EC numbering.

| Code | Name | Statement | Main enforcement gate |
|---|---|---|---|
| EA01 | No primitive identity | Identity is admitted only relative to a finite probe family. | Reject bare token identity; require finite probe-family identity witness. |
| EA02 | Probe-relative indistinguishability | `a ~ b` iff every active finite probe fails to distinguish them. | Probe-vector equality over declared finite probe family; z-only equality is a graveyard control. |
| EA03 | Boundary / contrast identity | Self-identity requires boundary or contrast under admissible probes. | Require contrast class or boundary probe; reject uncontrasted center-point identity. |
| EA04 | No primitive time / causality | Ordered composition exists without wall-clock time. | Causal/order claims must be commutator or composition-order readouts, not clock labels. |
| EA05 | No primitive coordinates / metric / geometry | Coordinates and metrics are induced after the finite QIT carrier. | Use invariant readouts and chart-scramble controls; reject raw coordinate distance as ontology. |
| EA06 | No closure by default | Closure, completeness, identity, and inverse properties must be earned. | Operation families need closure/inverse/identity checks; amplitude damping should fail inverse. |
| EA07 | Finite witness discipline | Every admissible claim requires a finite witness. | Require receipt path, finite fixture, reproducible command, and bounded claim ceiling. |

## Numbered EC Catalog Found In Sidequest

Claude's EC07-EC16 list is real in `system_v5/grok_sim/iters/iter_223_test_missed_derived_constraints.py`, but that file is sidequest/advisory and NumPy-based. The clean registry maps each EC row to a canonical enforcement row.

| EC | Name | Canonical enforcement row |
|---|---|---|
| EC07 | No primitive equality | EA02 |
| EC08 | No cloning / no broadcasting for noncommuting states | EC08 |
| EC09 | No primitive probability | EC09 |
| EC10 | No primitive optimization / utility | EC10 |
| EC11 | No primitive time / causality | EA04 |
| EC12 | No closure by default | EA06 |
| EC13 | No outside observer | EC13 |
| EC14 | No global total order | EC14 |
| EC15 | No primitive coordinates / metric | EA05 |
| EC16 | No semantic smuggling | EC16 |

Important: no source that labels `EC01` through `EC06` by that exact EC namespace was found in the current repo search. Do not invent those names. The closest earlier material is the read-only `EA01-EA07` list, the `BC04-BC12` fences, and the C/X charter rows.

## C/X Charter Catalog

The actual YAML at `system_v4/skills/intent-compiler/constraint_manifold.yaml` contains 16 rows:

| Code | Name | Maps to |
|---|---|---|
| C1_finitude | finite state representations | F01 |
| C2_noncommutation | order-sensitive operators | N01 |
| C3_cptp_admissibility | trace/positivity/complete-positivity preservation | CPTP contract |
| C4_operational_equivalence | identity by admissible-probe indistinguishability | EA01/EA02 |
| C5_entropy_monotonicity | unitary entropy preservation / nonunitary entropy change | entropy flow |
| C6_dual_loop_requirement | deductive and inductive loops both required | dual-loop theorem |
| C7_spinor_periodicity | 720 degree / 8-stage spinor cycle | spinor periodicity |
| C8_ratchet_gain | nonnegative net negentropy over full cycle | ratchet gain |
| X1_gt_isolation | game labels do not alter CPTP admissibility | overlay isolation |
| X2_chirality_matters | T-first and F-first orderings differ | chirality/order |
| X3_attractor_is_nash | attractor is Nash-like under single-op deviations | attractor candidate |
| X4_structure_saturation_stalls | structure-only seeking stalls | anti-structure-only |
| X5_irrational_escape | temporary entropy increase enables escape | escape dynamics |
| X6_refinement_noncommutative | refinement operators do not commute | N01 refinement |
| X7_finite_stability | stability scoped to finite perturbations | finite basin stability |
| X8_holodeck_fixed_point | self-referential observer fixed point | observer fixed-point candidate |

Contradiction to fix: `CONSTRAINT_SURFACE_AND_PROCESS.md` says "24 constraints: C1-C8 core + X1-X8 cross-cutting." That arithmetic is 16, and the checked YAML has 16. Treat "24" as unresolved documentation drift until a master 24-row source is found.

## Base And Topology Fences

Base fences from `LADDERS_FENCES_ADMISSION_REFERENCE.md`:

| Code | Ban |
|---|---|
| BC04 | no primitive identity predicate on state-tokens |
| BC05 | no primitive equality-as-substitutability |
| BC06 | no global total order |
| BC07 | no closure by default |
| BC08 | no identification except via finite probe families |
| BC09 | no probabilistic primitives at base |
| BC10 | no metric/distance/norm/chart as primitive |
| BC11 | no optimization or utility primitives |
| BC12 | no semantic smuggling |

Topology/relation fences:

| Code | Ban |
|---|---|
| T1_01 | compatibility not global by default |
| T2_01 | adjacency does not imply direction, precedence, or temporal ordering |
| T2_02 | adjacency does not imply metric distance |
| T2_03 | adjacency does not imply reachability or transitive closure |
| T3_01 | neighborhoods do not exist by default |
| T3_02 | neighborhoods do not imply openness, limits, or convergence |
| T4_03 | same endpoints do not force path equivalence |
| T6_01 | compatibility/adjacency do not imply identity/equality |
| T6_03 | no scalar rank/distance from topology by default |
| T8_01 | no geometry/metric/coordinates at topology layer |
| T8_02 | no continuity/differentiability/smoothness by default |
| T8_03 | topology does not complete semantics by default |

## Enforcement Pattern

Every enforceable constraint row should have four pieces:

1. Static check: what source pattern is forbidden.
2. Runtime gate: what the sim must measure.
3. Graveyard controls: what must fail.
4. Receipt status: where the current evidence lives and what ceiling applies.

Minimum examples:

| Constraint | Static check | Runtime gate | Graveyard control |
|---|---|---|---|
| F01 | finite dimensions/counts required | finite `carrier_dim`, `path_count`, `registry_count` | implicit continuum or constant fake witness |
| N01 | named noncommuting pair required | order gap vs commuting collapse | commuting pair or hidden joint eigenspace |
| EA02 / EC07 | no single-probe equality | finite probe-vector comparison | z-only equality |
| EC08 | no copy primitive for noncommuting states | no-cloning fidelity/linearity bound | CNOT-copy of nonorthogonal pair |
| EC09 | every probability names a probe | same state, different probes produce different values | standalone `p(x)` |
| EC10 | objective must be named | different functionals choose different optima | primitive "best" state |
| EA04 / EC11 | no wall-clock causality primitive | order gap from commutator/composition | clock-index-only causality |
| EA06 / EC12 | closure must be proven | identity/inverse/closure checks | amplitude damping inverse |
| EC13 | observer inside joint state | reduced-state/back-action changes under joint construction | external classical observer |
| EC14 | no scalar total rank | same entropy but different operators / incomparable vectors | entropy-only ontology |
| EA05 / EC15 | no coordinate primitive | invariant readout plus chart control | raw chart distance |
| EC16 | no renamed classical property without proof | explicit quantum/classical contrast | "coherent info is just MI" |

Executable gate pack:

```text
system_v5/ops/constraint_audit_20260523/sim_constraint_axiom_torch_gate_pack.py
```

Covered gates:

| Gate | Status |
|---|---|
| F01_finitude | passed |
| N01_noncommutation | passed |
| EA01_EA02_identity_equality | passed |
| EA03_boundary_contrast_identity | passed |
| EA04_EC11_no_primitive_time | passed |
| EA05_EC15_no_primitive_metric | passed |
| EA06_EC12_no_closure_by_default | passed |
| EA07_finite_witness_discipline | passed |
| EC08_no_cloning | passed |
| EC09_no_primitive_probability | passed |
| EC10_no_primitive_optimization | passed |
| EC13_no_outside_observer | passed |
| EC14_no_global_total_order | passed |
| EC16_no_semantic_smuggling | passed |

This is still an audit/control packet, not a formal promotion. It does, however, give Claude and future Codex runs a local torch-native executable map for the constraints that were previously scattered across docs and sidequest results.

## Current Sim And Work Audit

### Clean Rebuild Lane

Current trusted runnable lane:

```text
system_v5/ops/clean_rebuild_20260523/
```

Receipts: 8/8 pass.

Key results:

- `rebuild_001`: finite source-engine chart rebuilt; noncommuting order gap nonzero and commuting gap collapses.
- `rebuild_002`: Hopf/Weyl pre-axis flux rebuilt; fiber density stationary, base density traversing, chirality current nonzero.
- `rebuild_003`: spinor entropy carrier rebuilt; b0 signs and Clifford entropy seat verified.
- `rebuild_004`: Xi/rho_AB bridge families rebuilt; multiple live bridge rows, final Xi/Phi0 still blocked.
- `rebuild_005`: QIT-FEP finite path batch rebuilt; path posterior finite, but readouts choose different top modes.
- `rebuild_006`: matched controls kill history-window family; point-reference initially survives MI/logZ+MI.
- `rebuild_007`: point-reference survivor killed by amplitude-scrambled and related stress controls.
- `rebuild_008`: status classifier says current Axis0 survivor is `killed_or_nonrobust`, with no final survivor after rebuild 007.

Verdict: clean rebuild has a solid negative result for the current Axis0 candidate family. It does not admit final Axis0.

### Formal Scout Estate

Current broad formal estate:

- `427` `sim_*.py` files under `system_v5/ops/formal_scouts`
- `427` result JSONs under `system_v5/ops/formal_scouts/results`
- dirty/untracked contamination lines include cross-lane synthesis docs, section-connection audit probes, 64-site close probes, and Grok audit receipts.

Verdict: do not use the broad formal estate as clean evidence without quarantine or rebuild. It can be mined for candidate ideas, but not cited as current formal proof.

### Sidequest `grok_sim`

Useful finding:

- `iter_223` gives a concrete EC07-EC16 gate catalog.

Limits:

- It is sidequest-only by its own claim ceiling.
- It uses NumPy and SciPy.
- It can guide clean torch-native constraints, but should not be treated as formal admission.

### Older Tier Status

`TIER_STATUS.md` says:

- Resolution 0 root constraints and Resolution 1 admissibility charter are doctrinal, not mechanically executed.
- `constraint_manifold.yaml` has C1-C8 and X1-X8 predicates, but the old note says they were never run as a validator.

The new clean rebuild lane improves this for F01/N01 and several downstream surfaces, but it does not yet replace a full root/extended-constraint validator.

## What Needs To Be Built Next

1. Torch-native root/extended-constraint gate pack:
   - F01, N01, EA01-EA07, EC08-EC16 where distinct.
   - No NumPy.
   - Lives under clean rebuild or a new nonformal audit lane first.

2. Master numbering reconciliation:
   - Find or create a durable master list that resolves `EA01-EA07`, `EC07-EC16`, `BC04-BC12`, and `C1-C8/X1-X8`.
   - Do not invent EC01-EC06 unless the owner/source explicitly assigns them.

3. Formal estate quarantine:
   - Keep contaminated cross-lane artifacts out of formal admission.
   - Rebuild only the smallest admissible torch-native gates from clean source docs.

4. Axis0 rebuild after constraints:
   - Only after the root/extended constraint pack passes should another Axis0 bridge candidate be rebuilt.
   - The current clean evidence says the tested Axis0 candidates are killed or nonrobust.
