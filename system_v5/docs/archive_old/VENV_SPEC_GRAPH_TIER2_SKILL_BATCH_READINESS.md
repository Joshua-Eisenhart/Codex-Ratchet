# .venv_spec_graph Tier-2 Skill Batch — Execution-Readiness Audit

Date: 2026-04-04
Produced by: Claude Code (Terminal B)
Canonical interpreter: `/opt/homebrew/bin/python3`
Companion to: `VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md`

---

## Purpose

Determine whether the four tier-2 skills with `PREFERRED_INTERPRETER` strings can be
safely migrated to the canonical interpreter, and identify the smallest safe batching
strategy. This is an audit only — no code has been patched.

---

## Files Audited

| File | PREFERRED_INTERPRETER line | How the string is used |
|---|---|---|
| `nested_graph_builder.py` | 93 | Defined, **never referenced again** — dead metadata |
| `clifford_edge_semantics_audit.py` | 29 | Used in `subprocess.run` at line 100–127 (guarded) |
| `toponetx_projection_adapter_audit.py` | 27 | Appears only in JSON output fields (lines 243, 263) — metadata |
| `pyg_heterograph_projection_audit.py` | 31 | Appears only in JSON output fields (lines 387, 414) — metadata |

---

## Package Availability Under Canonical Interpreter

All packages required by this batch were confirmed importable under `/opt/homebrew/bin/python3`:

```
import torch             ✓
import torch_geometric   ✓
import toponetx          ✓
import clifford          ✓
import kingdon           ✓
import networkx          ✓
```

(Confirmed via live import check. Source: `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md` §1 and direct verification.)

---

## Per-File Readiness Classification

---

### 1. `system_v4/skills/nested_graph_builder.py`

**Classification: Canonical-interpreter ready now**

**Evidence:**
- Top-level imports: stdlib only (`json`, `os`, `time`, `hashlib`, `collections`, `pathlib`, `typing`). No package imports at module level.
- `PREFERRED_INTERPRETER` at line 93 is defined but never referenced anywhere else in the file — it is a dead constant with no execution effect.
- `toponetx` is imported at line 518 via `import toponetx as tnx` directly in the current interpreter, with a graceful `ImportError` fallback returning `{"available": False, "error": ...}`.
- `torch` and `torch_geometric` are imported at lines 569–570 directly in the current interpreter, with a graceful `ImportError` fallback.
- `toponetx`, `torch`, and `torch_geometric` are all importable under canonical interpreter.

**Migration action required:** Update the `PREFERRED_INTERPRETER` string constant for metadata correctness only. No execution path changes needed.

**Risk:** None. The string is never passed to any subprocess or execution path.

---

### 2. `system_v4/skills/clifford_edge_semantics_audit.py`

**Classification: Ready with caveat**

**Evidence:**
- Top-level imports: stdlib only (`json`, `os`, `subprocess`, `time`, `collections`, `pathlib`, `typing`). No package imports at module level.
- `PREFERRED_INTERPRETER` at line 29 IS used in execution:
  - Line 100: `interpreter = root / PREFERRED_INTERPRETER` — constructs a `Path` object
  - Lines 105–127: `if interpreter.exists(): subprocess.run([str(interpreter), "-c", code], ...)`
  - The subprocess runs a Python snippet that imports `clifford` and `kingdon`.
- **Current behavior**: since `.venv_spec_graph/bin/python` does not exist on disk, the `if interpreter.exists()` guard fires, the subprocess is skipped, and the function returns `{"clifford": {"available": False}, "kingdon": {"available": False}}`. The rest of the skill continues running with this fallback.
- **After migration**: updating `PREFERRED_INTERPRETER` to `/opt/homebrew/bin/python3` will cause the subprocess to fire. `clifford` and `kingdon` are both importable under canonical interpreter, so the sidecar proof will run and return live values.

**Migration action required:** Update `PREFERRED_INTERPRETER` to `/opt/homebrew/bin/python3`. After patching, run the skill and confirm the math sidecar returns `{"clifford": {"available": True}, "kingdon": {"available": True}}`.

**Caveat:** This is the only file in the batch where the string change has a real execution effect. The change is safe (canonical interpreter + both packages available) but requires a validation run post-patch.

**Risk:** Low. Current state is graceful fallback, not a crash. Migration enables the sidecar proof to fire correctly.

---

### 3. `system_v4/skills/toponetx_projection_adapter_audit.py`

**Classification: Canonical-interpreter ready now**

**Evidence:**
- Top-level imports: stdlib only.
- `PREFERRED_INTERPRETER` at line 27 appears only in JSON output metadata fields (lines 243 and 263 — embedded in `payload` dicts that are written to disk). It is never passed to any subprocess or execution path.
- `toponetx` is imported at line 65 via `import toponetx as tnx` directly in the current interpreter, inside a try/except that returns `(None, error_string)` on failure.
- `toponetx` is importable under canonical interpreter.

**Migration action required:** Update the `PREFERRED_INTERPRETER` string for metadata accuracy only.

**Risk:** None. The string change has no execution effect.

---

### 4. `system_v4/skills/pyg_heterograph_projection_audit.py`

**Classification: Canonical-interpreter ready now**

**Evidence:**
- Top-level imports: stdlib only (`json`, `time`, `collections`, `pathlib`, `typing`).
- `PREFERRED_INTERPRETER` at line 31 appears only in JSON output metadata fields (lines 387 and 414). Never passed to any subprocess.
- `_try_import_pyg()` (lines 82–87) imports `torch` and `torch_geometric.data.HeteroData` directly in the current interpreter, with a broad `except Exception` fallback.
- `_build_pyg_summary()` (lines 241–243) imports `torch` and `torch_geometric.data.HeteroData` unconditionally — but it is only called at line 371 when `pyg_ok is True` (guarded by the `_try_import_pyg()` check at line 351).
- Both `torch` and `torch_geometric` are importable under canonical interpreter.

**Migration action required:** Update the `PREFERRED_INTERPRETER` string for metadata accuracy only.

**Risk:** None. The string change has no execution effect.

---

## Separate Real Package Blockers From Stale Path Strings

| File | Stale path string | Real package blocker |
|---|---|---|
| `nested_graph_builder.py` | Yes (dead metadata) | None — packages available |
| `clifford_edge_semantics_audit.py` | Yes (used in subprocess guard) | None — `clifford` + `kingdon` available; blocker is the stale path itself |
| `toponetx_projection_adapter_audit.py` | Yes (metadata only) | None — `toponetx` available |
| `pyg_heterograph_projection_audit.py` | Yes (metadata only) | None — `torch` + `torch_geometric` available |

**There are no real package blockers in this batch.** All required packages are installed and importable under the canonical interpreter. The only blocker is the stale `PREFERRED_INTERPRETER` string.

---

## Smallest Safe Batching Strategy

### Batch A — Trivial string update (no execution effect)

Files:
- `nested_graph_builder.py:93`
- `toponetx_projection_adapter_audit.py:27`
- `pyg_heterograph_projection_audit.py:31`

Change: update `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"` to `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` in all three files.

No validation run required — these strings have no execution effect. Change all three in one commit.

### Batch B — Functional string update (subprocess becomes live)

File:
- `clifford_edge_semantics_audit.py:29`

Change: same string update as Batch A.

Validation required: after patching, run the skill and confirm `_verify_math_sidecars` returns `{"clifford": {"available": True}, ...}` rather than the fallback. One short spot-check.

### Recommended order

Batch A first (zero risk, no validation needed), then Batch B (low risk, one validation run). Both can be done in the same handoff if Batch B validation is included in scope.

---

## What This Batch Does Not Unblock

- **Tier 1 files** (`run_formal_geometry_packet.py`, `run_root_emergence_packet.py`, `qit_graph_stack_runtime.py`) remain blocked and are NOT part of this batch. Their package requirements (particularly `cvc5`) are still unmet under canonical interpreter.
- This batch is purely about correcting stale metadata strings and enabling the clifford math sidecar proof. It does not advance the pre-Axis sim ladder.
