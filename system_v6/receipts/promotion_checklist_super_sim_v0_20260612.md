# Mechanical Eligibility Report - manifold_super_sim_v0

Date: 2026-06-12
Repo: `/Users/joshuaeisenhart/Codex-Ratchet`
Target packet: `system_v6/sims/manifold_super_sim_v0`
Target commit/context: `42542f120` plus hardening round 1 and posthardening clean validator state
Scope: mechanical checklist only. The final decision is owner-gated; this receipt does not make or imply that decision.

## Fresh Local Rerun

Criterion: passes local rerun.

Status: `ELIGIBLE_BY_CRITERION`.

Fresh commands run in this turn:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json, sys
from pathlib import Path
sim_dir = Path('system_v6/sims/manifold_super_sim_v0').resolve()
sys.path.insert(0, str(sim_dir))
import validate_manifold_super_sim_v0 as v
payload = json.loads(v.ENVELOPE.read_text())
errors = v.validate_payload(payload)
print(json.dumps({'ok': not errors, 'result_json': str(v.ENVELOPE.relative_to(Path.cwd())), 'errors': errors}, indent=2, sort_keys=True))
raise SystemExit(0 if not errors else 1)
PY
```

Observed result:

```json
{
  "errors": [],
  "ok": true,
  "result_json": "system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json"
}
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json
```

Observed result:

```json
{
  "ok": true,
  "result_json": "system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json"
}
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_super_sim_v0/tests
```

Observed result:

```text
6 passed, 11 subtests passed in 15.65s
```

## SIM_TEMPLATE And Classification Conformance

Criterion: SIM_TEMPLATE/classification conformance.

Status: `ELIGIBLE_BY_CRITERION_WITH_SCRATCH_CEILING`.

Mechanical observations from `system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json`:

```json
{
  "all_pass": true,
  "classification": "scratch_diagnostic",
  "formal_admission_allowed": false,
  "promotion_allowed": false,
  "schema_version": "three_engine_sim_result_v1",
  "sim_id": "manifold_super_sim_v0"
}
```

Packet-local validator checks the same fields and returned `ok=true`.

Boundary: this criterion supports only the recorded scratch-diagnostic/no-formal-admission/no-promotion ceiling. It does not change that ceiling.

## Tool Manifest And Load-Bearing Statuses

Criterion: tool manifest with non-empty reasons plus load-bearing statuses.

Status: `ELIGIBLE_BY_CRITERION`.

Mechanical observations from `TOOL_MANIFEST` and `TOOL_INTEGRATION_DEPTH` in the envelope result:

```json
{
  "manifest_count": 7,
  "manifest_tools": [
    "Graphs",
    "cvc5",
    "networkx",
    "sympy",
    "torch.func",
    "torch_geometric",
    "z3"
  ],
  "empty_reasons": [],
  "depth_values": {
    "Graphs": "load_bearing",
    "cvc5": "load_bearing",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "torch.func": "supportive",
    "torch_geometric": "supportive",
    "z3": "load_bearing"
  },
  "bad_depth_values": {}
}
```

Depth values are restricted to accepted contract vocabulary observed here: `load_bearing` and `supportive`. No empty tool reasons were found.

## Fresh Audit Existence And Caveat Closure

Criterion: fresh audit exists and caveat closure status is explicit.

Status: `ELIGIBLE_BY_CRITERION_WITH_STANDING_CAVEATS`.

Audit surface: `system_v6/sims/manifold_super_sim_v0/audit_verdict.md`.

Mechanical audit facts:

- Audit verdict exists and records `VERDICT: GENUINE-WITH-CAVEATS`.
- Accepted claim is explicitly scratch-diagnostic Family A integrated run over one shared 33-cell Bloch-grid object.
- Rejected-above-ceiling text forbids formal admission, canonical process truth, invariant manifold theorem, bridge/axis/physics evidence, two-engine/joint-engine convention result, or fully independent all-three-backend implementation of L1-L5.
- Closure annotation records `G1_SOURCE_HASH_LOCKS_ARE_WRONG_SURFACE` as `CLOSED_BY_HARDENING_42542f120_ROUND_1`.
- Closure annotation records `G2_G1_CHART_LABELS_DROPPED_IN_REDUCED_ROWS` as `CLOSED_BY_HARDENING_42542f120_ROUND_1`.

Standing caveats:

- `G3_UNIFIED_TRAJECTORY_CLASSIFICATION_MISSING`: trajectory lacks per-step `step-dependent` versus `carried` classification.
- `G4_BACKEND_INDEPENDENCE_SCOPE`: backend independence is partial; Julia independently checks G0/G1 counts, while JAX and PyTorch share the Python common builder for the full L1-L5 object.
- `G5_DECORATIVE_LAYER_DETECTOR_WEAK_ROWS`: L5 detector is weaker than direct L5 input perturbation.
- `G6_PARENT_CAVEATS_CARRIED`: parent caveats are carried at scratch ceiling.
- `G7_TRACKING_STATUS_CURRENT_TURN_ONLY`: tracking status must be cited from current commit/worktree state.

Updated required citation suffix from the audit:

```text
Use with caveats G3-G7: the trajectory lacks per-step step-dependent/carried classification, backend independence is partial, L5's decorative detector is weaker than a direct L5 input perturbation, parent caveats are carried, and tracking status must be cited from the current commit/worktree state.
```

## Checklist Result

Mechanical checklist result: all four requested criteria are `ELIGIBLE_BY_CRITERION` or `ELIGIBLE_BY_CRITERION_WITH_STANDING_CAVEATS`.

Decision boundary: owner-gated. This report records criterion eligibility only and does not alter classification, citation ceiling, queue state, or admission status.

