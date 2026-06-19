# Message To Claude Code / Claude TUI

Claude, repair your Codex Ratchet skills and agents so they use the current
runtime map and stop copying stale install paths.

Work in `/Users/joshuaeisenhart/Codex-Ratchet`, especially:

```text
.claude/skills/
.claude/agents/
CLAUDE.md only as reference, not Codex authority
```

Current map:

```text
python command path: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
python physical env: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
julia carrier command: JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier
runtime map: system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md
full target sets: system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md
doctor: scripts/codex_runtime_env_doctor.py
mapping audit: scripts/audit_runtime_mapping_references.py
```

Patch active Claude skills/agents so package-dependent work first reads the
runtime map, reads the full target-set map, and runs the doctor. New Python
commands should use the `sim-stack` alias. Old physical-path receipts must be
labeled historical/physical-target.
Carrier Julia checks must use strict `JULIA_LOAD_PATH=@:@stdlib`; global
`~/.julia/environments/v1.12` visibility does not prove carrier availability.

Do not install packages unless the controller or user approves an install
intent with target environment, reason, preflight result, and `install_allowed:
true`. Do not add `PythonCall`, `DLPack`, or `CondaPkg` to
`system_v5/julia_carrier/Project.toml` unless explicitly scoped as a bridge
micro-probe.

Run and report:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/audit_runtime_mapping_references.py
make runtime-environment-audit
```

Return:

```text
Claude env-map repair:
skills patched:
agents patched:
old docs demoted/superseded:
doctor:
mapping audit:
runtime audit:
remaining blockers:
```
