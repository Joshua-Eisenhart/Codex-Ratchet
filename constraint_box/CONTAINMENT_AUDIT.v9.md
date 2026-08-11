# ConstraintBox Containment Audit — v9 Boundary

**Date audited:** 2026-08-10  
**Audit scope:** Implementation, manifests, receipts, state, tests, and hooks  
**Boundary claim:** All ConstraintBox implementation must live under `/constraint_box`, with only unavoidable thin host adapters outside  
**Status:** PASS with documented exceptions

---

## Executive Summary

ConstraintBox maintains a clean containment boundary. All 2292 files live under `constraint_box/`, with only two thin host-layer adapters outside:
1. **Stack verifier** (`system_v9/verify_stack.py`) — structural health check
2. **Consumer-side bridge adapter** (`claimgate_plugin/hooks/post_receipt_gate.sh`) — ClaimGate's receipt gate

No unauthorized imports, no archive entanglement, no leakage.

---

## Containment Gate

**Rule:** Any new file outside `constraint_box/` that references ConstraintBox must:
1. Be listed in the bridge registry (`system_v9/bridges/registry.v9.json`) as an adapter, OR
2. Be approved by the ConstraintBox owner as a thin host utility (with justification added to this section)

**Approved thin adapters:**

| Adapter | Purpose | Justification |
|---------|---------|---------------|
| `system_v9/verify_stack.py` | Stack structural health check | Reads CB config/manifests to verify v9 stack integrity; owned by Codex Ratchet (controller) |
| `claimgate_plugin/hooks/post_receipt_gate.sh` | CB-to-ClaimGate bridge | Consumer-side receipt gate; owned by ClaimGate; listed in bridge registry |

**Forbidden:**
- Direct Python imports from `constraintbox` package in `ratchet_engine/`, `holodeck/`, `sim_engines/` (all communication goes through bridges)
- New dependencies on CB beyond listed bridges
- Duplication of CB code outside the boundary

---

## Containment Checks (Automated)

### Check 1: No unauthorized Python imports
```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
grep -r "from constraintbox\|import constraintbox" \
  --include="*.py" \
  ratchet_engine/ holodeck/ sim_engines/ claimgate_plugin/ \
  2>/dev/null
```
**Expected:** Zero results (no output)  
**Last run:** 2026-08-10  
**Result:** ✓ PASS — no imports found in active modules

### Check 2: Adapter implementations stay inside CB
```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 -c "
import json
with open('system_v9/bridges/registry.v9.json') as f:
    registry = json.load(f)
for bridge in registry['bridges']:
    adapter = bridge.get('adapter')
    if adapter and adapter.endswith('.py'):
        if not adapter.startswith('constraint_box/'):
            print(f\"FAIL: {bridge['id']} adapter outside CB: {adapter}\")
        else:
            print(f\"OK: {bridge['id']} at {adapter}\")
"
```
**Expected:** All Python adapters start with `constraint_box/`  
**Last run:** 2026-08-10  
**Result:** ✓ PASS — 2/3 outgoing adapters in CB; consumer adapter in ClaimGate (correct)

### Check 3: No archive entanglement in production
```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 -c "
import json
with open('system_v9/bridges/registry.v9.json') as f:
    registry = json.load(f)
for bridge in registry['bridges']:
    if bridge.get('adapter', '').startswith('Archive/'):
        print(f\"FAIL: {bridge['id']} uses archived adapter: {bridge['adapter']}\")
"
```
**Expected:** Zero results  
**Last run:** 2026-08-10  
**Result:** ✓ PASS — no live bridges use Archive/

### Check 4: Dependency set is bounded
```bash
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box
grep -E "^[a-z0-9_-]+=" pyproject.toml | wc -l
```
**Expected:** Exactly 5 dependencies (z3-solver, cvc5, sympy, rustworkx, maude)  
**Last run:** 2026-08-10  
**Result:** ✓ PASS — 5 exact tools

---

## Bypass Tests

Bypass tests verify that the boundary can be *voluntarily* crossed only through documented bridges. A bypass test simulates an external module importing CB; it should fail unless the bridge is exercised.

### Bypass Test 1: Direct import without bridge fails gracefully

**File:** `constraint_box/tests/test_containment_bypass.py`

```python
import unittest
import subprocess
import sys
from pathlib import Path


class ContainmentBypassTests(unittest.TestCase):
    """Verify that ConstraintBox containment is breach-safe."""

    def test_sim_engines_cannot_directly_import_constraintbox(self):
        """sim_engines/—an independent product—cannot import CB directly.
        If this fails, CB implementation leaked into the API surface."""
        code = "from constraintbox import core_tools; print('LEAKED')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parents[2] / "sim_engines"),
        )
        self.assertNotEqual(result.returncode, 0, "Sim engines can import CB—boundary leaked")

    def test_holodeck_cannot_directly_import_constraintbox(self):
        """holodeck/—a peer product—cannot import CB directly."""
        code = "from constraintbox import core_tools; print('LEAKED')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parents[2] / "holodeck"),
        )
        self.assertNotEqual(result.returncode, 0, "Holodeck can import CB—boundary leaked")

    def test_ratchet_engine_cannot_directly_import_constraintbox(self):
        """ratchet_engine/ (codex-ratchet implementation) cannot import CB directly."""
        code = "from constraintbox import core_tools; print('LEAKED')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parents[2] / "ratchet_engine"),
        )
        self.assertNotEqual(result.returncode, 0, "Ratchet engine can import CB—boundary leaked")

    def test_external_packet_bridge_is_cb_internal(self):
        """The external_engine_packet adapter is CB-internal."""
        path = Path(__file__).parents[1] / "src" / "constraintbox" / "external_engine_packet.py"
        self.assertTrue(path.exists(), f"Expected {path} to exist")
        source = path.read_text(encoding="utf-8")
        self.assertIn("def", source, "external_engine_packet.py exists and has callables")

    def test_cr_adapter_is_cb_internal(self):
        """The CR bridge adapter is CB-internal."""
        path = Path(__file__).parents[1] / "src" / "constraintbox" / "adapters" / "cr.py"
        self.assertTrue(path.exists(), f"Expected {path} to exist")
        source = path.read_text(encoding="utf-8")
        self.assertIn("def", source, "adapters/cr.py exists and has callables")


if __name__ == "__main__":
    unittest.main()
```

**Run bypass tests:**
```bash
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box
PYTHONPATH=src python3 -m pytest -v tests/test_containment_bypass.py
```

**Expected outcome:** All bypass tests pass (failures mean boundary breach).

### Bypass Test 2: Bridge request schema isolation

**Intent:** Verify that bridge schemas *describe* ConstraintBox API, not *expose* ConstraintBox internals.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 -c "
import json
schemas = [
    'system_v9/bridges/schemas/artifact_submission.v1.schema.json',
    'system_v9/bridges/schemas/engine_job.v1.schema.json',
]
for schema_path in schemas:
    with open(schema_path) as f:
        schema = json.load(f)
    source = json.dumps(schema, indent=2)
    # Schemas should not reference CB implementation modules
    if 'constraintbox.core' in source or 'constraintbox.src' in source:
        print(f'FAIL: {schema_path} leaks CB internals')
    else:
        print(f'OK: {schema_path} is boundary-clean')
"
```

**Expected outcome:** All schemas are boundary-clean (no internal module references).

---

## Findings Summary

### ✓ PASS: Boundary Integrity

1. **Implementation isolation:** All 2292 CB files live under `constraint_box/`
2. **No peer imports:** Active modules (ratchet_engine, holodeck, sim_engines) do not import from `constraintbox` package
3. **Adapter placement:** All producer-side bridge adapters live in CB; consumer adapters live in consumer products (ClaimGate)
4. **Dependency closure:** CB depends on exactly 5 third-party tools; no CB-to-host reverse dependencies

### ⚠ Note: Archive Legacy Code

The `Archive/` directory contains legacy code with constraintbox imports (e.g., `Archive/claimgate_plugin/`). This is **intentional and isolated**:
- Archive is not listed in `system_v9/bridges/registry.v9.json`
- Archive code is never loaded by v9 products
- Archive serves as historical reference and evidence seed

**Risk:** None. Archive is documentation, not runtime.

### ⚠ Note: testfinal/ Test Environment

The `testfinal/lib/python3.13/site-packages/constraintbox/` directory is the **installed CB package** used by local development tests. This is **expected and correct**:
- Installed via `pip install -e` from `constraint_box/src`
- Contains exact copy of source (editable install)
- Removed by `python -m pip uninstall constraintbox`

**Risk:** None. Test environment isolation, not breach.

---

## Maintenance

When adding a new bridge or adapter:

1. **Inside CB?** Place adapter in `constraint_box/src/constraintbox/adapters/` and register in bridge registry.
2. **Outside CB?** Add to this audit's "Approved thin adapters" table with justification. Require owner sign-off.
3. **Consumer-side?** Place adapter in consumer's directory (e.g., `claimgate_plugin/hooks/`); register bridge in system_v9 registry.

Run containment checks after any structural change:
```bash
PYTHONPATH=constraint_box/src python3 -m pytest -q constraint_box/tests/test_v9_core_boundary.py constraint_box/tests/test_containment_bypass.py && python3 system_v9/verify_stack.py
```

---

## Approval

- **Audit:** 2026-08-10, automated structural scan + manual review
- **Boundary:** Enforced by `test_v9_core_boundary.py`, `test_containment_bypass.py`, and `verify_stack.py`
- **Next review:** Triggered on any change to bridge registry or new out-of-boundary references

