# Message To Hermes Desktop

Hermes, repair the active Codex Ratchet runtime mapping surfaces.

Work in `/Users/joshuaeisenhart/Codex-Ratchet` plus Hermes installed skills
under `/Users/joshuaeisenhart/.hermes/skills/software-development`.

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

Patch active Hermes skills, task-card templates, and current wiki/front-door
surfaces so new commands use the `sim-stack` alias. Treat the physical venv
path as historical/physical-target only. Treat `/opt/homebrew/bin/python3` and
`/usr/local/bin/python3` as audit targets or wrong-env comparisons, never
Codex Ratchet command authority. Treat default-project Julia as global smoke
only; carrier truth requires strict `JULIA_LOAD_PATH=@:@stdlib`.

Do not install, delete, or move packages. Do not rewrite historical receipts
except to add supersession wording when a receipt is likely to be copied as a
current instruction.

Run and report:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/audit_runtime_mapping_references.py
make runtime-environment-audit
```

Return a compact receipt:

```text
Hermes env-map repair:
files patched:
historical references left as receipts:
doctor:
mapping audit:
runtime audit:
blocked/needs Codex controller:
```
