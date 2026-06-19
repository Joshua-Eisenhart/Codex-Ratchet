# Message To Codex App

Codex app, sync and validate the active Codex Ratchet runtime-map skills.

Current authoritative source:

```text
/Users/joshuaeisenhart/Codex-Ratchet/system_v5/codex_skills/
```

Active app skill home:

```text
/Users/joshuaeisenhart/.codex/skills/
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

Sync these skill folders from repo source into `.codex` if they differ:

```text
codex-ratchet-env-agent-coordination
codex-ratchet-tool-status-auditor
jax-sim
julia-sim
pytorch-sim
three-engine-sim
```

After sync, future package-dependent Codex Ratchet work must read the runtime
map, read the full target-set map, and run the doctor before installing, simming, or claiming package-backed
evidence. Use the `sim-stack` alias in command examples and receipts. The old
physical venv path is compatibility/history, not the preferred command path.

Run and report:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/audit_runtime_mapping_references.py
make runtime-environment-audit
for skill in codex-ratchet-env-agent-coordination codex-ratchet-tool-status-auditor jax-sim julia-sim pytorch-sim three-engine-sim; do
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/.codex-second/skills/.system/skill-creator/scripts/quick_validate.py "/Users/joshuaeisenhart/.codex/skills/$skill"
done
```

Return:

```text
Codex app env-map repair:
skills synced:
doctor:
mapping audit:
runtime audit:
quick_validate:
remaining blockers:
```
