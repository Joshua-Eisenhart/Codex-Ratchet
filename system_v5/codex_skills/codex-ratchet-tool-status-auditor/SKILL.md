---
name: codex-ratchet-tool-status-auditor
description: Audit Codex Ratchet tool integration status across skills, agents, sources, and result JSONs so package names become real function/API receipts before any claim is strengthened.
---

MIRROR: authoritative copy is .claude/skills/codex-ratchet-tool-status-auditor/SKILL.md; sync direction .claude -> codex_skills.

# Codex Ratchet Tool Status Auditor

Use this when the question is whether the new tool stack is actually integrated, not merely installed or mentioned.

## Core rule

A tool is only integrated when a real function/API call changes, constrains, certifies, or falsifies the bounded claim. Import success, package names, optimizer convergence, and engine agreement are not enough.

Each claimed tool needs a receipt with:

```text
tool name
function/API surface
input object
output object
positive case
negative or erased control
boundary case
demotion condition if the tool is removed or bypassed
source_path + source_sha256
result_path + result/schema/classification
```

## Audit surfaces

Check, in order:

1. `system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md`, `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`, and `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py`.
2. `system_v5/codex_skills/` plus active copies in `~/.codex/skills/` and `~/.codex-second/skills/`.
3. `.claude/skills/` and `.claude/agents/` when Claude is involved.
4. `system_v5/ops/formal_scouts/` and `system_v5/julia_carrier/` sources.
5. Result JSONs under `system_v5/ops/formal_scouts/results/` and carrier artifact results.
6. Tool fields: `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, `tool_calls`, `load_bearing_tool_claims`, `claim_path_tools`.

## Classification

Use these labels per tool/package:

- `installed_only`: import/version seen, no claim use.
- `imported_in_source`: import exists, no load-bearing receipt.
- `api_smoke`: a bounded API call ran, but not tied to a domain claim.
- `function_level_receipt`: API call has input/output and positive/boundary/negative controls.
- `claim_load_bearing`: removing/bypassing the tool demotes or flips the claim.
- `proof_discharge`: SMT/interval/reachability/SOS/Z3/cvc5 discharges a finite or certified claim.
- `control_only`: numpy/scipy/mpmath/CSV/pickle/host object or other baseline/control path.
- `quarantined`: risky package usable only behind adapter/isolated env.

## Canon algebra integration

For finite noncommutation/nonassociativity packets, verify the Julia-owned artifact:

```text
system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json
system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json
```

Consumers must verify `source_sha256`, `artifact_sha256`, `proof_tag`, `proof_pass`, `table_version`, and `bracket_convention`, then compute from exported `C[k][i][j]`. Hand-typed tables, hidden reassociation, optimizer-as-proof, `.numpy()`, `np.asarray`, CSV, pickle, or host-object bridges fail the audit.

## Output

Return:

```text
Observed: counts and paths checked
Integrated: tools with function-level receipts
Thin: tools only imported or smoke-tested
Quarantined/blocked: risky or missing packages
Estate gap: files/results lacking tool_calls or function-level receipts
Next gate: smallest skill/agent/source patch or capability sim needed
```

Do not promote scientific claims. This skill audits tool-integration readiness only.
