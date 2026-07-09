# QIT Dual Ratchet Engine Teeth Audit 2026-07-07

This audit records a fresh local check of the current QIT / dual-ratchet / object-perception engine surfaces in the live Codex-Ratchet repo.

## Scope

Live repo read gate used:

- `/Users/joshuaeisenhart/Codex-Ratchet/AGENTS.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/CODEX.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/LEGO_SIM_CONTRACT.md`

Reference-only Desktop material was used for context. The live repo authority for this receipt is `/Users/joshuaeisenhart/Codex-Ratchet`.

## Verdict

The engines have real teeth at the finite schedule, order-sensitivity, cross-substrate parity, and bounded loop levels. They do not yet prove the full object-perception engine, full Type-1/Type-2 64-stage QIT closure, Axis0 unlock, production ontology engine, or Lev mesh runtime integration.

Strong current evidence:

- The 16 chart-locked macro-stages and 4 substages/operators per macro-stage are represented by the Engine 64 schedule atlas, with two engine sheets producing 64 ordered microsteps.
- Order matters. The fresh order-sensitive schedule diagnostic returned 64 ordered states while the order-blind control collapsed to 11 buckets.
- The 16 oracle-contract stages are numerically distinct and order-sensitive across current 1q/3q JAX/Torch/Julia validators.
- The v6 full 64-stage packet reran across base, JAX, Julia, envelope, and validator after repairing envelope hash drift.
- The `qit_dual_engine_live_v0` loop reran fresh for 300 ticks across NumPy, JAX, Torch, and Julia, with exact action parity and measurable D/C sheet divergence.
- Formal scout probes show perception-like finite work: source-aligned engines run and differ, engine trajectories carry class signal, dynamics beat static controls, constraint placement is discriminable, holodeck replay has bounded survival, and spinor-memory adapter seeds survive controls.

Blocked or weak current evidence:

- `qit_dual_engine_live_v0` is explicitly not a full Type-1/Type-2 engine at full operator plus geometry depth. It is a sheet-restricted belief/action loop.
- The one-object/many-projection registry is a mapper and validator surface, not a proved object factory. Its own deep audit fences the earlier central claim as partly circular/decorative.
- Current "engine personalities" are engine-mode grammars, stage strategies, sheet differences, and trajectory behaviors. They are not subjective personalities or general cognition.
- The current entropy/surprise evidence is a live-loop profile, not an admitted global entropy-gradient theorem.
- Axis0 / FEP / bridge / physics / full Lev object mesh claims remain blocked downstream consumers unless a later packet satisfies the nonclassical foundation gate.

## Fresh Evidence

### 64 Schedule

Command:

```sh
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/constraint_core/sims_and_scripts/engine_64_schedule_sim.py
```

Result:

```json
{
  "n_orderblind": 11,
  "n_ordersensitive": 64,
  "n_with_order_gap": 64,
  "mean_order_gap": 0.5436866002450209
}
```

Interpretation: the 64 slots are not just labels in this diagnostic. Removing order collapses the state space.

### 64-Stage Full Run Packet

Fresh sequence:

```sh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_jax.py
/opt/homebrew/bin/julia --startup-file=no system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/engine_64_stage_full_run_v0/results/engine_64_stage_full_run_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/validate_engine_64_stage_full_run_v0.py
```

Result: all final validators green after rerunning the envelope to clear stale base-result hash drift.

Claim ceiling from the result remains scratch-diagnostic: realization-relative schedule trajectory only; no source admission, no match-lane claim, no basin/subbasin claim.

### 16-Stage Engine Contract

Fresh sequence under `system_v7/constraint_core/engines`:

```sh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 oracle_targets.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 oracle_targets_3q.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 jax_engine.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 torch_engine.py
/opt/homebrew/bin/julia --startup-file=no julia_engine.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 jax_engine_3q.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 torch_engine_3q.py
/opt/homebrew/bin/julia --startup-file=no julia_engine_3q.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 validate_engines.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 validate_engines_3q.py
```

Key outputs:

- 1q oracle wrote 16 stages with minimum pairwise distance `0.0276`; all order gaps were nonzero.
- 3q oracle wrote 16 stages in 63-dimensional Pauli space with minimum pairwise distance `0.1742`; all order gaps were nonzero and genuinely 3q.
- JAX, Torch, and Julia all passed 1q and 3q validation.
- 3q worst pvec deviation was `9.89e-13`.

Interpretation: this is the strongest current evidence that the 16 oracle-contract stages are numerically distinct and order-sensitive, not a renamed loop over one behavior. It is not a semantic proof that every stage has a final admitted ontology.

### Live Dual Engine Loop

Command:

```sh
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_dual_engine_live_v0/qit_dual_engine_live_v0.py --fresh
```

Key outputs:

- `all_parity_passed: true`
- `classification: scratch_diagnostic`
- `promotion_allowed: false`
- D and C exact action match counts: `1800` each
- Global stage match counts: `1800` each
- Maximum numeric absolute deviation across leaves: `3.984368390774762e-12`
- D/C sheet final and maximum gap trace distance: `0.6367990145139109`
- Surprise profile final: `4.345428045862478`; maximum: `10.283387018266158`
- D memory fidelity at read ticks: `1.0`; C memory fidelity at tick 299: `0.14644660940672632`
- NumPy, JAX, Torch, and Julia all ran in the fresh substrate metrics.

Interpretation: this is real loop work with cross-substrate agreement and sheet divergence. It is not full engine closure.

### Constraint Core Harness

Command:

```sh
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 run_all.py
```

Location:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/run_all_report.json`

Result:

- 73 pass
- 0 fail
- 0 skip

Included green rows cover sixteen-stage schedules, Type-1 IGT, QIT-FEP ratchet, active-inference planning, agent-loop, quantum Hopfield memory with Torch, and cross-substrate 1q/3q engine validation.

### Object And Perception Surfaces

Fresh object/perception-relevant checks:

- `system_v7/sims/one_object_many_projection_registry_v0/validate_registry.py`
- `system_v5/ops/formal_scouts/sim_source_aligned_qit_engine_runtime_probe.py`
- `system_v5/ops/formal_scouts/results/source_aligned_qit_engine_runtime_probe_results.json`
- `system_v5/ops/formal_scouts/sim_qit_engines_perform_classification_task_with_trainable_readout_probe.py`
- `system_v5/ops/formal_scouts/results/qit_engines_perform_classification_task_with_trainable_readout_probe_results.json`
- `system_v5/ops/formal_scouts/sim_qit_engine_dynamics_required_work_discrimination_probe.py`
- `system_v5/ops/formal_scouts/results/qit_engine_dynamics_required_work_discrimination_probe_results.json`
- `system_v5/ops/formal_scouts/sim_constraint_manifold_placement_neural_behavior_discrimination_probe.py`
- `system_v5/ops/formal_scouts/results/constraint_manifold_placement_neural_behavior_discrimination_probe_results.json`
- `system_v5/ops/formal_scouts/sim_holodeck_qit_engine_replay_probe.py`
- `system_v5/ops/formal_scouts/results/holodeck_qit_engine_replay_probe_results.json`
- `system_v5/ops/formal_scouts/sim_holodeck_qit_spinor_memory_adapter_seed_probe.py`
- `system_v5/ops/formal_scouts/results/holodeck_qit_spinor_memory_adapter_seed_probe_results.json`

Current object verdict:

- The registry has 10 rows, one root object id, and well-formed projections.
- The source-aligned runtime probe says the engines run, are distinct, and converge under the tested formal-scout conditions.
- The trainable readout probe shows engine features beat random and shuffled controls.
- The dynamics-required probe shows full trajectories beat initial/static/manifold-disabled controls.
- The placement discrimination probe shows nominal trajectory placement beats flat/loop/sheet/stage controls.
- The holodeck and spinor-memory adapter probes show bounded replay/recall survival.

Claim ceiling: perception-like formal scouts and adapter seeds exist. A production object factory, AI perception engine, ontology writer, MMM driver, or Lev mesh object engine is not admitted yet.

## Stage And Engine Identity

Current evidence supports this structure:

- 16 macro-stages are numerically distinct and order-sensitive under the current oracle/validator contract.
- Each macro-stage has 4 operator/substage moves in the 64 schedule atlas.
- Two engine sheets produce 32 ordered microsteps each.
- Total ordered microsteps are 64.

The subtle part: the repo has both 16 chart-locked macro-stages and 64 ordered microsteps. Do not collapse them into "64 independent macro-stages" or "16 labels repeated four times." The current strongest interpretation is:

```text
2 engine sheets x 8 macro visits per sheet x 4 operator/substage moves = 64 ordered microsteps
```

## Intelligence / Personality Ceiling

It is admissible to describe unique engine-mode intelligence in a bounded sense:

- D and C sheets diverge under the live loop.
- Ordered stage trajectories carry classification and placement signal.
- Some probes require dynamics, not just static state.
- Different stage/sheet/topology/context placements act like distinct computational moods or strategies.

It is not admissible yet to claim:

- subjective personality;
- general cognition;
- autonomous scientific discovery;
- production perception;
- ontology creation without a gate;
- full Type-1 / Type-2 method closure.

## Bidirectional Science Method Ceiling

The current repo has pieces of a bidirectional scientific method:

- hypothesis / candidate state;
- finite measurement;
- action or update;
- negative controls;
- cross-substrate replay;
- receipt classification;
- blocked downstream consumers.

The missing full proof is per-engine method closure:

```text
Engine Type 1:
candidate -> measurement -> prediction -> action/update -> falsifier -> receipt -> recursive model change

Engine Type 2:
candidate -> measurement -> counter-projection -> action/update -> falsifier -> receipt -> recursive model change
```

Both must be run on the same object family, with held-out tests, order-erased controls, density-only controls, shuffled context controls, and a clear comparison of what each engine can do that the other cannot.

## Lev / Mesh / MMM Implication

The current safe bridge to Leviathan is not "Codex-Ratchet mutates Lev state." It is:

```text
candidate object
-> measurement packet
-> gate policy
-> decision
-> receipt
-> Lev imports as claim/evidence
-> local verifier quorum
-> mesh-visible object projection
```

For MMMs and ontologies, the useful claim is narrow but important:

- an MMM can be treated as a scoped language/object projection surface;
- multiple projections can point at one candidate root object;
- failed projections need anti-hashes/graveyard receipts;
- cross-node convergence can become a gate policy;
- agents should import remote graph data as claims/evidence, not as direct state mutation.

This is directly useful for blue-collar SME cases once the object gate exists: work orders, assets, crews, job sites, parts, incidents, contracts, and policies can be unified as projected object structures across local vocabularies.

## 2026-07-07 Update: 64-Live V1 Exists

The required `qit_full_type1_type2_64_live_v1` packet now exists under:

```text
system_v7/sims/qit_full_type1_type2_64_live_v1/
```

It is still a scratch diagnostic, but it gives the first narrow object-formation tooth:

- 64 ordered microsteps over the 16 macro-stage atlas.
- 32 Type-1 slots and 32 Type-2 slots.
- Four finite loop-object cards.
- Ordered object recovery succeeds.
- Static/bag-erased controls collapse object identity.
- Julia/JAX/PyTorch agree on survivor object count.
- PyTorch has a bounded learnable readout role.

## 2026-07-07 Update: Projection Battery V0

The next packet now exists under:

```text
system_v7/sims/qit_projection_battery_v0/
```

This packet consumes the v1 finite carrier and asks whether multiple partial
MMM-style projections can converge to the same underlying four object cards.
It intentionally excludes direct `loop` and `engine_type` fields because those
would trivially identify the objects and launder the result.

Fresh measured result:

- nominal mean held-out projection accuracy: `0.9`;
- bag-erased control mean: `0.25`;
- view-erased control mean: `0.25`;
- Julia/JAX/PyTorch object-count divergence: `0.0`;
- Julia/JAX/PyTorch view-count divergence: `0.0`;
- z3/cvc5 gate negation: `unsat`;
- erased controls: `sat` / chance;
- Lev host contract: evidence only, no graph mutation, no mesh projection.

Interpretation: this is a stronger object-factory scout than v1 because it
tests one-object/many-projection convergence instead of only ordered stream
recovery. It is still not live perception, not an ontology writer, not MMM
driver admission, not Axis0/FEP, and not Lev mesh runtime integration.

## 2026-07-07 Update: Bidirectional Science Type-1/Type-2 V0

The required bidirectional method packet now exists under:

```text
qit_bidirectional_science_type1_type2_v0
```

This packet consumes the projection battery and runs two finite science-method
orders over the same four projection object cards:

- Type-1: candidate -> measurement -> counter-projection -> update -> falsifier -> receipt.
- Type-2: measurement -> candidate -> counter-projection -> update -> falsifier -> receipt.

Fresh measured result:

- paired method trials: `40`;
- Type-1 nominal accuracy: `1.0`;
- Type-1 wrong-candidate accepted rate: `0.1`;
- Type-2 nominal accuracy: `0.9`;
- Type-2 bag-erased accuracy: `0.25`;
- Type-2 view-erased accuracy: `0.25`;
- unique-win table: `18` shared wins, `2` Type-1-only wins, `0` Type-2-only wins, `0` shared failures;
- Julia/JAX/PyTorch object-count divergence: `0.0`;
- Julia/JAX/PyTorch trial-count divergence: `0.0`;
- z3/cvc5/Julia Z3 method-gate negation: `unsat`;
- Lev host contract: evidence only, no graph mutation, no mesh projection.

Interpretation: Type-1 and Type-2 are now materially different finite methods,
not just names. Type-1 is sharper at confirming or rejecting a declared
candidate object. Type-2 can form a candidate from a measurement view, but it
remains ambiguous in two single-view planning cases.

This is still scratch evidence. It does not admit live perception, production
ontology writing, MMM driver authority, Axis0/FEP, or Lev mesh runtime
integration.

## Current Honest Status

```text
real engines running: yes, bounded
real 16-stage numerical distinction/order-sensitivity: yes, under current validators
real 64 ordered schedule: yes, under current scratch diagnostics
real projection-object scout: yes, bounded finite carrier only
real bidirectional Type-1/Type-2 science method: yes, bounded finite carrier only
real perception/object factory: not yet, but object-factory scouts now have measurable teeth
Lev receipt/evidence bridge path: implemented in Lev as an evidence-only consumer; not graph/runtime admitted
full QIT engine admission: blocked
Axis0/FEP/physics bridge admission: blocked
```

## 2026-07-07 Update: Lev Evidence-Only Consumer

Lev now has a narrow host-side QIT evidence importer:

```text
/Users/joshuaeisenhart/GitHub/lev/core/orchestration/src/proof/qit-evidence-consumer.ts
/Users/joshuaeisenhart/GitHub/lev/core/orchestration/src/handlers/qit-evidence.ts
```

Fresh Lev validation:

```sh
pnpm --dir /Users/joshuaeisenhart/GitHub/lev/core/orchestration exec vitest run src/proof/qit-evidence-consumer.test.ts src/handlers/qit-evidence.test.ts
pnpm --dir /Users/joshuaeisenhart/GitHub/lev/core/orchestration run typecheck
pnpm --dir /Users/joshuaeisenhart/GitHub/lev/core/orchestration test
```

Result: `9` focused tests passed, package typecheck passed, and the full
orchestration suite passed `850` tests across `55` files.

Live read-only smoke from Lev over the current QIT envelopes:

- `qit_full_type1_type2_64_live_v1`: `host_evidence_consumed`; evidence-only, graph mutation false.
- `qit_projection_battery_v0`: `host_evidence_consumed`; evidence-only, graph mutation false.
- `qit_bidirectional_science_type1_type2_v0`: `host_evidence_consumed`; evidence-only, graph mutation false.

This improves the CR -> Lev bridge from sketched to implemented as a host
receipt/evidence boundary. It still does not admit Lev graph mutation, Lev mesh
projection, ontology writing, MMM driver authority, or runtime object creation.

Follow-up refresh: the v1 envelope source now emits the explicit
`lev_host_consumer_contract` and `tool_intent` fields. Fresh v1 checks passed:

```sh
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_envelope.py
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/validate_qit_full_type1_type2_64_live_v1.py
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/qit_full_type1_type2_64_live_v1/results/qit_full_type1_type2_64_live_v1_envelope_results.json --require-pytorch --strict-source-backed --require-tool-intent
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1.py system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_envelope.py
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v7/sims/qit_full_type1_type2_64_live_v1/tests
```

Follow-up Lev quorum update: the Lev QIT batch consumer now implements an
explicit evidence-only k-of-n local verifier policy via `--quorum=N`. Default
batch behavior remains all-envelopes-required. Fresh Lev validation passed:

```sh
pnpm --dir /Users/joshuaeisenhart/GitHub/lev/core/orchestration exec vitest run src/proof/qit-evidence-consumer.test.ts src/handlers/qit-evidence.test.ts
pnpm --dir /Users/joshuaeisenhart/GitHub/lev/core/orchestration run typecheck
pnpm --dir /Users/joshuaeisenhart/GitHub/lev/core/orchestration test
```

Result: focused tests `11/11`, typecheck passed, full orchestration suite
`852` tests across `55` files passed.

Live temporary-batch smoke with symlinked current CR envelopes and
`--quorum=3` returned `host_evidence_quorum_met`, `3/3` distinct evidence
envelopes, `blocked=0`, `reviewed_failed=0`, and graph mutation false. This is
still only a local evidence quorum; it does not admit mesh-visible object
projection or runtime state mutation.
