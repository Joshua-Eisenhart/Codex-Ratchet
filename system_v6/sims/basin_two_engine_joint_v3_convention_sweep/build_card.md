# BUILD CARD - basin_two_engine_joint_v3_convention_sweep (the convention-relative 64 test)

You are a codex builder. Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside the new dir system_v6/sims/basin_two_engine_joint_v3_convention_sweep/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## Why
The 64-subsubbasin prediction (2 engines x 2 loops x 4 stages x 4 substages) is RE-REGISTERED CONVENTION-RELATIVE (read system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md IN FULL, including both adjudication entries, then system_v6/receipts/substage_transition_convention_mining_20260611.md IN FULL). No owner source pins the substage transition law; the admitted family is A (stage-word/loop-readout), C (composition-first), D (Matrix64/Carnot product), plus v2's cyclic wrap as the contrast row. Apply the generating-set-sweep pattern (system_v6/sims/basin_generating_set_sweep_v0/) to CONVENTIONS: one joint-dynamics realization per row, same partition machinery for all.

## Read also
- system_v6/sims/basin_two_engine_joint_v2/ (sources + audit_verdict.md - reuse its 1024-state joint-object machinery and its anti-by-construction design; fix caveat G2 where feasible: Julia must independently recompute the per-row terminal counts via Graphs.jl, not consume the Python lattice payload)
- system_v6/receipts/attractor_basin_criterion_20260611.md (the basin contract, the 9 requirements, THE GUARD)
- system_v6/foundations/two_engine_readout_automaton_20260609.md + symbolic_layer_iching_taijitu_20260609.md (the B constraints' source: stage word vs loop readout; the paired word preserves two-loop stage structure)
- sim-wizard SKILL (TOOL_INTENT_MATRIX mandatory in build_card.md; envelope ONLY via scripts/build_three_engine_envelope.py)

## The sweep (binding design rules)
1. For each convention row (A, C, D, v2-cyclic-contrast): realize the per-engine fine dynamics (2 loops x 4 stages x 4 substages = 32 states/engine; joint = 1024) under that row's substage update law, derived from the QUOTED source lines in the mining receipt - cite the exact quote each law realizes in a per-row provenance field. Where a row's source underdetermines a detail, enumerate the minimal sub-variants rather than silently picking (cap: the few that the quotes admit; document each).
2. B CONSTRAINTS BIND EVERY ROW: both directed loop orders preserved (deductive Se->Ne->Ni->Si on one loop, inductive Se->Si->Ni->Ne on the other); order tested separately from labels (an order-shuffled control per row MUST change the terminal structure - if it does not, the row is flagged order-blind and excluded as source-invalid).
3. Same partition machinery for all rows: SCCs, terminal closed classes w/ absent-exit proofs, may/must split, natural quotient projections (engine/loop/stage/substage factor maps as dynamical quotients w/ equivariance checks), Morse ordering. 64 must be DISCOVERED as a terminal/SCC count at some primary level - never imposed (the v0 lesson: no state-identity or marginal-intersection 64; the coarse 8x8 row stays a fenced control).
4. Per-row verdict field: primary_64_level found true/false + the actual class lattice. Sweep verdict: which rows (if any) realize 64, which realize other counts, cross-row comparison under an order-blind label-free signature (the k=5 lesson: no signature component may recover the ordering).
5. Controls per row: order-shuffled (must flip), label-permutation (must NOT change counts - label-freeness), dissipative-merge contrast, v1-replication fence (accepted_as_primary_evidence=false).

## Engineering contract
Three engines (Julia reference recomputing per-row terminal counts independently via Graphs.jl + Z3.jl w/ package_observables; JAX workhorse; PyTorch first-class), SMT binds COMPUTED counts (negated per-row count identity UNSAT + a flipped control SAT), TOOL_INTENT_MATRIX in build_card.md, envelope via scripts/build_three_engine_envelope.py, validate --require-pytorch --strict-source-backed ok:true, classification scratch_diagnostic, promotion_allowed=false, positive+negative+boundary sections. Vocabulary: terminal classes earned w/ absent-exit proofs; every claim convention-row-relative (a=a iff a~b). End by listing validator commands + ok statuses.

## Builder Operational Additions

Object: `basin_two_engine_joint_v3_convention_sweep`, a 1024-state two-engine convention sweep over admitted substage-transition convention rows.

Claim under test: the re-registered convention-relative `64 = 2 engines x 2 loops x 4 stages x 4 substages` prediction is tested as a discovered terminal/SCC class count under each row's declared convention, never as a state address, label product, marginal intersection, or control artifact.

Controls:
- positive: convention rows compute terminal closed classes, absent-exit proofs, may/must rows, quotient rows, and Morse ordering from the 1024-state transition object;
- negative: order-shuffled controls flag order-blind rows as `source_valid=false`; v1 replication is fenced as `accepted_as_primary_evidence=false`;
- boundary: dissipative merge may produce 64 but remains control-only; v2 cyclic wrap is contrast-only and not owner-source admitted.

PIN:
```json
{
  "state_family": "L_engine32 x R_engine32",
  "per_engine_factorization": "2 loops x 4 stages x 4 substages",
  "joint_state_count": 1024,
  "directed_orders": {
    "deductive": ["Se", "Ne", "Ni", "Si"],
    "inductive": ["Se", "Si", "Ni", "Ne"]
  },
  "placements": {
    "L": "Type1: outer/base deductive, inner/fiber inductive",
    "R": "Type2: outer/base inductive, inner/fiber deductive"
  },
  "primary_count_observable": "terminal_class_count over row-labelled transition SCCs",
  "proof_observable": "per-row computed terminal-count identity: negated mismatch UNSAT; flipped expected count SAT",
  "ceiling": "scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false"
}
```

Files to create:
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/build_card.md`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/basin_two_engine_joint_v3_convention_sweep_common.py`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/basin_two_engine_joint_v3_convention_sweep_jax.py`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/basin_two_engine_joint_v3_convention_sweep_pytorch.py`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/basin_two_engine_joint_v3_convention_sweep_julia.jl`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/basin_two_engine_joint_v3_convention_sweep_envelope.py`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/validate_basin_two_engine_joint_v3_convention_sweep.py`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_jax_results.json`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_pytorch_results.json`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_julia_results.json`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_envelope_results.json`
- `system_v6/sims/basin_two_engine_joint_v3_convention_sweep/results/basin_two_engine_joint_v3_convention_sweep_validator_results.json`

Ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Envelope builder: `scripts/build_three_engine_envelope.py` only.

TOOL_INTENT_MATRIX:
```json
{
  "claim_classes": [
    "convention_relative_terminal_class_count",
    "finite_transition_partition",
    "order_shuffled_negative_control",
    "computed_count_identity_smt"
  ],
  "engine_tool_intent": {
    "julia": {
      "Graphs": "independent Graphs.SimpleDiGraph SCC and terminal-count recomputation for every convention row",
      "Z3": "Julia-side computed terminal-count identity UNSAT with flipped expected-count SAT"
    },
    "jax": {
      "networkx": "workhorse SCC, terminal class, may/must, quotient, and Morse partition machinery",
      "sympy": "exact integer checksum for label-free terminal-count signatures",
      "z3": "computed terminal-count identity UNSAT with flipped expected-count SAT",
      "cvc5": "independent computed terminal-count identity UNSAT with flipped expected-count SAT"
    },
    "pytorch": {
      "torch.func": "batched torch transition materialization for convention-row graph tensors",
      "torch_geometric": "edge_index graph carrier for convention-row transition relations",
      "sympy": "exact integer checksum for torch-side terminal-count signatures",
      "z3": "torch-side computed terminal-count identity UNSAT with flipped expected-count SAT",
      "cvc5": "independent torch-side computed terminal-count identity UNSAT with flipped expected-count SAT"
    }
  }
}
```

Builder output only. Do not create `audit_verdict.md`. Do not git add or commit.
