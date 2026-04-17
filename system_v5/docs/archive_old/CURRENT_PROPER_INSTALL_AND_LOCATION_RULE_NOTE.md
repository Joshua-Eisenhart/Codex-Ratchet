# Current Proper Install and Location Rule Note

Date: 2026-04-04
Status: current operational snapshot — not a migration plan

---

## The rule

**Anything actually used in the live execution path must live in a proper, known install surface.**

Proper means:
- packages: installed under the canonical interpreter (`/opt/homebrew/bin/python3`) via `pip install` or Homebrew
- interpreter references in code: explicit canonical path, not a relative or legacy venv path
- code and skills: inside the repo (`system_v4/`) under version control
- external reference repos: in `~/GitHub/` under their own git tracking
- archives and mining sources: identified as `later-mining only`, not imported into live execution

Improper means:
- a package exists only in a legacy venv or scattered user-site dir and is not available under the canonical interpreter
- a code file uses a hardcoded path to a legacy venv to spawn subprocesses
- a skill or probe only runs if a specific internal venv exists
- a needed resource lives in an unprocessed archive directory with no access plan

---

## Current canonical install surface

`/opt/homebrew/bin/python3` (Homebrew Python 3.13)

Core packages confirmed importable under it:
- proof/logic: `z3`, `sympy`, `hypothesis`, `pytest`
- graph/geometry: `torch`, `torch_geometric`, `toponetx`, `clifford`, `pyquaternion`, `kingdon`, `hypernetx`, `xgi`, `gudhi`
- data/validation: `networkx`, `pydantic`, `jsonschema`

Packages missing under canonical interpreter (needed for pre-Axis ladder):
- `cvc5` — present only in `.venv_spec_graph`; missing under Homebrew Python
- `quimb`, `qutip`, `ripser` — not yet needed in live path; still missing

---

## Highest-priority violations

### 1. `.venv_spec_graph` — live execution dependency, improper location
Three files construct `Path` objects pointing into `.venv_spec_graph` and pass them to subprocess calls:
- `system_v4/probes/run_formal_geometry_packet.py:33` — `SPEC_GRAPH_PYTHON = ROOT.parent.parent / ".venv_spec_graph" / "bin" / "python3"`
- `system_v4/probes/run_root_emergence_packet.py:22` — same pattern
- `system_v4/skills/qit_graph_stack_runtime.py:71` — `PREFERRED_INTERPRETER = REPO_ROOT / ".venv_spec_graph" / "bin" / "python"`

These are Tier-1 violations: if `.venv_spec_graph` is deleted, these execution paths break.
**Blocker:** `cvc5` (used by the formal geometry and root emergence packets) is missing under Homebrew Python. Cannot migrate until `cvc5` is installed or the call site is redesigned.

### 2. Four skills with `PREFERRED_INTERPRETER` string references (Tier 2)
- `system_v4/skills/nested_graph_builder.py:93`
- `system_v4/skills/clifford_edge_semantics_audit.py:29`
- `system_v4/skills/toponetx_projection_adapter_audit.py:27`
- `system_v4/skills/pyg_heterograph_projection_audit.py:31`

All set `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"`. These are relative string references (not `Path` objects used in subprocess). Lower urgency than Tier 1, but they will silently reference a wrong interpreter when `.venv_spec_graph` is eventually removed.

### 3. Scattered user-site packages under `~/Library/Python/3.13`
`torch`, `networkx`, `sympy` install to `~/Library/Python/3.13/lib/python/site-packages/` instead of the Homebrew site-packages directory. They are importable under Homebrew Python (the user site is on `sys.path`), so this is a low-severity violation today — but it means a `pip install` in a clean environment would not reproduce the full stack.

### 4. `cvc5` gap — needed package not in canonical surface
`cvc5` is present only in the legacy `.venv_spec_graph`. It is required by the formal geometry packet (pre-Axis Tier 2–3 ladder). Until it is installable under the canonical interpreter, the formal geometry packet cannot migrate off `.venv_spec_graph`.

---

## Preserved later-mining surfaces (not violations — intentional)

These surfaces contain useful content but are not in the live execution path. They should be left in place until actively mined.

| Surface | Location | Reason kept |
|---|---|---|
| `.venv_spec_graph` audit/historical docs | `system_v4/a2_state/audit_logs/` | Provenance records of past runs; must not be patched |
| `~/LevRatchet` | User home | Unprocessed archive; contains prior QIT work; not yet ingested |
| `~/GitHub/reference/*` | `~/GitHub/reference/` | Reference repos (z3, alphageometry, dreamcoder-ec); used as reading material, not imports |
| `system_v3` | Repo root | Prior system layer; owner-law canonical surface; not directly imported into v4 execution |

---

## Migration sequence (when to act)

Do not migrate yet. The sequence when `.venv_spec_graph` removal becomes safe:

1. Install `cvc5` under Homebrew Python (or determine it cannot be installed there)
2. If `cvc5` is available: migrate `run_formal_geometry_packet.py` and `run_root_emergence_packet.py` to `sys.executable` or canonical path
3. Confirm `qit_graph_stack_runtime.py` package requirements are met under canonical interpreter, then migrate its `PREFERRED_INTERPRETER`
4. Batch-update the four Tier-2 `PREFERRED_INTERPRETER` skill strings
5. Update run-instruction comments in affected probes
6. Only then consider deleting `.venv_spec_graph`

Do not delete `.venv_spec_graph` before step 3 is confirmed complete.

---

## What this note is not

This note is not a deletion plan.
It is not a renaming plan.
It is an operational map of where the current location/install surface stands and what the highest-priority violations are, so future migration handoffs can be bounded and sequenced safely.
