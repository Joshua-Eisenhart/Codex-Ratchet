---
name: codex-ratchet-tool-status-auditor
description: Audit Codex Ratchet tool integration status across skills, agents, sources, and result JSONs so package names become real function/API receipts before any claim is strengthened.
---

# Codex Ratchet Tool Status Auditor

Use this when the question is whether the new tool stack is actually integrated, not merely installed or mentioned.

This repo-held Codex skill is the source candidate governed by `AGENTS.md`. Claude skill and agent surfaces are reference-only when they are audited; they are not the authority or sync source for this file.

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

## Skill provenance receipt

Tool execution and skill use are separate claims. If a run says a skill affected the work, attach a dedicated receipt with schema `codex-ratchet-skills-used-v1` and validate it with:

```bash
python3 system_v5/codex_skills/codex-ratchet-tool-status-auditor/scripts/validate_skills_used.py RECEIPT.json --repo-root "$PWD"
```

Add `--allow-root PATH` once for each active skill home outside the repo. Unlisted roots fail closed.

Every `skills_used` entry has exactly these keys:

```json
{
  "path": "system_v5/codex_skills/example/SKILL.md",
  "sha256": "64 lowercase hex characters",
  "role": "guidance",
  "affected_commands": ["command-id"]
}
```

Rules:

- `path` resolves under the repo root or an explicit `--allow-root`, exists, and matches `sha256` byte for byte.
- `affected_commands` contains unique IDs from the receipt's exact `commands` ledger; a free-form command string is not an ID.
- `role: guidance` points to `SKILL.md`. It may name commands it constrained, but it is guidance evidence only and can reach at most skill-provenance L2.
- `role: executable_validator` or `role: executable_runner` points to a real file under that skill's `scripts/` directory, has a matching `guidance` entry for the sibling `SKILL.md`, and names at least one declared-success command that invokes the exact script path and emits a hash-matched artifact.
- The command ledger is self-reported. Even a valid executable entry is only `l3_eligible` and remains capped at skill-provenance L2. Actual L3 requires a separate, independently produced and hash-bound runner receipt, such as a Lev scorecard, that records the exact command/case IDs and passes its own validator.
- No skill-provenance receipt proves that a downstream tool API was load-bearing, discharges a scientific claim, or grants L4.
- Missing keys, extra keys, stale hashes, path escapes, unknown roles or commands, failed commands, decorative script mentions, or missing output artifacts block the receipt. Never infer skill use from package imports, prose, commit messages, or self-reported pass counts.

The complete command/artifact schema and promotion boundary are exercised by the validator's focused tests. Keep informative red verdicts; do not rewrite them green.

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
