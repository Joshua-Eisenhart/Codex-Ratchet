# BUILD CARD - basin_information_fusion_v1 (the joint basin-information-flow object)

Original user card copied into the packet under the card-persistence rule.

```text
# BUILD CARD — basin_information_fusion_v1 (the joint basin-information-flow object)

You are codex1 (builder). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside the new dir system_v6/sims/basin_information_fusion_v1/ (file-disjoint; touch nothing outside it). NO git add/commit. Copy this card into the packet as build_card.md (the card-persistence rule).

## Why this packet exists
basin_information_fusion_v0 (commit 4c8f9bc7d) was adjudicated PARTIAL PASS: real partition-information ACCOUNTING, but NOT the joint object. Read its audit_verdict.md first — your packet must construct exactly what it held: per-class information objects computed ALONG the dynamics, not before/after table deltas.

## Read first
- system_v6/receipts/attractor_basin_criterion_20260611.md (the basin contract: S, Adm_C, R_C, trapping, escape, may/must, the 9 requirements, THE GUARD)
- system_v6/sims/basin_information_fusion_v0/ (sources + audit_verdict.md)
- system_v6/sims/basin_generating_set_sweep_v0/ + basin_rc_transition_graph_v0/ (the committed 33-cell object, G0-G5 generator rows)
- system_v6/sims/basin_grid_refinement_control_v0/audit_verdict.md (BINDING: G1 classes are CHART-RELATIVE finite structure — every G1-citing row must carry that label)
- system_v6/sims/manifold_information_throughput_v0/audit_verdict.md (CAVEAT_Q1: a record side must be CONSTRUCTED, never assigned = loss)
- .claude/skills/sim-wizard/SKILL.md or system_v5/codex_skills/sim-wizard/SKILL.md (TOOL_INTENT_MATRIX is now mandatory in build_card.md; envelopes via scripts/build_three_engine_envelope.py with per-lane package_observables)

## The object (all four rows REQUIRED, computed on the SAME committed 33-cell substrate + G0-G5 generators)
1. ENTROPY PRODUCTION ALONG ACTUAL R_C ORBITS: for each generator row, evolve explicit orbit ensembles step by step; per-step typed counting-entropy trajectory (declare the type on every row; never mix types without an explicit convention). Report production/destruction per step, not endpoint deltas.
2. RECORD RETENTION AT MERGES: when the full generator set re-merges G1's 3 chart-relative classes, CONSTRUCT the record object packet-locally: per-orbit syndrome table (which G1 class each orbit started in), then compute whether class-of-origin is recoverable from any declared readout after the merge (recoverable bits = computed counting entropy of the syndrome-given-readout), or genuinely erased. record_retained must be COMPUTED from the constructed table — assigning record := loss is the exact CAVEAT_Q1 failure and is FORBIDDEN.
3. PER-CLASS THROUGHPUT: for each terminal class (with its absent-exit proof), the class-restricted update channel and its information throughput on a pinned ensemble (typed; exact only where exactness is earned — label bounds as bounds).
4. BASIN-CONDITIONED FLOW: may/must basin membership as the conditioning variable; information flow conditioned on must-basin vs may-only cells; report whether they are distinguishable under the declared probe family (a=a iff a~b: identical-under-probes means identical, say so).

## Controls (must FLIP — byte-identical pass/fail is decorative)
- erased-record control: destroy the syndrome table -> recoverable bits must drop to 0 and the conservation defect must become nonzero, COMPUTED.
- shuffled-order control: permute the orbit step order -> the production trajectory must change (order matters; N01).
- similarity-only control: a clustering of cells WITHOUT dynamics must fail the basin-conditioned rows (THE GUARD).
- partial-record control: retain half the syndrome -> recoverable bits strictly between 0 and full, computed.

## Engineering contract
- Three engines: Julia reference (use real aligned packages — Graphs.jl/Z3.jl as in v2; declare package_observables for every load-bearing package), JAX workhorse, PyTorch first-class. SMT (z3+cvc5) binds COMPUTED values (negated identity UNSAT + erased SAT flip), never hardcoded literals.
- TOOL_INTENT_MATRIX block in build_card.md (mode decided by the matrix). Envelope ONLY via scripts/build_three_engine_envelope.py (three_engine_sim_result_v1, mode as a field). Validate with scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed (must be ok:true).
- classification = "scratch_diagnostic", promotion_allowed=false, formal_admission_allowed=false. Positive + negative + boundary sections.
- Every G1-citing row carries the chart_relative label. Vocabulary: survived/admitted/excluded/terminal class — basin words only with trapping+escape evidence attached.
- End by listing every validator command you ran and its ok status. Worker prose is not evidence; the result JSONs are.
```

## Binding Builder Addendum

object: `basin_information_fusion_v1`

claim: A scratch-diagnostic joint basin-information-flow object over the committed finite 33-cell substrate and G0-G5 generator rows, with information objects computed along actual `R_C` orbits, a packet-local G1 syndrome record at the G1->G2 re-merge, terminal-class restricted throughput, and may/must basin-conditioned flow.

ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

persistence: this file is the persisted build card.

write scope: `system_v6/sims/basin_information_fusion_v1/` only.

PIN:

```json
{
  "state_space": "committed finite 33-cell Bloch grid from basin_rc_transition_graph_v0, with G4 as the parent conditioned subset row",
  "Adm_C": "x^2 + y^2 + z^2 <= 1 over the committed grid",
  "R_C": "generator-labelled finite transition graph from basin_generating_set_sweep_v0 G0-G5 rows",
  "entropy_log_base": "natural log",
  "counting_entropy_convention": "log(number of occupied readout labels); distribution entropies are not summed into counting entropy rows",
  "G1_chart_relative_label": "G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE",
  "record_convention": "record recoverability is computed from the packet-local per-orbit G1 syndrome table; erased and partial records are table transforms, not assigned losses",
  "readout_probe_family": "one-step generator successor communicating-class signatures plus reachable-size readouts"
}
```

TOOL_INTENT_MATRIX:

```json
{
  "claim_classes": [
    "finite_basin_information_flow",
    "orbit_counting_entropy",
    "record_retention_at_merge",
    "terminal_class_throughput",
    "basin_conditioned_may_must_flow"
  ],
  "engine_tool_intent": {
    "julia": {
      "Graphs": "reference finite graph carrier for terminal-class and G1 syndrome rows",
      "Z3": "integer conservation/no-erasure proof over computed syndrome readout counts"
    },
    "jax": {
      "networkx": "workhorse finite R_C graph/orbit and basin-conditioned readout computation",
      "sympy": "exact natural-log counting entropy expressions for record and throughput counts",
      "z3": "SMT negated identity UNSAT over computed record counts",
      "cvc5": "independent SMT negated identity UNSAT over computed record counts"
    },
    "pytorch": {
      "torch.func": "batched generator-action materialization for orbit images",
      "torch_geometric": "finite graph edge_index carrier for the committed R_C substrate",
      "sympy": "exact natural-log counting entropy expressions for torch-side counts",
      "z3": "SMT negated identity UNSAT over computed record counts",
      "cvc5": "independent SMT negated identity UNSAT over computed record counts"
    }
  }
}
```

files_to_create:

- `build_card.md`
- `basin_information_fusion_v1_common.py`
- `basin_information_fusion_v1_jax.py`
- `basin_information_fusion_v1_pytorch.py`
- `basin_information_fusion_v1_julia.jl`
- `basin_information_fusion_v1_envelope.py`
- `validate_basin_information_fusion_v1.py`
- `results/basin_information_fusion_v1_jax_results.json`
- `results/basin_information_fusion_v1_pytorch_results.json`
- `results/basin_information_fusion_v1_julia_results.json`
- `results/basin_information_fusion_v1_envelope_results.json`
- `results/basin_information_fusion_v1_validator_results.json`

does_not_prove:

- invariant continuum basin geometry;
- formal basin theorem;
- canonical or admitted result;
- bridge, axis, manifold completion, physics, or universal information-scalar claim;
- packet-local Z4 radiated-record object beyond the constructed G1 merge syndrome object in this packet.
