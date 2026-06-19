# BUILD CARD: basin_two_engine_joint_v2 - discoverable 1024-state two-engine basin test

Claim under test: the owner prediction `64 = 2 engines x 2 loops x 4 stages x 4 substages` must be discovered from a joint dynamics larger than 64, not constructed by intersecting marginal labels.

Parent lineage:
- v1 failure analysis: `system_v6/sims/basin_two_engine_joint_v0/audit_verdict.md`
- owner prediction / registration: `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md`, amendment `0bed51ac2`
- basin contract: `system_v6/receipts/attractor_basin_criterion_20260611.md`, commit `000f48e71`
- two-engine readout automaton: `system_v6/foundations/two_engine_readout_automaton_20260609.md`, commit `dd9ec4999`
- scaffold: `system_v6/foundations/working_math_scaffold_20260609.md`, sections 14-15 and Axis-3 loop placement notes

Ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

State object:
- one engine fine state is `2 loops x 4 stages x 4 substages = 32`;
- the joint state space is `32 x 32 = 1024`;
- L uses Type1 placement: base/outer deductive, fiber/inner inductive;
- R uses Type2 placement: base/outer inductive, fiber/inner deductive.

Substage convention:
- committed sources pin two loops and four stages, but do not pin a four-substage transition law for this packet;
- v2 pins a declared convention: substage increments cyclically; on wrap, stage advances; on stage wrap, loop advances;
- this convention is claim-scoped and remains below admission.

Rows:
- source-backed full-tick interleavings: sync, L-only, R-only, async L/R union, all-interleavings union;
- conditioned/restricted dynamical rows: sync loop advance, sync stage progression, sync substage cycling, sync coordinate generators, async coordinate generators;
- every row computes SCCs, terminal closed classes, absent-exit proofs, may/must rows, and Morse edges.

Discovery rule:
- the primary result is the computed class lattice over the 1024-state object and its natural quotient rows;
- `64` counts only if it appears as a terminal/SCC class count under a row, not as a state count or partition intersection;
- if no primary 64 level appears, report the actual lattice.

Controls:
- label permutation reruns the graph/signature computation;
- decode test reports what class signatures recover and what remains only a dynamical invariant;
- root-off changes the engine loop modulus and must change the lattice;
- v1 replication reproduces the coarse 8x8 intersection baseline and labels it `by_construction_baseline`;
- dissipative merge control adds an explicit substage reset operation and must produce fewer than 1024 terminal classes.

Product test:
- if a primary 64 class level appears, factor projections must be well-defined on classes, equivariant, and reconstruct exactly;
- if no primary 64 appears, the packet reports the actual factor structure;
- if a control produces 64, it is labeled as control evidence and not as the owner prediction.

Tools:
- Python/JAX leg: networkx + sympy + z3 + cvc5 over the 1024-state graph;
- Julia leg: real Graphs.jl + Z3.jl;
- PyTorch leg: torch.func + torch_geometric + sympy + z3 + cvc5;
- envelope via `scripts/build_three_engine_envelope.py`;
- validator must pass `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed`.

Builder output only. Do not create `audit_verdict.md`. Do not git add or commit.
