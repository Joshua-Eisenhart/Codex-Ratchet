# Cross-Runtime Env Mapping Repair

Status: current repair packet for Hermes Desktop, Claude Code/TUI, Codex TUI,
and Codex app.
Updated: 2026-06-09.

This page exists to prevent old docs, skills, agents, and copied prompt
templates from sending workers into the wrong Python or Julia runtime.

## Current Runtime Map

Use these as current command targets:

```text
repo: /Users/joshuaeisenhart/Codex-Ratchet
python_preferred_alias: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
python_physical_env: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
julia_carrier: JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
runtime_map: system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md
full_target_sets: system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md
doctor: scripts/codex_runtime_env_doctor.py
mapping_audit: scripts/audit_runtime_mapping_references.py
```

The physical Python env may appear in historical receipts. New command examples,
role cards, and worker prompts should use the `sim-stack` alias.

When deciding whether a package is already present, optional, quarantined, or
blocked, use `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`. The
canonical Python env already has broad JAX, PyTorch, graph/topology, proof, and
AI support; missing CS/causal extras are optional probe candidates, not default
install targets.

## Bad Mappings To Demote

Demote these to historical/physical-target/reference-only unless the task is
explicitly reproducing an old receipt:

```text
bad mapping to demote: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3
bad mapping to demote: /opt/homebrew/bin/python3
bad mapping to demote: /usr/local/bin/python3
bad mapping to demote: /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
bad mapping to demote: /opt/homebrew/bin/julia --startup-file=no -e ...
```

The Julia carrier command is valid only with `JULIA_LOAD_PATH=@:@stdlib`.
Default-project Julia probes are smoke/global observations, not carrier truth.

## Required Checks

Run from `/Users/joshuaeisenhart/Codex-Ratchet`:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/audit_runtime_mapping_references.py
make runtime-environment-audit
```

For Codex skills:

```bash
python3 /Users/joshuaeisenhart/.codex-second/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
```

## Current Local Result

Current Codex repair pass:

```text
doctor: ok=True install_state=stable_observed
mapping_audit: ok=True failure_count=0
runtime-environment-audit: blocker_count=0 advisory_count=0
```

Warnings from `audit_runtime_mapping_references.py` are allowed only for
historical/reference receipts, not active command surfaces.

## Sendable Messages

Individual messages live in:

```text
system_v5/ops/runtime_mapping_repair_messages/hermes-desktop.md
system_v5/ops/runtime_mapping_repair_messages/claude-code.md
system_v5/ops/runtime_mapping_repair_messages/codex-tui.md
system_v5/ops/runtime_mapping_repair_messages/codex-app.md
```

Send the relevant file verbatim to each runtime, then require the checks above
before accepting that surface as repaired.
