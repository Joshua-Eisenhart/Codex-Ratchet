# Validity Audit Lane D - Tooling / Gates / Validators

Date: 2026-06-12
Repo: `/Users/joshuaeisenhart/Codex-Ratchet`
Lane: D, validators/gates/tooling layer
Claim ceiling: audit receipt only
Write scope: this receipt only

## Bottom Line First

`all_pass=true` usually means "this local contract accepted this artifact shape." It does not, by itself, mean current-source freshness, rich tool use, stage admission, axis/bridge/engine maturity, independent recomputation, or claim-name truth.

The strongest teeth are real but narrower than their names: `stage_gate.py` correctly blocks axis/bridge/engine claims while `active_stage=lego`; `validate_three_engine_sim_result.py --strict-source-backed` catches thin rich-tool claims; `verify_load_bearing_has_capability_probe.py` catches missing/stale load-bearing probes; `builder_audit_boundary.py` encodes the post-G.2a builder/audit boundary. The weak point is integration: many packet-local validators still allow stale source hashes, pre-G.2a audit-absence checks, thin `load_bearing` labels, or axis-named receipts that are only audit/candidate labels.

Current strict-source-backed sweep over tracked committed envelope results:

- total tracked `*envelope_results.json`: 169
- pass: 150
- fail: 19

The unlock path is not "trust less"; it is mechanical: add a commit-time source-hash freshness gate, require strict source-backed plus tool-intent checks for new three-engine envelopes, teach the stage gate explicit v6 claim-ceiling vocabulary, repair the remaining hard audit-absence packet validators, and make load-bearing capability probes fresh and function-level.

## Shared Rubric

- VALID: the result is computed from source, reproducible, controls fire for computed reasons, independently cross-audited or honestly labeled awaiting-audit, and the claim's name matches what was actually measured. Honest negatives, nulls, and deaths are valid.
- SHALLOW: real computation but the claim exceeds the measurement. Species include static/synthetic fields wearing measurement names; one-step witnesses wearing response/dynamics names; formula taxonomy wearing family-closure names; decorative tools such as `load_bearing` labels without capability probes or byte-identical `all_pass` mirrors; thin/unfair baselines; carrier-relative results cited carrier-free; pre-G.2a contract gaps; and results resting on provenance-disowned doctrine.
- FAKE/BROKEN: not reproducible from current source; hardcoded/echoed values presented as computed; claims with no computation behind them; red validators cited as green; quote fabrication; decorative SMT asserting literals.

This audit builds on the static-shallowness audit `b4ee8f030`, Hermes scorecard `b891e0611`, owner correction `0313d47bc`, and receipts-index addendum `276d42d81`.

## Route Truth

Wizard v4.2 Max Assembly was attempted as a partial controller-side route. The packet, skills manifest, compact MMM, and relevant mini-MMM registry were loaded; full MMM and native Codex subagent topology were not completed in this lane. Therefore this receipt does not claim a full Wizard topology, a full council run, or independent subagent plurality.

The requested files `scripts/load_bearing_proof.py`, `scripts/per_sim_contract.py`, and `scripts/max_deep_lego_gate.py` are not present in this checkout. Active equivalents audited here include `scripts/verify_load_bearing_has_capability_probe.py`, `scripts/lint_sim_contract.py`, `scripts/stage_gate.py`, `scripts/validate_three_engine_sim_result.py`, `scripts/audit_three_engine_source_claims.py`, and Makefile targets that wrap those gates.

## Gate-By-Gate Findings

| Gate / Validator | Actual Teeth | Where Green Means Less Than It Reads | Classification | Evidence Sentence | Upgrade To VALID |
|---|---|---|---|---|---|
| `scripts/stage_gate.py` and Makefile stage-gate targets | Reads `system_v5/ops/stage_gate.json`; orders stages as tool micro, tool integration, lego, coupling; allows current-stage and prior-stage claims; blocks `axis`, `bridge`, `engine`, `coexistence`, and `scientific_coupling` until coupling-stage evidence and exact receipts exist. | Top-level `all_pass:true` means the governance file is internally readable and current low-stage claims are allowed; it does not mean axis/bridge/engine claims are admissible. | VALID for governance blocking; SHALLOW if cited as global readiness. | Fresh run showed `active_stage=lego`; `axis`, `bridge`, and `engine` claim checks exited blocked. | Add explicit v6 claim-ceiling vocabulary so axis-named audit receipts can be allowed as names/labels without implying axis-stage admission. |
| `scripts/validate_three_engine_sim_result.py` | Checks `schema_version`, engine objects, ran flags, source paths, no peer reads, non-empty packages, load-bearing subset of packages, crossover proofs, divergence object, optional PyTorch, no promotion unless explicit, and optional source-backed/tool-intent audits. | Without `--strict-source-backed --require-tool-intent`, green is mostly envelope shape plus declared engine/tool fields; it does not recompute the science, prove current source hashes, or guarantee rich package semantics. | SHALLOW by default; VALID as a strict envelope contract when the claim name is "three-engine envelope shape/source-token audit." | `--strict-source-backed` currently fails 19 of 169 tracked envelopes. | Make strict-source-backed plus tool-intent mandatory for new or touched v6 envelopes, and compose it with source-hash freshness. |
| `scripts/audit_three_engine_source_claims.py` | Reads declared engine source files and checks whether rich package claims have source-level backing tokens and observables. | Source-token evidence is not the same as capability evidence or semantic load-bearing use. | SHALLOW. | It catches engine_64-style rich-tool thinness, but a token match can still be a decorative import. | Require function-level `package_observables`, probe receipts, and negative controls tied to the exact claimed tool function. |
| `scripts/lint_sim_contract.py` | Static AST/text lint for classification, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, classical divergence logs, load-bearing probe presence/freshness, numpy/PyTorch control patterns, and unsafe repair sentinels. | It does not execute sims or recompute results; violations are repo-wide and many legacy probes still fail. | VALID for static contract lint; SHALLOW for result validity. | Current run checked 3809 sims and found 1146 violations across 838 sims. | Run on staged/touched paths as a required pre-commit gate and separate legacy baseline debt from new-regression failures. |
| `scripts/verify_load_bearing_has_capability_probe.py` | Parses `TOOL_INTEGRATION_DEPTH` and verifies each `load_bearing` tool has a capability probe with passing summary fields and freshness. | A passing capability probe does not prove the tool is load-bearing inside the specific sim claim, and stale probes are common. | VALID for probe-existence/freshness; SHALLOW for claim-specific tool semantics. | Whole-repo run audited 3778 sims with depth metadata and found 319 violations. | Require per-tool/function probe id, source hash, and exact observable consumed by the result validator. |
| `scripts/builder_audit_boundary.py` | Allows missing audit verdict during build; after audit, accepts only independent/fresh/read-only audit headers and rejects builder-side audit claims. | Only works where packet-local validators delegate to it; some packets still hard-check permanent audit absence. | VALID when used; SHALLOW across the estate until all hard absence checks are removed. | 70 tracked packet validators contain the shared helper pattern, but 10 still carry suspect hard absence checks. | Replace all `packet_audit_verdict_absent`/`not AUDIT_VERDICT.exists()` gates with shared helper calls and add a census gate. |
| `scripts/wizard_loop_state.py` | Reports git head/status, open lane count, load/memory, recent commits, and mtime freshness for open-lane audit verdicts. | It is not a source-hash freshness gate and not evidence that worker topology ran. | VALID for loop-state observation; SHALLOW for result freshness. | Fresh run reported zero modified tracked files and zero open lanes, but this says nothing about stale envelope source locks. | Add separate source-hash freshness gate and keep loop state as route/ops telemetry only. |
| `scripts/wizard_v4_2_runtime_audit.py` | Audits v4.1 drift, queue state, heartbeat, worker receipts, ops-report freshness, lint status, helper drift, and runtime blockers. | With skipped preflight or zero worker receipts, it cannot certify Max Assembly topology. | VALID as a red runtime guard; SHALLOW as topology proof. | Fresh bounded run returned `ok:false`, `runner_idle_with_backlog`, `worker_receipts_checked:0`, and contract-lint timeout fallback. | Require full preflight plus accepted worker receipts before any visible FULL Wizard/runtime claim. |
| `scripts/validate_wizard_worker_receipts.py` | JSON/schema checks for worker receipt shape, v4.2 version, route, pool, launch surface, terminal status, topology-counting rules, artifact path, accepted conclusion, and external-pool markers. | Receipt shape is not proof the worker did good work or loaded the correct mini-MMM content unless artifact review follows. | VALID for receipt-shape/pool truth; SHALLOW for work quality. | The schema correctly prevents tools/external pools from being silently counted as Codex-native subagents. | Pair schema acceptance with artifact-path review and mini-MMM/path hash checks. |
| `scripts/codex_runtime_env_doctor.py` | Checks sim-stack interpreter alias, expected Python imports, Julia project when enabled, forbidden deps/pollution, and active installer/process hazards. | Import success is not tool capability, function coverage, or load-bearing use. | VALID for environment hygiene; SHALLOW for tool integration. | Fresh run with `--json --skip-julia` returned ok true and `install_state: stable_observed`. | Keep as preflight only; never cite as evidence for sim/tool claims. |
| Packet-local validators, strong family pattern | Recompute packet-specific tables, source locks, control rows, SMT flip behavior, manifest/depth constraints, and builder/audit boundary. | Many names are larger than their measured object: "axis", "basin", "engine", or "response" may mean finite witness, static readout, or scratch diagnostic. | Mixed: VALID when claim ceiling is local and source hashes are fresh; SHALLOW when names exceed measurement. | Strong examples include `geo_s7_discrete_refinement_v0` and `manifold_ab_weld_relation_v0`, which bind finite objects and controls tightly. | Require every packet receipt to carry one evidence sentence and a claim-ceiling field that matches the measured object. |
| Packet-local validators, weak/red pattern | Hard audit absence, stale source locks, validator writes during audit, generic envelope shape pass despite source drift, or known `all_pass=false`. | A green or cited packet validator can be stale, non-idempotent, or not green today. | SHALLOW to FAKE/BROKEN. | Lane A stale findings and Lane B red-state findings show generic validators can pass stale/broken packets. | Mechanical source-freshness gate, post-G.2a idempotency gate, and no-write validator mode. |

## Stage-Gate Tension

Fresh stage-gate facts:

- `system_v5/ops/stage_gate.json` says `active_stage: lego`.
- `stage_gate.py` allows `tool_micro`, `tool_integration_micro`, `tool_lego_fit`, and `lego`.
- It blocks `axis`, `bridge`, `engine`, `coexistence`, and `scientific_coupling` until coupling-stage evidence exists.

Adjudication by the repo's own authority order:

1. Current user request and `AGENTS.md` are top authority.
2. `AGENTS.md`, `ENFORCEMENT_AND_PROCESS_RULES.md`, `LLM_CONTROLLER_CONTRACT.md`, and `LEGO_SIM_CONTRACT.md` all preserve the hard ladder: tool/function, tool integration, lego, then coupling, then bridge/axis/engine claims.
3. The Makefile/stage gate is therefore authoritative for claim admission.
4. The v6 receipt process can use axis/engine words as route labels or audit categories only when the claim ceiling says so. It cannot promote an axis-named or engine-named packet into an axis/engine-stage claim while `stage_gate.py --claim axis|engine` is blocked.

Conclusion: the governance layer is internally stricter than some v6 naming. The unification should be vocabulary-aware, not lax.

Recommended unification:

- Teach `stage_gate.py` these non-promotional v6 ceilings: `axis_named_receipt_only`, `axis_readout_candidate_only`, `one_step_axis_witness`, `engine_schedule_trajectory_only`, `registered_basin_negative`, `scratch_diagnostic`, `audit_receipt_only`, and `awaiting_independent_audit`.
- Keep `axis`, `bridge`, `engine`, `coexistence`, and `scientific_coupling` blocked until their existing stage receipts exist.
- Require each v6 packet/result/receipt to declare both `stage_gate_claim` and `claim_ceiling`.
- Make validators fail when the packet name or receipt title implies a higher stage than `claim_ceiling`.

Alternative, if vocabulary is not added: v6 must stop shipping axis/engine-named claims until `make stage-gate-claim CLAIM=axis` or `CLAIM=engine` passes. That is cleaner but would block useful audit labels and scratch diagnostics. The better owner-aligned path is to keep labels but force ceilings.

## Strict-Source-Backed Sweep

Command shape:

```sh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  --strict-source-backed <tracked-envelope-result>
```

Committed envelope sweep result: 169 total, 150 pass, 19 fail.

Failures:

1. `system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_envelope_results.json` - JAX/SymPy source-token thin; Julia has no source-backed rich package evidence; Z3 not imported.
2. `system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_envelope_results.json` - JAX/SymPy source-token thin.
3. `system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json` - Julia has no source-backed rich evidence; Z3/SymPy not imported.
4. `system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_envelope_results.json` - Julia/Graphs source-token thin.
5. `system_v6/sims/ecd03_typed_coratchet_v0/results/ecd03_typed_coratchet_v0_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
6. `system_v6/sims/ecd05_instruction_machine_v0/results/ecd05_instruction_machine_v0_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
7. `system_v6/sims/engine_64_stage_full_run_v0/results/engine_64_stage_full_run_v0_envelope_results.json` - JAX has no rich package evidence; SymPy source-token thin; Julia has no rich evidence; `julia_gf4_stdlib` not imported.
8. `system_v6/sims/entropy_type_ratchet_v1/results/entropy_type_ratchet_v1_envelope_results.json` - PyTorch load-bearing empty/no source-backed rich claim.
9. `system_v6/sims/fiber_augmented_cover_v1/results/fiber_augmented_cover_v1_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
10. `system_v6/sims/fiber_augmented_cover_v2/results/fiber_augmented_cover_v2_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
11. `system_v6/sims/fiber_augmented_cover_v2_1/results/fiber_augmented_cover_v2_1_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
12. `system_v6/sims/fiber_cover_incidence_structure_v0/results/fiber_cover_incidence_structure_v0_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
13. `system_v6/sims/geo_s10_intertwiner_depth_v0/results/geo_s10_intertwiner_depth_v0_envelope_results.json` - Julia has no rich evidence; `julia_gf4_stdlib` not imported.
14. `system_v6/sims/malcev_akivis_tangent_micro_v0/results/malcev_akivis_tangent_micro_v0_envelope_results.json` - JAX has no rich package evidence; Z3/CVC5 not imported.
15. `system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/results/six_bit_two_trigram_szilard_fixture_v0_envelope_results.json` - Julia has no rich evidence; `julia_gf4_stdlib` not imported.
16. `system_v6/sims/topology_parity_cell_model_v1/results/topology_parity_cell_model_v1_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
17. `system_v6/sims/topology_parity_guard_v2/results/topology_parity_guard_v2_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
18. `system_v6/sims/topology_parity_guard_v3/results/topology_parity_guard_v3_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.
19. `system_v6/sims/topology_parity_micro_v0/results/topology_parity_micro_v0_envelope_results.json` - not `three_engine_sim_result_v1`; `engines` missing.

Classification: these are not all broken results. Several are honest non-three-engine packets being tested by a three-engine validator. The gate failure means they cannot be cited as strict-source-backed three-engine envelopes.

## G.2a / Post-Audit Idempotency Census

Tracked packet validator count sampled by filename pattern: 132.

Shared builder/audit boundary helper pattern present in tracked packet validators: 70.

Suspect hard absence checks still present: 10.

Suspect validators:

1. `system_v6/sims/axis0_contender_heavy_v0/validate_axis0_contender_heavy_v0.py`
2. `system_v6/sims/basin_dof_perturb_and_read_v0/validate_basin_dof_perturb_and_read_v0.py`
3. `system_v6/sims/carnot_szilard_basin_cycle_v0/validate_carnot_szilard_basin_cycle_v0.py`
4. `system_v6/sims/discrete_axes12_pair_v0/validate_discrete_axes12_pair_v0.py`
5. `system_v6/sims/discrete_axis0_field_v0/validate_discrete_axis0_field_v0.py`
6. `system_v6/sims/discrete_axis3_placement_v0/validate_discrete_axis3_placement_v0.py`
7. `system_v6/sims/discrete_axis4_composition_v0/validate_discrete_axis4_composition_v0.py`
8. `system_v6/sims/discrete_axis5_family_partial_v0/validate_discrete_axis5_family_partial_v0.py`
9. `system_v6/sims/discrete_axis6_precedence_v0/validate_discrete_axis6_precedence_v0.py`
10. `system_v6/sims/ring_checkerboard_automaton_v0/validate_ring_checkerboard_automaton_v0.py`

Classification: SHALLOW until repaired. These validators may perform real packet checks, but permanent `audit_verdict.md` absence checks make them pre-G.2a/non-idempotent and can turn honest post-audit packets red.

Upgrade: replace hard absence with `scripts/builder_audit_boundary.py` and add a repo-level census target that fails new packet validators containing `packet_audit_verdict_absent` or `not AUDIT_VERDICT.exists()`.

## Freshness Gap

No current gate enforces source-hash freshness at commit time across the result estate.

Evidence:

- Lane A found stale source-path/source-sha pairs where generic validators still returned ok.
- `wizard_loop_state.py` only checks open-lane audit verdict mtime freshness.
- `wizard_v4_2_runtime_audit.py` checks ops report freshness and runtime state, not every envelope's declared source hash against the current committed blob.
- `validate_three_engine_sim_result.py --strict-source-backed` reads source files for package-token backing but is not a general source-hash commit gate.

Mechanical gate proposal:

1. Add `scripts/validate_source_hash_freshness.py`.
2. Input modes: `--staged`, `--paths`, `--all-tracked-results`, and `--changed-since <rev>`.
3. Parse JSON fields including `source_path`, `source_sha256`, `source_hash`, `source_locks`, `parent_source_sha256`, `runner_sha256`, and packet-local lock tables.
4. Resolve paths relative to repo root and packet root.
5. Compare declared hashes to current committed blob hashes for commit-time checks, and to worktree hashes for local preflight.
6. Fail missing source files, mismatched hashes, ambiguous relative paths, and hash fields with no path.
7. Make Makefile targets `source-freshness-gate` and `commit-result-freshness-gate`.
8. Make packet-local validators call this in check-only mode for their own packet/result files.

Classification: current freshness coverage is SHALLOW. The proposed gate is the single highest-leverage unlock because it turns stale positives into reproducible current-source claims or honest awaiting-rerun labels.

## Load-Bearing Capability-Probe Check

Whole-repo probe command:

```sh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/verify_load_bearing_has_capability_probe.py
```

Result:

- audited sims with `TOOL_INTEGRATION_DEPTH`: 3778
- violations: 319
- dominant species: stale capability probes

Contract lint context:

- checked sims: 3809
- total violations: 1146
- sims with violations: 838
- `C1_classification_missing`: 551
- `C5_probe_stale`: 302
- `C2_manifest_missing`: 139
- `C3_depth_missing`: 84
- `C4_divergence_log_missing`: 68
- `C5_missing_probe`: 2

Spot checks:

| Sim | Load-Bearing Claim Result | Classification |
|---|---|---|
| `system_v4/probes/sim_3qubit_dag_formal_ordering_v2.py` | `cvc5`, `pytorch`, `rustworkx`, `sympy`, and `z3` all had accepted probes. | VALID for probe existence/freshness. |
| `system_v4/probes/sim_2_category_strict_coherence_constraint_canonical.py` | `cvc5` had an accepted probe. | VALID for probe existence/freshness. |
| `system_v4/probes/sim_L1_loop_families.py` | `numpy` probe stale. | SHALLOW until refreshed. |
| `system_v4/probes/sim_integration_networkx_pyg_graph_roundtrip_micro.py` | `pyg` accepted; `networkx` stale. | Mixed; SHALLOW for the stale tool. |

Conclusion: the capability-probe rule exists and has real teeth, but `load_bearing` remains a shallow label unless the exact function/capability probe is fresh and consumed by the packet result.

## Packet-Local Validator Pattern Sample

| Packet / Family | Classification | One Sentence Of Evidence | Upgrade To VALID |
|---|---|---|---|
| `engine_64_stage_full_run_v0` | SHALLOW | Validator checks many real finite 64-schedule fields, controls, SMT rows, and manifest/depth fences, but strict-source-backed fails rich-tool evidence for the committed envelope. | Refresh/rebuild with strict-source-backed rich package observables and rename to finite schedule/trajectory unless engine-stage gate passes. |
| `basin_two_engine_joint_v4_flux` | VALID within ceiling | Validator binds per-leg hashes, erased/carried counts, product controls, SMT unsat/flipped-sat rows, divergence, and builder boundary. | Keep cited as registered finite basin/flux negative or scratch diagnostic, not carrier-free basin theorem. |
| `ecd06_prediction_first_inference_v2` | SHALLOW / awaiting refresh | Validator has real source locks, controls, no-leak checks, and nested three-engine checks, but supplemental source hash drift has been reported. | Refresh source locks and rerun before citing current-source validity. |
| `discrete_axis4_composition_v0` | SHALLOW | Validator recomputes one-step carrier tables and controls, but the axis/composition name exceeds one-step witness scope and the validator carries a hard audit-absence check. | Repair G.2a boundary and retitle/ceiling as one-step Axis-4 composition witness. |
| `entropy_type_ratchet_v2` | VALID within ceiling | Validator checks construction-attempt rows, doctrine comparison, parent artifact derivation, controls, and strict nested envelope validation. | Keep as bounded construction/death table, not entropy-family closure. |
| `fiber_augmented_cover_v2_1` | VALID as negative guard | Validator checks rebuild object, hashes, `all_pass`, and explicitly forbids Betti/homology computation claims. | Keep as no-Betti/guard plumbing; do not cite as topology result. |
| `geo_s7_discrete_refinement_v0` | VALID within ceiling | Exact-strength validator binds finite interval/topology certificates, source hashes, negative controls, and SMT flip behavior. | Keep finite/discrete; require separate bridge for continuum/general theorem. |
| `manifold_ab_weld_relation_v0` | VALID within ceiling | Validator binds A/B states by hash, weld-only rows, nonrecoverability controls, SMT erased/perturbed flips, and trajectory artifact hash. | Keep as finite A/B weld relation object, not manifold dynamics. |
| `ring_checkerboard_automaton_v0` | FAKE/BROKEN if cited green today | The packet is known to have red-state/all-pass false and pre-G.2a boundary issues. | Repair validator boundary and rerun before any green citation. |
| `terrain_spinor_flux_nest_n4_v0` | FAKE/BROKEN until rerun | Lane A found stale source hash behavior where generic validation can pass despite source drift. | Add/trigger source-freshness gate, rerun from current source, and relabel stale receipt as historical only. |

## Unlock Proposal, Ranked By What It Unblocks

1. Source-hash freshness gate.
   - Unblocks: current-source reproducibility and stale-result cleanup.
   - New gate: `scripts/validate_source_hash_freshness.py` plus Makefile targets for staged and all-tracked result checks.
   - Stop condition: no result with declared source hash can be committed or cited green when the source blob has drifted.

2. Stage-gate/v6 claim-ceiling unification.
   - Unblocks: honest axis/engine audit work without stage bypass.
   - New fields: `stage_gate_claim`, `claim_ceiling`, and `stage_gate_status`.
   - Stop condition: a packet title/name cannot imply a stronger stage than the gate admits.

3. Strict rich-tool gate.
   - Unblocks: engine_64-style rich-tool thinness.
   - Required command for new/touched envelopes: `validate_three_engine_sim_result.py --strict-source-backed --require-tool-intent`.
   - Stop condition: `load_bearing` rich tools must have source-backed observables and function-level capability probes.

4. G.2a validator census.
   - Unblocks: post-audit idempotency and independent audit addenda.
   - New gate: fail packet validators with permanent audit-verdict absence checks unless explicitly legacy/quarantined.
   - Stop condition: audit verdict presence cannot make a once-green builder packet fail solely because audit exists.

5. Load-bearing probe freshness and specificity.
   - Unblocks: decorative tool labels.
   - Required check: `verify_load_bearing_has_capability_probe.py --sim <path>` for touched sims plus source freshness on probe receipts.
   - Stop condition: a `load_bearing` tool must name the exact capability/function and fresh probe consumed by the packet.

6. Packet validator check-only mode.
   - Unblocks: reliable audit reruns.
   - New convention: packet validators must not rewrite result JSON or audit files unless invoked with an explicit build/repair mode.
   - Stop condition: read-only audit commands leave `git status` unchanged except permitted receipt outputs.

7. Per-receipt classification/evidence/upgrade fields.
   - Unblocks: fast triage and honest negatives.
   - Required fields: `classification`, `evidence_sentence`, and `upgrade_to_valid`.
   - Stop condition: no receipt can say only `all_pass=true` without naming what passed and what remains below VALID.

## Final Classification

Lane D result: VALID audit receipt with partial Wizard route truth.

The tooling layer has real teeth, but they are not yet unified. The main false-green species are:

- contract-shape green cited as current-source validity;
- stage-gate green cited as axis/bridge/engine permission;
- load-bearing labels cited without fresh function probes;
- packet-local validator green cited despite stale hashes or pre-G.2a audit absence;
- rich package imports/tokens cited as capability use.

Honest negatives, nulls, and deaths should continue to count as VALID when their source is fresh, controls fire for computed reasons, and the claim name stays as small as the measurement.
