# Current Tool Status — Installed vs Missing vs Not Wired

Status: working status document
Purpose: map the current tool plan onto the actual current environment and repo wiring state.

Canonical interpreter assumed for this status doc: `/opt/homebrew/bin/python3`

## 1. Installed and importable now (Homebrew Python)
- `z3` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/z3/__init__.py`
- `sympy` — import OK
  - path: `/Users/joshuaeisenhart/Library/Python/3.13/lib/python/site-packages/sympy/__init__.py`
- `gudhi` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/gudhi/__init__.py`
- `torch` — import OK
  - path: `/Users/joshuaeisenhart/Library/Python/3.13/lib/python/site-packages/torch/__init__.py`
- `torch_geometric` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/torch_geometric/__init__.py`
- `toponetx` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/toponetx/__init__.py`
- `clifford` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/clifford/__init__.py`
- `pyquaternion` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/pyquaternion/__init__.py`
- `kingdon` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/kingdon/__init__.py`
- `hypernetx` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/hypernetx/__init__.py`
- `xgi` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/xgi/__init__.py`
- `hypothesis` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/hypothesis/__init__.py`
- `pytest` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/pytest/__init__.py`
- `networkx` — import OK
  - path: `/Users/joshuaeisenhart/Library/Python/3.13/lib/python/site-packages/networkx/__init__.py`
- `jsonschema` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/jsonschema/__init__.py`
- `pydantic` — import OK
  - path: `/opt/homebrew/lib/python3.13/site-packages/pydantic/__init__.py`

## 2. Missing now under canonical interpreter
- `cvc5` — missing/failing
  - detail: `ModuleNotFoundError: No module named 'cvc5'`
- `quimb` — missing/failing
  - detail: `ModuleNotFoundError: No module named 'quimb'`
- `qutip` — missing/failing
  - detail: `ModuleNotFoundError: No module named 'qutip'`
- `ripser` — missing/failing
  - detail: `ModuleNotFoundError: No module named 'ripser'`

## 3. Current interpretation
- `installed` means importable from the canonical Homebrew Python base
- `missing` means not currently importable from that base
- `not wired` is separate: a tool may be installed and still not actually used in the repo execution path

## 4. Strongest installed core owner stack
- `pydantic`
- `jsonschema`
- `networkx`
- `pytest`
- `hypothesis`
- `z3`
- `sympy`

## 5. Strongest installed rich geometry / graph stack
- `torch`
- `torch_geometric` / `PyG`
- `toponetx`
- `clifford`
- `pyquaternion`
- `kingdon`
- `hypernetx`
- `xgi`
- `gudhi`

## 6. Fresh additions currently relevant now
- `sympy` — installed and importable now
- `gudhi` — installed and importable now
- `cvc5` — justified and present in older `.venv_spec_graph` evidence, but currently missing under the canonical Homebrew interpreter

## 7. Not wired yet / likely underused
These tools may exist but are not yet assumed to be integrated into the actual pre-Axis sim pipeline just because they import.
Likely examples:
- `cvc5`
- `sympy` (as exact pressure in current sims)
- `gudhi`
- `PyG` / `TopoNetX` / `clifford` writeback path in the real sim chain
- `kingdon`
- `hypernetx` / `xgi`
- `quimb` / `qutip` / `ripser` if later installed

## 8. Repo-local wiring issue still present
The repo still contains direct `.venv_spec_graph` references in `system_v4`, so install status alone is not enough.

Known hardcoded references currently found:
```
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis_7_12_audit.py:43:    print("        ./.venv_spec_graph/bin/python system_v4/probes/sim_axis_7_12_audit.py\n", file=sys.stderr)
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/run_formal_geometry_packet.py:33:SPEC_GRAPH_PYTHON = ROOT.parent.parent / ".venv_spec_graph" / "bin" / "python3"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_nonclassical_guard_probe.py:1:# REQUIRES: .venv_spec_graph
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_nonclassical_guard_probe.py:2:# Run as: ../../.venv_spec_graph/bin/python3 sim_nonclassical_guard_probe.py
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/run_root_emergence_packet.py:22:SPEC_GRAPH_PYTHON = ROOT.parent.parent / ".venv_spec_graph" / "bin" / "python3"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/formal_geometry_packet_run_results.json:9:      "python": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python3",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_edge_state_writeback.py:1:# REQUIRES: .venv_spec_graph
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_edge_state_writeback.py:2:# Run as: ../../.venv_spec_graph/bin/python3 sim_edge_state_writeback.py
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_geometry_truth.py:1:# REQUIRES: .venv_spec_graph
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_geometry_truth.py:2:# Run as: ../../.venv_spec_graph/bin/python3 sim_geometry_truth.py
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/safe_pack/task_2_sim_audit.md:12:5. Run the probe using `./.venv_spec_graph/bin/python system_v4/probes/sim_axis_7_12_audit.py` and verify it fails or logs structurally sound results.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/safe_pack/task1_results.md:5:2. **Over-globbing hidden dirs:** Added safe guards to prevent over-globbing hidden directory contents. Directories explicitly named `.git`, `.venv`, and `.venv_spec_graph` are aggressively ignored, alongside any child objects with relative folder paths beginning with `.`.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/safe_pack/task2_results.md:16:Running `./.venv_spec_graph/bin/python system_v4/probes/sim_axis_7_12_audit.py` resulted in structurally sound outputs, proving the contract successfully. Below are the values extracted:
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/safe_pack/task_1_provenance.md:11:4. Run the ingestion explicitly: `./.venv_spec_graph/bin/python system_v4/skills/graph_intake/multi_repo_ingestor.py` and verify `system_v4/a2_state/graphs/full_stack_provenance_graph.json` contains valid data.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_PACKET__CURRENT__v1.json:8:  "preferred_interpreter": ".venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.json:325:      "path": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/EGGLOG_V13_WORKING_EXAMPLES__v1.md:5:> **venv**: `.venv_spec_graph`  
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json:347:  "preferred_interpreter": ".venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_PACKET__CURRENT__v1.json:8:  "preferred_interpreter": ".venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PACKAGE_INVENTORY__v1.md:1:# Package Inventory: .venv_spec_graph
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PACKAGE_INVENTORY__v1.md:3:**Environment**: `/home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph`
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PACKAGE_INVENTORY__v1.md:6:The `.venv_spec_graph` environment contains **232** total packages. It represents a heavy-duty research and verification stack, incorporating advanced topological analysis, formal verification (SMT), and machine learning (GNN).
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PHASE1_TOOL_ADOPTION_FIRST_EXPERIMENTS__v1.json:4:  "environment": "/home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_PACKET__CURRENT__v1.json:13:  "preferred_interpreter": ".venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PHASE1_TOOL_ADOPTION_AUDIT_REPORT__v1.md:7:- **venv**: `.venv_spec_graph`
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json:9:  "preferred_interpreter": ".venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/MUTMUT_RESULTS__nested_graph_builder__v1.md:7:- **Environment**: macOS, `.venv_spec_graph`
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/PHASE1_PHASE2_COMBINED_AUDIT__v1.json:4:  "environment": "/home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python3",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:7:- Activate: source .venv_spec_graph/bin/activate
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:23:Activate .venv_spec_graph.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:42:Activate .venv_spec_graph.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:65:Activate .venv_spec_graph.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:88:Activate .venv_spec_graph. egglog 13.0.1 is installed.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:108:Activate .venv_spec_graph. PySMT 0.9.6, z3-solver 4.16.0, cvc5 1.3.3 installed.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:130:Activate .venv_spec_graph. dotmotif 0.14.0 is installed.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:160:Activate .venv_spec_graph. GUDHI 3.11.0, leidenalg 0.11.0 installed.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:180:Activate .venv_spec_graph. leidenalg installed.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:198:Activate .venv_spec_graph.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:222:Activate .venv_spec_graph.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:299:Activate .venv_spec_graph.
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md:301:1. Run: pip freeze > system_v4/a2_state/audit_logs/PIP_FREEZE__venv_spec_graph__2026_03_22.txt
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.json:98:  "preferred_interpreter": ".venv_spec_graph/bin/python",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/CROSS_SOLVER_VERIFICATION_REPORT__v1.md:6:- **interpreter**: `.venv_spec_graph`
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.md:66:- preferred sidecar interpreter: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python`
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/DVC_SETUP_REPORT__v1.md:6:**Venv**: `.venv_spec_graph`
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/full_stack_ingestion_manifest.json:22:      ".venv_spec_graph",
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/nested_graph_builder.py:93:PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/clifford_edge_semantics_audit.py:29:PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/qit_graph_stack_runtime.py:71:PREFERRED_INTERPRETER = REPO_ROOT / ".venv_spec_graph" / "bin" / "python"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/graph_intake/multi_repo_ingestor.py:110:                                if set(file_path.parts) & {".git", ".venv", ".venv_spec_graph"}:
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/toponetx_projection_adapter_audit.py:27:PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"
/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/pyg_heterograph_projection_audit.py:31:PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"
```

## 9. Meaning of the current status
Current state is not just installed vs missing. There are at least five meaningful statuses:
- `installed_and_importable`
- `installed_but_not_wired`
- `wired_but_broken`
- `missing_under_canonical_interpreter`
- `present_in_legacy_env_only`

## 10. Immediate next follow-up
The next better companion doc after this one should classify tools into:
- installed and actively used
- installed but not wired
- wired but broken
- missing but justified
- installed but not justified / later only