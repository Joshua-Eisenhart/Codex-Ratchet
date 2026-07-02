# Informal Axis 7-12 And Game-Theory Exploration Audit + Prompt

Date: 2026-05-25
Lane: `system_v5/grok_sim/` only.
Status: sidequest control artifact. This is not a canonical sim, not a
promotion artifact, and not a claim-bearing result.

## 1. Read-Only Audit Findings

This audit read the repo authority docs and the current `grok_sim` lane. The
informal lane is useful, but it is not clean enough to let a fresh agent copy old
schemas blindly.

### 1.1 Correct lane path

The repo path is singular:

```text
system_v5/grok_sim/
```

Do not write to `system_v5/ops/formal_scouts/`, `system_v5/docs/`, or any
formal result/index surface from the informal run.

### 1.2 Boundary guard is red at repo level

Fresh run:

```text
python3 scripts/grok_sim_boundary_guard.py
```

returned 80 current violations in `system_v5/grok_sim/`. The main patterns are:

- old informal result JSONs using formal-lane vocabulary;
- old sources that can regenerate formal-lane result classifications;
- NumPy marked as load-bearing in old Axis0/result payloads;
- missing or malformed sidequest claim ceilings in some later result JSONs;
- negated proof-language phrases inside JSON strings that still trip the guard.

This means the next informal run must treat the guard output as a red baseline,
not as proof that the whole lane is unusable. The stricter rule for the fresh
run is:

```text
run guard before writing
run guard after writing
no new violation path may be introduced by files touched in the new run
```

If a new file appears in the guard violations, repair the new file before moving
on.

### 1.3 Substrate reset still controls the informal lane

`RESET_2026_05_24_numpy_substrate_failure.md` and
`GROK_SIM_SUBSTRATE_VIOLATION_AUDIT_20260524.md` remain the local reset
boundary:

- `iter_292` through `iter_304` are hard-blocked as question generators only.
- `iter_287` through `iter_289` are adapter/control only.
- `iter_283` through `iter_286`, `iter_290`, and `iter_291` are source
  baselines only, with invalid result vocabulary.
- `iter_306a*` through `iter_311` are better candidate sources but still not
  formal-lane support.
- `iter_312` through `iter_321` are the newest useful informal chain, but they
  are exact-dense or smoke-scale and remain sidequest-local.

The lesson is not "stop exploring." The lesson is "do not let informal results
pretend to be admission receipts."

### 1.4 Axis 7-12 and game theory are not yet a real informal program

Current coverage is thin:

- `iter_156_alt_dof_exploration_beyond_seven_axes.py` only sketches candidate
  extra degrees of freedom, including engine count as multi-engine territory.
- `HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md` records
  that axes 0-6 did not uniquely decompose all stage configurations in an older
  read, creating pressure for Axis 7+ or axis refinement.
- Existing FEP/game material is mostly sampled wiki-predicate work, not an
  engine-population game-theory program.
- The new `system_levels_20260525` docs define only a candidate correlation
  space: classical game theory -> QIT-FEP lift -> population/world simulation
  -> possible axes 7-12 shadows.

So the next informal lane can explore axes 7-12 and game theory, but it must
name them as shadow observables or candidate collective variables, not axes.

## 2. Prompt For Fresh Informal Claude

Copy the full block below into the fresh informal Claude/Codex/Grok sidequest
thread.

```text
You are running the informal Codex Ratchet sidequest lane, not the formal lane.

Your job is exploratory: make things work, try strange forward and backward
searches, and produce useful failures that can later fuel formal sims. You are
allowed to skip ahead, start from collective/game-theory hypotheses, and work
backward toward missing foundations. You are not allowed to present the result
as formal support or write outside the informal lane.

WRITE SCOPE
- You may write only under:
  system_v5/grok_sim/
- Prefer:
  system_v5/grok_sim/iters/
  system_v5/grok_sim/results/
  system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_*.md
- Do not write to:
  system_v5/ops/formal_scouts/
  system_v5/docs/
  system_v5/evidence/
  formal indexes, ledgers, classifiers, or queue files

READ FIRST
1. AGENTS.md
2. CODEX.md
3. system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
4. system_v5/docs/LLM_CONTROLLER_CONTRACT.md
5. system_v5/docs/LEGO_SIM_CONTRACT.md
6. system_v5/grok_sim/README.md
7. system_v5/grok_sim/RESET_2026_05_24_numpy_substrate_failure.md
8. system_v5/grok_sim/GROK_SIM_SUBSTRATE_VIOLATION_AUDIT_20260524.md
9. system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_321_chain.md
10. system_v5/docs/system_levels_20260525/07_IGT_QIT_FEP_STRATEGY_MATH.md
11. system_v5/docs/system_levels_20260525/08_STRATEGY_LOOP_ENGINE_SEMISYMMETRY_MAP.md
12. system_v5/docs/system_levels_20260525/09_CLASSICAL_GAME_QIT_FEP_CORRELATION_AXES_7_12.md

CLAIM CEILING
Every result JSON you write must include:

claim_ceiling: "side_quest_only"
promotion_allowed: false
evidence_allowed: false
evidence_allowed_for_formal: false
formal_reproduction_target: false
blocked_formal_consumers: ["manifold", "axis", "flux", "Axis0", "bridge", "physics", "canon"]

Do not use formal-lane classification vocabulary in grok_sim result JSONs.
Do not mark NumPy as load-bearing for nonclassical claims.
Do not use Bloch/Pauli/Cartesian fixtures as root manifold objects. They are
allowed only as adapter charts, baselines, or controls.

BOUNDARY GUARD
Before writing anything, run:

python3 scripts/grok_sim_boundary_guard.py

It is expected to be red because of old files. Save the count/path list in your
notes. After writing new files, run it again. Your success condition is:

no new violation path is one of the files you created or edited

If your new file appears in guard output, fix your file before continuing.

FOUNDATION CONTRACT FOR EVERY ITER
Every iter may be playful, but it must declare the finite object it is playing
with. Include these fields in the result JSON:

sim_id
claim_ceiling
question
mode: one of ["forward_exploration", "reverse_derivation", "baseline", "control", "tool_fit"]
F01_finite_sets
N01_order_or_noncommutation_witness
finite_map
domain
codomain_or_output
carrier
spinor_or_density_status
peps3d_anchor_status
quaternion_status
controls
negative_conditions
tool_manifest
tool_integration_depth
observables
pass_fail
failed_predictions
dependency_gaps
blocked_formal_consumers

If an iter cannot supply a finite map/domain/codomain, write a blocked-reason
JSON instead of a sim result.

EXPLORATION OBJECTIVE
Build an informal program for:

classical game theory math
-> QIT-FEP lift
-> IGT strategy-token loop comparison
-> multi-engine population/world simulation
-> candidate shadow observables for axes 7-12
-> reverse dependency report back to axes 1-6, spinor carrier, and PEPS3D gates

Axes 7-12 are not defined. Call them A7_shadow through A12_shadow or
collective shadow variables. They are probes, not axes.

GAME THEORY SEED MATH
Start from a finite classical game:

players i in {1, ..., N}
actions A_i
joint action a = (a_1, ..., a_N)
payoff u_i(a)
mixed strategy p_i
history h = (a^0, ..., a^T)
interaction graph or hypergraph G

Classical observables:

E[u_i] = sum_a p(a) u_i(a)
Cov(u_i, u_j)
Pareto gap
Nash/exploitability gap
coalition value V(C) = E[sum_{i in C} u_i]
local-loss/global-gain: Delta u_i < 0 and Delta V(C) > 0
strategy-response Jacobian
replicator or mirror update

Then lift to finite QIT-FEP objects:

H_i = finite strategy / observation / memory carrier
rho_i = local engine state
rho_G = joint population state
E_i = finite effect/probe family
U_i = sum_a u_i(a) |a><a|
Payoff_i(rho_G) = Tr(U_i rho_G)
Cov_Q(i,j) = Tr((U_i tensor U_j) rho_G) - Tr(U_i rho_G) Tr(U_j rho_G)
I_Q(i:j) = S(rho_i) + S(rho_j) - S(rho_ij)
TotalCorr(C) = sum_i S(rho_i) - S(rho_C)

Candidate path objective:

G_i(path) =
  E_h[Tr(U_i rho_h)]
  - beta_i F_Q(rho_h)
  + lambda_i I_Q(i:C_h)
  + mu_i Z_future(h)
  + nu_i Credibility_i(h)
  - cost_i(h)

Preserve this human hypothesis as a testable strategy class:

local payoff loss can be strategically common when
Delta Payoff_i < 0 but Delta G_i > 0 and Delta V(C) > 0.

This covers "lose in win-lose", victim/compassion/coalition organizing, and
cooperative large-scale coordination as a mathematical pattern. Do not make it
a political theorem. Treat it as one strategy family to test against controls.

IGT STRATEGY TOKEN MATH
Use the 16 ordered strategy channels from the semisymmetry map. For each
topology/operator pair, Axis6 order is the real distinction:

M_terrain_first(rho) = Operator(Terrain(rho))
M_operator_first(rho) = Terrain(Operator(rho))
Delta_A6 = M_terrain_first(rho) - M_operator_first(rho)

Axis5 is the strategy-family distinction:

T strategy = dephasing / projection / pinching
F strategy = coherent rotation / unitary alignment

Interpret "cold" and "hot" only as strategy-language:

T/cold = selection, partition, competition, boundary, measurement-like commitment
F/hot = coherence, coupling, coordination, coalition, compassion/alignment

Do not turn this into literal thermodynamics unless an iter supplies a thermal
model and controls.

Axis3 outer/inner must be tracked separately from Axis6:

outer/public = visible collective signal or major loop readout
inner/private = internal/fiber/private readout or minor loop readout

If an Axis6 swap also flips outer/inner in the chart, report that as chart
correlation, not as a theorem.

COLLECTIVE SHADOW VARIABLES
Use these as placeholders only:

A7_shadow: coalition polarity / payoff-sign covariance / group boundary cut
A8_shadow: collective quadrant routing / interaction graph cut / hypergraph incidence
A9_shadow: private-vs-public signal split / observation instrument / public projection
A10_shadow: coalition loop order / causal memory cycle / population schedule
A11_shadow: collective T-vs-F mixture / competition-cooperation coherence readout
A12_shadow: collective precedence / policy-before-evidence vs evidence-before-policy order witness

For every shadow variable, report:

what local axis it mirrors
finite map
domain
codomain
observable
control that should erase it
dependency gap that blocks promotion

MAX TOOL USAGE RULE
Use every relevant tool as a way to change or check the result, not as imports.
Each result must include a tool_manifest entry for every attempted or skipped
tool:

PyTorch/autograd:
  load-bearing for rho/channel/objective computation when QIT-FEP is active
z3:
  use for finite constraint feasibility, counterexamples, or impossible strategy patterns
cvc5:
  cross-check z3 or synthesize minimal finite payoff/strategy examples
sympy:
  use for symbolic payoff, commutator, entropy/objective, or channel-order formulas
Clifford:
  use if spinor/rotor/geometric-product claims are made
geomstats:
  use if metric/geodesic/manifold claims are made
e3nn:
  use if equivariance or rotation-symmetry-native computation is claimed
rustworkx:
  use for causal/order/dependency/game graphs
XGI:
  use for coalition hypergraphs and multi-agent hyperedges
TopoNetX:
  use for cell-complex versions of collective/public/private structure
GUDHI:
  use for filtration or persistent-homology readouts over the game/event graph
PyG:
  use for graph dynamics if installed and relevant

If a tool is not installed or cannot change the current iter's result, mark:

role: "blocked" or "not_relevant"
reason: concrete reason
impact: what result would change if the tool were available/relevant

Do not claim max tool usage if you only imported tools. The tool must create a
check, a counterexample, a certificate, a graph/topology observable, or a failed
attempt with a logged blocker.

ITERATION LADDER
Run small, separate iters. Do not create one giant context-window file.

Iter 322 candidate:
  classical game baseline
  2-4 agents
  payoff tables for win-win, win-lose, lose-win, lose-lose
  explicit local-loss/global-gain cases
  z3/cvc5 search for small payoff examples if possible

Iter 323 candidate:
  QIT-FEP payoff lift
  diagonal payoff observable U_i
  finite rho_G over small action Hilbert space
  compare classical payoff, QIT covariance, total correlation, and G_i(path)
  include a classical-only control

Iter 324 candidate:
  IGT ordered strategy channel comparison
  choose 2-4 tokens such as NeTi vs TiNe and FeSi vs SiFe
  compute Delta_A6 order witness
  compare T/cold and F/hot strategy families via coherence, payoff, information, and path objective
  include order-erased and label-erased controls

Iter 325 candidate:
  collective shadow variable map A7_shadow through A12_shadow
  use event graph V = {(engine_id, time, stage, slot)}
  use rustworkx/XGI/TopoNetX/GUDHI where available
  each shadow gets finite map/domain/codomain/control/dependency gap

Iter 326 candidate:
  reverse derivation report
  start from strongest observed collective/game pattern
  work backward to the missing lower receipts
  emit dependency gaps, formal reproduction targets, and killed hypotheses
  do not write a formal handoff unless the target is narrow and reproducible

CRASH AND CONTEXT CONTROL
- One iter = one question.
- Keep each Python file under roughly 500 lines unless there is a concrete reason.
- Keep each result JSON small but complete.
- Every 3-5 iters, write a short chain handoff in `system_v5/grok_sim/`.
- If context gets confused, stop and write a reset note instead of pushing forward.

SUCCESS CONDITIONS
The informal run succeeds if it gives the formal lane useful fuel:

- a small reproducible payoff/QIT-FEP pattern;
- a falsified strategy mapping;
- a tool-specific blocker;
- a clean finite map for a shadow variable;
- a reverse-dependency gap list.

It does not need to prove axes 7-12. It must not claim axes 7-12 are defined.
```

## 3. Controller Recommendation

Let the informal sim skip ahead, but force it to leave behind narrow artifacts:

```text
small iter
small result JSON
sidequest-only claim ceiling
guard-diff check
finite map
tool manifest with real use or explicit blocker
dependency gap list
```

The best near-term direction is not another Axis0 or flux run. The strongest
new fuel is a finite population/game-world baseline that tests whether
local-loss/global-gain, T/F strategy family, and Axis6 order witnesses produce
different QIT-FEP readouts. If that produces a real pattern, the reverse report
can tell the formal lane which lower carrier/PEPS3D/spinor dependency has to be
earned before any collective axis language becomes admissible.
