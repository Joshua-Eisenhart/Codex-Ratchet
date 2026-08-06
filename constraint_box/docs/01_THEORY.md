# Why visible receipt checks fail

## The adversary produces the claim

Constraint Box is not merely a linter or a test runner. Its adversary is the thing producing the claim. The producer can also produce the receipt, helper script, process behavior, and plausible-looking evidence. The gate must not trust that party to report whether its own work happened.

A receipt can be internally consistent and still describe work that never occurred. A worker can import the named library, print the expected numbers, emit the expected fields, and satisfy a check designed around those fields. More receipt inspection does not establish a connection to the world.

## Five failed defenses

The repository records five successive candidate defenses. Each inspected the producer's representation more carefully without creating a producer-independent measurement of the claimed work.

1. Path-prefix exclusion rejected suspicious values except under approved fixture paths. Poison placed under a fixture prefix bypassed it. See `claimgate_plugin/results/purgatory_shape_detectors_v0.json`, field `the_one_error_class_four_times`.
2. A key-name denylist plus container allowlist tried to distinguish outcomes from configuration by shape. Cases b7, b8, and b9 moved the same meaning into allowed shapes. See `claimgate_plugin/results/purgatory_shape_detectors_v0.json`.
3. Twenty-two exempt full paths plus subtree pruning narrowed the shape detector again. Cases b11 and b12 used the exemptions and pruning boundary. See `claimgate_plugin/results/purgatory_shape_detectors_v0.json`.
4. Typed roles with bounded slots assigned receipt values to a grammar. A real measurement of `2.2e-15` fit inside a tolerance slot bounded `[0, 1e-3]`; the value was genuine but the role was false. See `claimgate_plugin/run_typed_grammar_regression.py`, `claimgate_plugin/results/purgatory_stress_lane2_v0.json`, and commit `ae1e7708e`, which names typed grammar as the fourth candidate.
5. Artifact/output binding ran a producer-authored leg under a fixed perturbation family. Receipt-as-input, probe detection, additive cancellation, and selection laundering defeated it. Its receipt's `status` field reads "FIFTH FAILED CANDIDATE SET. All four adversarial stress lanes returned DEFEATED. 56 findings, 40 CAN_FAIL. None may enter CI or the fired chain." See `claimgate_plugin/results/purgatory_artifact_binding_v0.json`, `claimgate_plugin/results/purgatory_artifact_binding_stress_v0.json`, and commit `950e64edf`, which names artifact binding as the fifth candidate.

`claimgate_plugin/engine_witness.py` is another failed candidate and exposes the common root cause. Its file header says not to import it into a gate. `claimgate_plugin/results/purgatory_engine_witness_v0.json` records that its presence, dispatch, poison, and mutation controls inspect process properties. They do not bind engine output to the receipt's claimed values. The current production chain nevertheless reaches an importer of this module; `PROVENANCE.md` records that as an open owner decision.

## Severance measured reachability, not use

Import severance blocks a module and expects the worker to fail. `PROVENANCE.md` records the decisive counterexample. One worker imports `scipy`, reads `scipy.__name__`, and computes with standard-library `math`. Another genuinely calls `scipy.linalg.expm`. Both return positive exit 0 and severance exit 1. The fake import exists only to give severance something to sever.

The observation is narrow and important: a blocked import proves module reachability. It does not prove execution of the claimed operation.

## Operation poisoning was stronger, then visible

`external_sim_estate/legacy_estate_v2/workers/operation_poisoner.py` replaces the named function with a function that raises. The polarity is intentionally inverted:

- A nonzero worker exit supports the claim that the worker called the operation.
- A zero worker exit shows the worker survived without the operation, so the control fails.

This is stronger than module severance because surviving is the failure.

The first end-to-end bypass read the poison's identity instead of calling the operation. At the time recorded in `PROVENANCE.md`, the replacement exposed `__name__ == "_severed"`, `__qualname__ == "poison.<locals>._severed"`, and `__module__ == "__main__"`. An inspecting stand-in exited nonzero after recognizing the probe. It and the genuine worker both reached `READY` with `all_required_controls_passed`.

Current source has since copied common callable metadata with `functools.wraps`, a copied signature, and replaced code names. The old three-field fingerprint is therefore a reproduced defect, not the current fingerprint. The current poisoner documents remaining identification channels: type, `__wrapped__`, `__code__`, `__globals__`, `sys.modules`, source inspection, and disassembly. The general defeat remains.

## The result

Each fix built a better probe that remained visible to the adversary. Visibility is the defeat condition. A producer that can identify the probe can answer it correctly without doing the claimed work.

Before adding a check, ask: can the worker tell that it is being probed? If yes, treat a pass as evidence about the worker's response to that probe, not evidence that the claimed operation occurred. Prefer observations the producer cannot author, choose, or distinguish from ordinary execution. Where that is unavailable, record the control as unmeasured and lower the claim.

Identification-resistant in-process poisoning is not solved. `PROVENANCE.md`, “Open decision for the owner,” item 5 requires a choice: find such a control or stop claiming that the operation executed.

## False positives destroy the gate

`claimgate_plugin/bridge/check_no_uncomputed_verdict.py` first matched 1,119 sites across 7,879 files. It was narrowed after measurement because it flagged honest in-process outcomes.

A gate that fires on honest work is the worse failure. People route around it. False positives are not a minor quality issue; they are the failure mode that removes the gate from the real workflow. The same standard applies to every new signature: preserve an honest negative fixture, and fail the regression when it starts firing.
