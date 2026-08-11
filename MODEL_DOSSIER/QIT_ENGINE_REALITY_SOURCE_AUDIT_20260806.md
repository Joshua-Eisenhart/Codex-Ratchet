# QIT Engine Reality Checkpoint — source-addressed audit

**Audit date:** 2026-08-06  
**Input:** QIT_ENGINE_REALITY_CHECKPOINT_20260806_v1.zip  
**Input SHA-256:** ae5544acb718222c8df09a1d4b853bb6740aacc8dd20935936010d60960c7fd2  
**Disposition:** **Accept as a reproducible negative diagnosis; do not treat it as a completed-QIT-engine or strong CB-gate receipt.**

## Bottom line

The checkpoint catches a real integration problem: its historic candidate emitters do not all consume the current 16-stage/four-loop schedule. In particular, the two inductive loop orders are superseded, and the whole-engine runner uses atlas enumeration rather than the current unreset eight-stage order. This is exactly the kind of defect that should stop CB from calling an assembled engine complete.

It does **not** invalidate the already exercised QIT primitives or the four-lane Quantum-Hopfield probe. It says that those real components and the authored 16-stage one-qubit atlas are not yet joined into the requested two-engine / four-loop / sixteen-stage object.

The pack's own 13/13 verifier is useful only as a **self-consistency check of the negative diagnosis**. It does not rehash its claimed source inputs or recompute the affine compositions. Two non-destructive mutation controls still pass 13/13 after the altered result is rehashed. Therefore this verifier must not be promoted into a CB release or admission gate unchanged.

## What was run here

The ZIP passed unzip -t; its entry names contained no absolute or traversal paths. Its 16-file MANIFEST_SHA256.txt passed. No content in the attached ZIP was modified.

| Check | Fresh outcome | Ceiling |
|---|---:|---|
| Manifest verification | 16/16 hashes match | Package-integrity receipt |
| audit_current_candidate.py against its schedule and supplied JSON receipts | exact fresh result; G0_schedule_source_binding = FAIL | Deterministic receipt replay and recomposition |
| verify_checkpoint.py on that fresh result | 13/13 | Result/schedule shape and expected-count self-consistency |
| Candidate stage-atlas source replay | 16 distinct selected one-qubit affine maps | Authored local-map result, not stage abilities |
| Candidate cycle-report source replay | 14 declared processing signatures; 0 reported flux in all four old cycle reports | Diagnosis of the shipped old report |
| Candidate deformation replay | each stage independently ramps identity to an authored endpoint | Not a cumulative parent-to-child deformation genealogy |
| Candidate whole-engine replay | uses atlas positions 1..8 and 9..16 | Not a current-schedule engine run |

Fresh checkpoint result files are preserved in [evidence/](evidence/). The fresh QIT_ENGINE_REALITY_AUDIT.json has result_sha256 4c4e3554c1d02f81fffb1bfd31ea286c8c523ba4f0ef0ad2ae76c0bc33a520eb.

## The real integration failure it found

The package's machine-readable schedule agrees with the active source layout and active Type-1/Type-2 runner tables. Its four intended loop words are:

| Engine | Loop | Current order | Shipped cycle-report order matches? |
|---|---|---|---:|
| Left / Type 1 | outer / deductive | TiSe → NeTi → NiFe → FeSi | yes |
| Left / Type 1 | inner / inductive | SeFi → SiTe → TeNi → FiNe | **no** |
| Right / Type 2 | outer / inductive | FiSe → TeSi → NiTe → NeFi | **no** |
| Right / Type 2 | inner / deductive | SeTi → TiNe → FeNi → SiFe | yes |

Thus the package correctly stops at G0_schedule_source_binding, before tuning channels, adding a Holodeck, or claiming engine behavior. The current active sources used for this reconciliation are:

| Active source | SHA-256 |
|---|---|
| Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/type1_full_engine_both_loops_sim.py | 6abd9ea834aa0805576bc2f124d631a8c55f91cd4eb8d417af259e9d087fa5b8 |
| Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/type2_full_engine_both_loops_sim.py | 1c24b2e5a8923cfba1d02763eb88f2c31576d62fd61f9ce49f91ccaa919c3abd |
| Codex-Ratchet/system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md | 562dc18974d79bf454461f169602dca7348a40d8db0f1b4a8c238494fafb2eac |
| Codex-Ratchet/system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md | f817c31be6d4abd2482fcb17081a9644d0e44465fead8e4f51e177c7e390c778 |

That agreement is a **working schedule contract**, not complete owner-source provenance: the ZIP names an upstream owner document but does not include it or bind its bytes with a content hash.

## What the candidate actually establishes

| Candidate result | Supported | Not supported |
|---|---|---|
| 16 unique (M,c) Bloch-affine maps | chosen one-qubit local maps differ | 16 distinct cognitive/engine abilities |
| 14 processing signatures | duplicate descriptor pairs FiNe/NeFi and FeSi/SiFe are exposed | a stage-specific common-task/ablation tournament |
| 12 distinct cyclic full-return maps | phase-return collisions are detectable | 16 independently generated trapping regions |
| 12 point attractors plus invariant/no-point cases | local portrait classification | a nested 2 → 4 → 16 attractor hierarchy |
| identity-to-endpoint ramps | individual deformation families can be replayed | a cumulative chain in which each constraint deforms the preceding object |

The stage-atlas source is a plain Python/Bloch-affine construction, not a cross-runtime QIT implementation. It is a valid exploratory fixture, not a substitute for the already exercised QuTiP, JAX, PyTorch/PyG, and Julia QuantumOptics lanes.

Keep the carrier distinction explicit: the active formal source presents C^2 as a minimal live carrier for its finite QIT construction; the three-qubit floor appears in model-handoff/engine-scale material. A future run can require three qubits, but it should record that as an owner-level engine contract rather than silently claim it follows from the minimal-carrier statement.

## New verifier defects found by this audit

These controls altered only copies in scratch/evidence, never the attached ZIP or project sources.

| ID | Control | Observed result | Repair |
|---|---|---|---|
| QIT-CP-1 | Replace the result's recorded schedule hash with 64 zeros, recompute result_sha256, rerun verifier | **13/13 PASS** | Hash the schedule bytes consumed and compare them to a trusted input manifest. |
| QIT-CP-2 | Alter a recomposed affine-return matrix entry, recompute result_sha256, rerun verifier | **13/13 PASS** | Independently load stage receipt and recompute every claimed map/loop/engine value. |
| QIT-CP-3 | Inspect source/result relationship | Audit consumes shipped JSON receipts rather than executing and binding producer sources; named owner source document is absent | Bind producer code hashes + input hashes + fresh output hashes; include or content-address authority source. |

The preserved controls are executable in [evidence/mutation_control.py](evidence/mutation_control.py). Their outputs are in the same directory. The point is not that the checkpoint is dishonest: it openly stops at a negative conclusion. The point is that its verifier is too shallow to become the deterministic CB gate that protects the next build.

## Correct build order from here

Do **not** retune all physics or jump to the Holodeck. Make the missing bridge as a bounded, deterministic product first.

| Gate | Build | Required evidence | Claim ceiling |
|---|---|---|---|
| G0 | source_schedule_autonomous_return_v1 | One canonical schedule consumed directly by four loop adapters and two no-reset engine adapters; source, schedule, inputs, outputs all hash-bound | Schedule integration only; may remain a one-qubit fixture |
| G0v | Independent CB/ClaimGate verifier | Rehash inputs, replay compositions, reject stale path/hash/producer-boolean evidence; positive and schedule-permutation controls | Verifier integrity, not QIT validity |
| G1 | Real-QIT carrier lift | Explicit owner decision on carrier scope; stage maps implemented by actual QIT APIs; CPTP/Choi or equivalent validity, cross-lane comparison | Physical/simulation validity at selected scope |
| G2 | Four-loop and two-engine behavior | Unreset runs, common task/load, stationary-current/affinity criteria if claimed, basin/subbasin observables, destructive controls | Bounded engine behavior, not model proof |
| G3 | Stage-ability tournament | One task family, success observable, coordinate dictionaries, and per-stage ablation/replacement loss | 16 operationally distinguishable roles if earned |

At G0, do not change channel parameters. The test is simply: do every producer and consumer use the same schedule, and can an independent verifier recompute the output? This is the smallest repair that turns a real defect into CB fuel.

At G1 and later, CB should remain model-agnostic: schedule external engines, preserve inputs/outputs, run deterministic gates, and keep admission/promotion disabled unless named gate evidence exists. It should not be the LLM and it should not decide the mathematics. Actual QIT engines remain external runtimes; any internal CB simulation helper stays a separate labelled test tool.

## Practical state after this checkpoint

| Question | Honest answer |
|---|---|
| Are real QIT libraries and bounded QIT computations running? | **Yes.** Four-lane Quantum-Hopfield and related bounded runs established that separately. |
| Is there an authored 16-stage candidate? | **Yes.** It has 16 selected one-qubit affine maps. |
| Are there two completed QIT engines with four functioning loops and 16 demonstrated abilities? | **No.** Schedule binding fails first; behavior and ability gates remain unearned. |
| Does the checkpoint help? | **Yes.** It gives the smallest next repair instead of conflating tools, maps, and engine completion. |
| Is Holodeck/world-model expansion the critical path? | **No.** Preserve it, but keep it downstream of the source-bound QIT bridge. |

This makes the immediate task concrete: build and gate the schedule-bound bridge, then lift that same structure to the chosen real-QIT carrier. Nothing in this audit claims proof of the broader model, physics, or a unique manifold.

