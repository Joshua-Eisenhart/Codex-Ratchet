# Python / Repo / Skills Inventory and Cleanup Plan

Status: working inventory
Scope: clean up the repo folder slowly and properly, starting with Python/tooling
Primary goal: remove redundant tooling from inside the repo, especially `.venv_spec_graph`, only after a clean external/canonical stack is documented, installed, and verified

## 1. Current intent

This document exists to make cleanup slow, explicit, and reversible.

Use discipline:
- this is the cleanup policy doc, not the raw machine dump
- for the fuller machine-scope listing, see `FULL_MACHINE_PYTHON_REPO_SKILLS_INVENTORY.md`
- this doc should stay compact and policy-oriented

Rules:
- do not delete active tooling before replacement is verified
- do not rely on memory or shell assumptions about where packages live
- do not mix repo cleanup with broad repo refactors
- Python/tooling cleanup comes first
- repo location stays on Desktop for now
- Git repos remain in `~/GitHub`
- Python-related tooling should eventually be standardized outside the repo

## 2. High-level current state

Main repo:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet`
- current size: about `1.5G`

Repo-local Python environment to remove eventually:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph`
- current size: about `1.0G`
- this is the biggest obvious cleanup target inside the repo
- do NOT delete yet because repo code still references it

Chosen clean external folder for Python-related stuff:
- `/Users/joshuaeisenhart/python`
- currently exists
- intended as the clean home for future Python-related tooling/env organization

## 3. Known location classes

### 3.1 Main repo
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet`

Contains at least:
- `system_v4`
- `system_v5`
- `core_docs`
- repo-local `.venv_spec_graph`

### 3.2 Git repos / reference repos
- `/Users/joshuaeisenhart/GitHub`

Top-level repos currently seen:
- `codex-autoresearch`
- `hermes-agent`
- `hermes-agent-self-evolution`
- `leviathan`
- `leviathan-agent-lease`
- `leviathan-agentping`
- `leviathan-agents`
- `leviathan-lev-agentfs`
- `leviathan-lev-content`
- `pi-mono`
- `reference`
- `Sofia`

Important note:
- these should remain in `~/GitHub`
- cleanup should not move Git repos out of `~/GitHub`

### 3.3 Separate non-repo sim workspace
- `/Users/joshuaeisenhart/LevRatchet`

This appears to be a real separate sim/results workspace with many Python runners and JSON result artifacts.
It must be treated as a separate inventory surface, not ignored.

### 3.4 User-level Python package locations
- `/Users/joshuaeisenhart/Library/Python/3.13`
- `/Users/joshuaeisenhart/Library/Python/3.9`

Observed in `3.13`:
- `torch`
- `sympy`
- `networkx`
- `jinja2`
- `psutil`
- other user-site packages

Meaning:
- some Python tooling is installed in user-site, outside repo envs

### 3.5 Other Python/tooling-related locations
- `/Users/joshuaeisenhart/.local`
- `/Users/joshuaeisenhart/.conda`
- `/Users/joshuaeisenhart/.continuum/anaconda-client`
- `/Users/joshuaeisenhart/.hermes/hermes-agent/venv`

Meaning:
- tooling and environments are currently spread across several locations

## 4. Interpreter situation

Known Python 3 executables:
- `/opt/homebrew/bin/python3` -> `Python 3.13.6`
- `/usr/local/bin/python3` -> `Python 3.13.2`

Important consequence:
- the machine has multiple Python installations
- the repo/tooling must standardize on one canonical interpreter family

## 5. What appears to be the canonical Python base right now

Current evidence points to Homebrew Python as the correct base:
- `/opt/homebrew/bin/python3`

Reasons:
- rich package stack is available there
- `.venv_spec_graph` was created from Homebrew Python
- `/usr/local/bin/python3` lacks key packages required by the repo

Repo-local `.venv_spec_graph/pyvenv.cfg` shows:
- `home = /opt/homebrew/opt/python@3.13/bin`
- it was built from Homebrew Python

## 6. Key package/tool observations

### 6.1 Homebrew Python has the rich stack
Observed import-resolving under `/opt/homebrew/bin/python3`:
- `z3`
- `gudhi`
- `torch_geometric`
- `toponetx`
- `clifford`
- `hypothesis`
- `hypernetx`
- `kingdon`
- `pyquaternion`
- `xgi`

Observed install location:
- `/opt/homebrew/lib/python3.13/site-packages`

### 6.2 /usr/local Python is not the correct base
Under `/usr/local/bin/python3`, at least these fail:
- `z3`
- `gudhi`
- `torch_geometric`
- `toponetx`
- `clifford`
- `hypothesis`

Conclusion:
- `/usr/local/bin/python3` should not be treated as canonical for Codex Ratchet

### 6.3 User-site packages are active too
Both global interpreters see:
- `/Users/joshuaeisenhart/Library/Python/3.13/lib/python/site-packages`

This means user-site package state is part of the real environment picture and must be documented before cleanup.

## 7. Repo-local environment cleanup target

Target for eventual removal:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph`

Reason:
- too large
- should not live inside the repo long-term
- redundant once a clean external/canonical Python setup is verified

But currently blocked because code still references it.

## 8. Known hardcoded `.venv_spec_graph` references

Confirmed direct references include:
- `system_v4/probes/sim_geometry_truth.py`
- `system_v4/probes/sim_nonclassical_guard_probe.py`
- `system_v4/probes/sim_edge_state_writeback.py`
- `system_v4/probes/run_formal_geometry_packet.py`
- `system_v4/probes/run_root_emergence_packet.py`
- `system_v4/probes/sim_axis_7_12_audit.py`
- `system_v4/skills/nested_graph_builder.py`
- `system_v4/skills/pyg_heterograph_projection_audit.py`
- `system_v4/skills/toponetx_projection_adapter_audit.py`
- `system_v4/skills/clifford_edge_semantics_audit.py`
- `system_v4/skills/qit_graph_stack_runtime.py`

Important note:
- this is a confirmed set from current audit work
- before deletion, the complete patch list should be rechecked once more

## 9. Skills / probes scale snapshot

Observed counts in main repo:
- `system_v4/skills/*.py`: about `157`
- `system_v4/probes/*.py`: current machine count came back as `1256`

Note:
- the probes count should be treated as a rough current machine-scan figure and revalidated before using it for planning decisions

## 10. Formal cleanup principles

### 10.1 Python first
Cleanup starts with Python/tooling inventory and standardization.

### 10.2 No literal “moving” unless necessary
Preferred cleanup model:
- standardize one canonical Python base
- install and test there
- make repo use that
- delete redundant old versions later

### 10.3 Keep repo and Git repos where they belong
- main repo stays on Desktop for now
- Git repos stay in `~/GitHub`
- Python/tooling standardization happens around them, not by relocating them

### 10.4 Deletion rule
Nothing gets deleted until:
- replacement path is documented
- replacement path is tested
- repo scripts are patched
- critical probes run against the replacement path

## 11. Canonical organization target (Python phase only)

Current chosen clean folder:
- `/Users/joshuaeisenhart/python`

Planned role:
- home for clean Python-related organization outside the repo

This does NOT mean everything is physically moved there right away.
It means cleanup should converge toward a clean external Python/tooling setup rooted there, while using Homebrew Python as the canonical interpreter base.

## 12. Immediate next audit/document tasks before execution

1. Reconfirm full hardcoded `.venv_spec_graph` reference list
2. Inventory what under `~/GitHub` is only reference material versus runtime dependency
3. Inventory `LevRatchet` and decide whether it is:
   - active separate workspace
   - legacy
   - partial duplicate
   - migration target later
4. Record the exact canonical interpreter decision:
   - expected answer currently: `/opt/homebrew/bin/python3`
5. Define the future external Python/tooling structure under `/Users/joshuaeisenhart/python`
6. Define the exact test suite that must pass before deleting `.venv_spec_graph`

## 13. Minimum deletion gate for `.venv_spec_graph`

Do not delete `.venv_spec_graph` until all are true:
- a clean replacement environment/tooling layout is documented
- Homebrew Python is confirmed as canonical interpreter base
- required packages are available in the replacement path
- hardcoded references are patched away
- critical probes and packet runners succeed using the replacement path
- imports no longer depend on repo-local venv behavior

## 14. Critical probes/runners that must be in the deletion test set

At minimum:
- `system_v4/probes/sim_geometry_truth.py`
- `system_v4/probes/sim_nonclassical_guard_probe.py`
- `system_v4/probes/sim_edge_state_writeback.py`
- `system_v4/probes/run_formal_geometry_packet.py`
- `system_v4/probes/run_root_emergence_packet.py`
- graph-sidecar audits that currently reference `.venv_spec_graph`

## 15. Current best summary

The repo can be cleaned up, but the first phase is documentation and inventory, not deletion.

The strongest current conclusions are:
- the repo-local `.venv_spec_graph` is the biggest obvious repo-space cleanup target
- Homebrew Python appears to be the correct canonical interpreter family
- `/usr/local/bin/python3` is the wrong interpreter for this repo’s rich stack
- GitHub and LevRatchet are real adjacent dependency/reference/workspace surfaces and must be explicitly documented
- cleanup should proceed by standardization and verification, then deletion of redundancy later
