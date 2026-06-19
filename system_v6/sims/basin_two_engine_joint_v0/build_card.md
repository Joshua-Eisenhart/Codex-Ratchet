# BUILD CARD: basin_two_engine_joint_v0 - two-engine joint basin hierarchy

Claim under test: the L-engine x R-engine joint stage-configuration dynamics earns, or fails to earn, the pre-registered 64 subsubbasin prediction under an order-blind, label-free partition signature.

Pre-registration:
- `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md`
- commit hints: `d5914f67f`, amendment `0bed51ac2`

Committed parents:
- basin contract and may/must vocabulary: `000f48e71`, `system_v6/receipts/attractor_basin_criterion_20260611.md`
- first basin partition machinery: `631f1c3db`, `system_v6/sims/basin_rc_transition_graph_v0/`
- two-engine readout automaton: `dd9ec4999`, `system_v6/foundations/two_engine_readout_automaton_20260609.md`
- matrix64 anchor: `system_v6/sims/terrain_operator_precedence_64_matrix/`
- mirror-law warning: family-local only; no universal L/R mirror assumption

Ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Primary object:
- finite state space: `S = L_stage_8 x R_stage_8`, 64 cells
- L word: deductive then inductive stage word from the committed automaton
- R word: inductive then deductive stage word from the committed automaton
- interleaving semantics pinned as separate rows:
  - synchronous: advance both engines in one paired transition
  - asynchronous: advance L-only or R-only as independent generator-labelled moves
  - both: use synchronous plus asynchronous generators

Hierarchy deliverable:
- basins: terminal closed communicating classes under the selected joint generator set
- subbasins: restricted/conditioned terminal classes under synchronous, L-only, and R-only rows
- subsubbasins: intersection refinement of the earned marginal restricted partitions
- may/must split at every level
- terminal classes with absent-exit proofs
- Morse ordering for every graph row

Signature discipline:
- signature is an equivalence-relation refinement over computed partitions, not stage names
- no signature component may include stage labels, stage indices, word positions, matrix64 cell ids, or original cell ids
- label permutation control must preserve counts and class-size multisets
- decode test must show stage order is not recoverable from signature components; only arbitrary partition-class identities remain

Adjudication:
- compare computed counts at basin, subbasin, and subsubbasin levels against the pre-registered 64
- if 64 appears, identify whether the computed product realizes 8x8 joint stages, matrix64, or 16x4 by computed correspondence
- if 64 does not appear, report the honest count and excluded candidates

Required rows:
- L/R chirality asymmetry: compare L-only and R-only marginal partitions without assuming a universal mirror
- N01/noncommutation: compare L-then-R and R-then-L interleaving effects on state partition and trace/readout order
- secondary bounded carrier-grid product row: small sampled product only, no dense carriers

Controls:
- single-engine marginal anchors where comparable
- label-permutation control
- similarity-cluster contrast
- root-off contrast
- decode test
- erased-signature flip for z3/cvc5 class-count identity

Tools:
- Python/JAX-labeled leg: networkx + z3 + cvc5 over the 64-cell joint graph
- Julia leg: real Graphs.jl + Z3.jl
- PyTorch leg: tensor/torch_geometric graph support
- envelope via `scripts/build_three_engine_envelope.py`
- validator must pass `scripts/validate_three_engine_sim_result.py --require-source-backed`

Builder output only. Do not create `audit_verdict.md`. Do not git add or commit.
