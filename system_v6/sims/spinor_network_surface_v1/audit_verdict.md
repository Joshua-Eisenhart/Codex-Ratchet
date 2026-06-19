# Independent audit verdict - spinor_network_surface_v1

Bottom line: VERDICT = NARROW SCRATCH FIRST-FLOOR EARNED, with hard caveats.

`spinor_network_surface_v1` defeats the fatal v0 failure mode (`A_CHART_BY_CONSTRUCTION`) well enough to earn a first floor for the surface doctrine at `scratch_diagnostic` strength: the A33 chart classifier is predeclared, terminal states are generated outside the v0 Pauli-label product pattern fixture, no-structure controls now reach the real failure predicate, typed non-product rows exist, and all three backends recompute the small finite packet.

Do not overcite it. It is not full doctrine closure, not full A33 recovery, not a global quantum-Hopfield basin theorem, and not `canonical by process`. The packet is also currently untracked in this checkout, so the public repo label is: `exists` in the working tree and `passes local rerun` for the fresh audit commands below; packet classification remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Authority And Boundary

Authorities checked:

- `AGENTS.md`, `CODEX.md`, `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`, `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`, `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md`
- `system_v6/sims/spinor_network_surface_v0/audit_verdict.md`
- `system_v6/receipts/spinor_network_surface_estate_20260611.md`
- `system_v6/sims/spinor_network_surface_v1/build_card.md`

Git anchors checked:

- `f3d3ad1c1`: v0 adjudication and binding v1 design rules.
- `0dc215ad3`: repaired estate receipt, including the true `system_v5` paths.

File boundary:

- No `git add` or `git commit` was run.
- The requested write is this file only.
- Fresh validation was run in no-write or read-only form where the packet validator would otherwise rewrite `results/spinor_network_surface_v1_validator_results.json`.
- `git status --short -- system_v6/sims/spinor_network_surface_v1` shows the whole v1 packet as untracked.

## Decisive Anti-Circularity Check

Adjudication: EARNED, narrow scratch strength.

What passed:

- The A33 classifier is declared before generation in the JAX/Python lane: `A33_ROWS`, `A33_CELL_IDS`, and `chart_cell_id()` precede `terminal_patterns()` in `system_v6/sims/spinor_network_surface_v1/spinor_network_surface_v1_jax.py:98-126`.
- Recovery uses `recover_chart_structure()` over single-site reduced densities and requires `classifier_id == "A33_committed_predeclared"`, 33 rows, and at least 6 non-origin recovered cells: `spinor_network_surface_v1_jax.py:354-399`.
- Pattern generation is no longer the v0 hardcoded `x+/y+/z+` product-label fixture. It uses chiral Hopf/Weyl quaternion patterns, one entangled non-product state, and one pinned-random state: `spinor_network_surface_v1_jax.py:155-199`.
- Repaired source lineage is real: the envelope consumes `system_v5/julia_carrier/basin3_julia.jl` and `system_v5/julia_carrier/npc2_connection_geometry_julia.jl`, with source quote slices declared in `spinor_network_surface_v1_envelope.py:29-41`.

Fresh recompute:

- Positive recovered non-origin cells: 6 of 33:
  `A33_x00_y00_zp10`, `A33_x00_yp5_z00`, `A33_xp10_y00_z00`, `A33_xp5_y00_z00`, `A33_xp5_y00_zm5`, `A33_xp5_y00_zp5`.
- `pinned_random` alone recovered 3 non-origin cells and failed the six-cell predicate, so the full positive row is above that base rate but not by a huge margin.
- Two terminal-state spot checks:
  `chiral_quaternion_L` maps all four sites to `A33_xp10_y00_z00`.
  `entangled_nonproduct` maps all four sites to `A33_x00_y00_zp10`.

Caveat:

The anti-circularity repair is real but not perfectly clean. The entangled state is a computational-basis endpoint superposition, so its single-site quotients naturally hit the z chart row. The chiral n4 Hopf/Weyl construction collapses mostly onto a y-near-zero chart plane. This is not v0's explicit Pauli-axis product seed, but it is still a chart-axis-bias caveat for v2.

## Falsifier Reachability

Adjudication: EARNED.

Fresh recompute of the maximally mixed control through the same `recover_chart_structure()` predicate returned:

```json
{
  "verdict": "RECOVERY_FAIL",
  "control_fired": true,
  "registered_falsifier_fired": true,
  "recovered_cell_ids": ["A33_x00_y00_z00"],
  "recovered_nonorigin_cell_count": 0
}
```

The packet records all four no-structure controls as failing through the same predicate: maximally mixed, quotient-erased, off-axis rotated, and wrong-row classifier. This fixes the v0 string-mismatch failure.

## The 11-Item List

1. Repaired consumed paths and source quotes: EARNED. True `system_v5` paths are consumed; the estate path repair at `0dc215ad3` is respected.
2. Classifier/generation separation: EARNED with caveat. Mechanically separated; indirect chart-axis bias remains.
3. No-structure controls and falsifier reachability: EARNED. All four controls fire the real predicate.
4. Real retrieval channel / CPTP relation: PARTIAL-EARNED. The update is explicit, `rho'=(1-alpha)rho+alpha target`, with trace and positivity recomputed on edges. In audit I also recomputed fixed-target Kraus completeness and Choi positivity to numerical tolerance. But the packet does not persist a full Kraus/Choi witness ledger; it stores a class string and branch diagnostics.
5. Trapping/absent-exit from transition relation: EARNED for the finite declared graph. JAX builds a `networkx.DiGraph`; Julia uses `Graphs.SimpleDiGraph`; PyTorch uses `torch_geometric.data.Data`.
6. Spurious search coverage: EARNED for the declared finite abstraction, not globally exhaustive. It finds 6 spurious attractor IDs over 6/6 equal pair mixtures. It does not enumerate the full density-state space.
7. Non-Hermitian control same Lyapunov row: EARNED. Fresh recompute gave `V_before=0.07065523122973005`, `V_after=0.198715041338279`, `delta=0.12805981010854894` on `V(rho)=1-max terminal fidelity`.
8. Julia independent recomputation: EARNED. Julia recomputes chart, basin graph, typed rows, and Z3 rows; no v0 scalar stub pattern found in the claim rows.
9. JAX/PyTorch independence or honest mode: EARNED at small-packet level. The files are self-contained mirrors rather than a shared common module. They still implement the same algorithm, so this is cross-runtime recomputation, not independent mathematics.
10. PyTorch load-bearing autograd: EARNED narrowly. `torch.func.jacrev` gates the retrieval energy delta for one boundary seed; this is real but not broad optimization evidence.
11. Typed `S(A|B)` and premature evaluation: EARNED. `S(A|B)` requires a predeclared bipartition and produces negative conditional entropy rows for non-product states; missing bipartition raises `MissingStructure`.

## Doctrine Expectations

1. Basin contract on the surface: PARTIAL.
Witness: finite transition graph with 48 nodes, 48 edges, 14 terminal SCC rows, absent-exit true, stored rows trapping, max Lyapunov delta about `2.22e-16`, and 6 spurious pair-mixture attractors. Caveat: the search is exhaustive only over the declared 14 seed states / 6 pair mixtures, and the packet does not persist a full Kraus/Choi ledger.

2. Chart recoverability from independent generation: EARNED at scratch strength.
Witness: 6/33 non-origin A33 cells recovered from generated terminal network states; no-structure controls fail; pinned-random alone recovers only 3 non-origin cells and fails the predicate. Caveat: the result is partial A33 recovery with a thin margin and residual basis/axis bias.

3. Typed rows exposing network structure: EARNED at scratch strength.
Witness: `S(A|B)` rows on `A=[0]`, `B=[1,2,3]`, with non-product negative conditional entropy rows. Caveat: this proves typed network telemetry on the finite packet, not chart-level weld closure.

## Standard Checks

Fresh commands/checks:

- Runtime doctor:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --json`
  returned `summary.ok=true`.
- Generic validator:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/spinor_network_surface_v1/results/spinor_network_surface_v1_envelope_results.json`
  returned `ok=true`.
- Packet validator logic, run in-process to avoid rewriting the validator result:
  `ok=true`, `error_count=0`.
- Pytest:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/spinor_network_surface_v1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/spinor_network_surface_v1/tests`
  returned `6 passed`.
- Fresh recomputation of recovery, controls, transition traces/eigenvalues, fixed-target Kraus completeness, Choi positivity, and non-Hermitian control was performed without calling the writing lane `main()` functions.

SMT:

- z3 and cvc5 bind computed finite counts: non-origin recovery count 6, control fail count 4, spurious count 6.
- The real negated assertion is UNSAT and the mutated control-count path is SAT. This is non-tautological at finite-count level.
- Caveat: SMT proves the small integer gate, not the physics or global basin semantics.

Tool honesty:

- `networkx`, Julia `Graphs`, and PyTorch Geometric carry finite transition graph evidence.
- z3/cvc5/Z3.jl carry finite-count proof flips.
- `torch.func` carries the narrow autograd energy-delta gate.
- Tools are load-bearing for packet gates, not for promotion beyond `scratch_diagnostic`.

## Named Caveats

- `UNTRACKED_PACKET`: all v1 files are currently untracked in this checkout.
- `PARTIAL_A33_RECOVERY`: 6/33 non-origin cells recovered; this is not full A33 recovery.
- `THIN_RANDOM_MARGIN`: full recovery count 6 vs pinned-random-alone count 3.
- `RESIDUAL_AXIS_BIAS`: entangled endpoint state and chiral n4 construction still lean into chart-axis/chart-plane readouts.
- `BRANCHWISE_CPTP_LEDGER`: audit recomputed Kraus/Choi for fixed-target branches, but the packet result does not persist a complete Kraus/Choi witness table.
- `FINITE_SEED_GRAPH_ONLY`: transition graph evidence covers declared stored/corrupt/pairmix seeds, not the full density-state space.
- `PAIR_MIXTURE_EXHAUSTIVE_ONLY`: spurious search is exhaustive for 6/6 equal pair mixtures, not a global attractor search.
- `COUNT_LEVEL_SMT`: solver flips are real but only over finite counts.
- `ALGORITHM_MIRROR_BACKENDS`: Julia/JAX/PyTorch are independent files but intentionally mirror one algorithm.
- `NO_PROMOTION`: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Future-Citation Rule

Future docs may cite v1 only as:

`spinor_network_surface_v1`: untracked-on-audit, validator-passing `scratch_diagnostic` surface packet that narrowly fixes v0's A-chart circularity by separating the predeclared A33 classifier from generated chiral/entangled/pinned-random terminal states; it recovers 6/33 non-origin A33 cells, proves no-structure falsifier reachability, gives finite transition-graph basin evidence with 6/6 declared pair-mixture spurious attractors, shows cross-backend recomputation, and emits typed non-product `S(A|B)` rows.

Forbidden citations:

- full A33 chart recovery;
- full quantum-Hopfield basin contract;
- global state-space exhaustive spurious-attractor search;
- canonical by process;
- formal admission;
- explicit persisted Kraus/Choi proof ledger;
- proof that Families A/B are fully views of this network surface.

## What v2 Needs

1. Persist explicit Kraus operators or Choi matrices, trace preservation, and positivity witnesses for each retrieval branch actually used.
2. Replace the computational-basis entangled endpoint with one or more entangled families whose local quotients are not z-axis by construction.
3. Add rotated/randomized classifier-blind variants and report recovery distribution against many pinned-random families, not one pinned-random seed.
4. Expand spurious search beyond equal pair mixtures, or formally state a finite abstraction where the exhaustive denominator is the whole object.
5. Add a stricter chart-bias kill test: recovery should survive basis rotations or explain exactly which chart structures are basis artifacts.
6. Keep all claims at `scratch_diagnostic` until a committed, tracked packet passes a fresh independent audit.

## Route Truth

Wizard v4.2 Max Assembly was partial, not full. Three Codex-native read-only parent sidecars completed independent slice audits:

- anti-circularity / generation-classifier separation;
- v0 11-item and cross-backend/tool checklist;
- validators / falsifier / SMT reachability.

No child subsubagent layer was completed. No Claude/Gemini/OMX route was used. No git/index mutation was run.
