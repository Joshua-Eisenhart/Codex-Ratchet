You are an external proposal-only audit lane for Codex Ratchet.

Context:
- Repo: /Users/joshuaeisenhart/Codex-Ratchet
- Current object: system_v7/sims/probe_quotient_fingerprint_floor_v1/check_agreement.py
- Fresh result: system_v7/sims/probe_quotient_fingerprint_floor_v1/results/probe_quotient_fingerprint_floor_v1_three_engine_results.json
- Runner under patch: scripts/codex_sim_runner.py
- Admission validator: scripts/wizard_sim_admission.py
- Tool registry: scripts/two_root_constraints.py

Observed failure:
- codex_sim_runner.py reruns the result deterministically and three-engine validation passes.
- wizard_sim_admission fails when the admission packet basename/claim is probe_quotient_fingerprint_floor_v1_three_engine and tool_target is jax.
- Findings:
  - nonclassical_load_bearing_tool_missing_two_root_registry
  - nonclassical_suitable_load_bearing_tool_missing

Known constraints:
- Model output is proposal-only. It is not sim evidence, not admission evidence, not Wizard FULL proof, and not promotion evidence.
- Do not suggest decorative PyTorch, no-op torch fields, weakening nonclassical evidence gates, or treating z3/cvc5/Z3 as load-bearing when the result says they are supportive.
- JAX and Julia are current primary execution engines in AGENTS.md, but this rung-0 object is a scratch diagnostic, not a nonclassical manifold/engine claim.
- The result has sim_id/object_id probe_quotient_fingerprint_floor_v1 and classification scratch_diagnostic with promotion_allowed=false and formal_admission_allowed=false.

Answer in compact JSON with these keys:
- diagnosis: what is actually wrong
- smallest_executable_fix: exact patch direction
- files_to_touch: exact repo paths
- files_not_to_touch: exact repo paths
- verifier_commands: exact commands to run
- stop_condition: when to stop and not promote
- one_risk: the most likely way this fix could be overclaimed

Keep it concrete. If you are unsure, say what local deterministic check would decide.
