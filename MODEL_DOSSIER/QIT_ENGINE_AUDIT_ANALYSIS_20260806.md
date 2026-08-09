# Adversarial Review: ProcessRatchet

## Question 1: CHEAPEST BYPASS

**Goal**: Work at rung N should be REFUSED without rung N-1's receipt.

**Attack surface**: The `advance()` method is the ONLY public entry point (line 336).
- No public method to append directly to ledger
- No public method to modify receipts
- No way to instantiate AdvanceResult and bypass the decision logic

**Potential bypasses**:
1. Direct ledger manipulation (not prevented by ProcessRatchet, but outside scope)
2. Tampering with the returned AdvanceResult? No, it's frozen (line 171)
3. Call advance() with rung_id not in ladder? Rejected at line 342-343
4. Bypass the decision? Cannot; dual_solve is called at line 467
5. Skip revalidation? No, it runs for every lower rung at lines 390-402
6. Call ledger.append() directly? It's outside ProcessRatchet; not prevented
7. Construct RungSpec with rung_id already in a previous receipt? The ladder is immutable

**Verdict**: No bypass found within ProcessRatchet's public interface. The cheapest attack is OUTSIDE
the module: directly edit the ledger file on disk or call ledger.append() directly. This is NOT a
defect in ProcessRatchet's design; it's a property of the operating environment (file access control).

---

## Question 2: RE_VALIDATION_REAL

**Claim**: Re-validation computes evidence digests FROM BYTES NOW on every advance.

**Trace of _revalidate_lower_rung (lines 282-332)**:

```python
def _revalidate_lower_rung(
    self, rung: RungSpec, record: dict[str, Any]
) -> tuple[str, tuple[tuple[str, str, str, str], ...], dict[str, str]]:
```

Critical line: 324-325:
```python
digest = _sha256_bytes(file_path.read_bytes())
recomputed[path] = digest
```

This READS the file from disk with `file_path.read_bytes()` at line 324, then computes the hash
with _sha256_bytes (which is hashlib.sha256, lines 88-93) RIGHT NOW. It does NOT fetch a stored
digest.

**Comparison to record**: Line 326:
```python
if digest != recorded_evidence[path]:
    drift.append(...)
```

The just-recomputed digest is compared to `recorded_evidence[path]`, which comes from the receipt
on line 303: `recorded_evidence = record.get("evidence")`. These are DIFFERENT values: one is
computed now, one is stored in the receipt.

**Verdict**: RE-VALIDATION IS REAL AND GENUINE. The digest is recomputed from file bytes every time
advance() is called, not pulled from any cache. The comparison is to the recorded value, so a silent
file mutation WILL be detected.

---

## Question 3: CONTROL_B_VALID

**Test** (lines 86-102): test_lower_rung_byte_drift_is_invariant_violation

```python
def test_lower_rung_byte_drift_is_invariant_violation(self) -> None:
    self.assertEqual(
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),)).state,
        ADVANCED,
    )
    (self.root / "e0.json").write_text('{"rung": 0, "edited": true}')  # Line 91: REAL MUTATION
    result = self.ratchet.advance("r1")
    self.assertEqual(result.state, INVARIANT_VIOLATION)
```

Line 91: `write_text()` directly mutates the evidence file on disk.

Evidence file path: self.root / "e0.json" = /tmp/.../e0.json
Setup (line 31): `(self.root / "e0.json").write_text('{"rung": 0}', encoding="utf-8")`

After advance("r0"), the receipt records the sha256 of `{"rung": 0}`.
After line 91, the file contains `{"rung": 0, "edited": true}` (different bytes).
When advance("r1") is called, _revalidate_lower_rung() reads the file fresh (line 324),
gets a different digest, and compares it to the recorded one (line 326).

**Verdict**: CONTROL_B IS ENTIRELY VALID. The mutation is real (file bytes on disk actually change),
the re-reading is real (read_bytes() is called fresh), and the detection is real (digests differ).

---

## Question 4: GATE_ESCAPE

**Claim**: A gate ID can appear in a rung receipt without its operation having run.

**Trace through advance() to gate_executions list construction (lines 551-552)**:

```python
record = {
    ...
    "gate_executions": [
        provided[gate_id].to_dict() for gate_id in target.gate_ids
    ],
    ...
}
```

The list is constructed by iterating target.gate_ids (the declared gates, line 149 in RungSpec).
For each gate_id, it calls `provided[gate_id].to_dict()`.

`provided` is built at lines 344-358:
```python
provided: dict[str, GateExecution] = {}
for execution in gate_executions:
    if not isinstance(execution, GateExecution):
        raise ValueError(...)
    if execution.gate_id not in target.gate_ids:
        raise ValueError(f"execution for undeclared gate: {execution.gate_id}")
    if execution.gate_id in provided:
        raise ValueError(f"duplicate gate execution: {execution.gate_id}")
    provided[execution.gate_id] = execution
```

**The catch**: At line 551-552, the code iterates `target.gate_ids`, but does NOT check if
`provided[gate_id]` exists. It calls `provided[gate_id].to_dict()` unconditionally.

**If a gate_id is in target.gate_ids but NOT in provided**:
- Line 407-410 sets gate_states[gate_id] = "declared_only"
- Line 519-521 checks for missing_gates and returns PARKED
- The code NEVER reaches line 551 in that case (the advance is refused)

**If a gate_id IS in provided**:
- It has a GateExecution with input_sha256, output_sha256, verdict (all required by __post_init__)
- to_dict() is called and produces the record at lines 134-139

**Verdict**: NO GATE ESCAPE. A gate_id can only appear in gate_executions list if it went through
GateExecution.__post_init__() and passed validation. Declared-only gates (no execution) are
caught at line 410-411 and the advance is PARKED before reaching line 551.

---

## Question 5: NEW_DEPENDENCIES

**Module imports** (lines 50-62):
- json (stdlib, stable)
- hashlib (stdlib, stable)
- dataclasses (stdlib, stable)
- datetime (stdlib, stable)
- pathlib (stdlib, stable)
- typing (stdlib, stable)
- **constraintbox.dualsolve** (internal: dual_solve)
- **constraintbox.intake** (internal: canonical_json)
- **constraintbox.ledger** (internal: HashChainLedger)
- **constraintbox.ratchet** (internal: _is_prefix)

**New dependencies**:

1. **dual_solve** (constraintbox.dualsolve)
   - Called at line 467
   - Takes a FiniteConstraintProblem spec (dict-shaped)
   - Returns decision dict with z3/cvc5/enumeration votes
   - Failure mode if absent: ImportError at module load time
   - Failure mode if stale: A backend (z3/cvc5) may emit unexpected output shape

2. **canonical_json** (constraintbox.intake)
   - Called at lines 267, 558
   - Converts dict to canonical JSON bytes
   - Used for hashing the decision spec and ladder prefix
   - Failure mode if absent: ImportError at module load time
   - Failure mode if stale: Hash mismatches with older recorded specs (ledger verification fails)

3. **HashChainLedger** (constraintbox.ledger)
   - Instantiated at __init__ line 216: self.ledger = ledger (passed in)
   - Called at line 363: ledger_ok, ledger_reason = self.ledger.verify()
   - Called at line 562: line_sha256 = self.ledger.append(record)
   - Failure mode if absent: ImportError or error at verify() call
   - Failure mode if stale: verify() may emit unexpected (ok, reason) tuple, or append() may fail

4. **_is_prefix** (constraintbox.ratchet)
   - Called at lines 249, 370
   - Checks if recorded rung sequence is a prefix of declared ladder
   - Failure mode if absent: ImportError at module load time
   - Failure mode if stale: May return wrong result (True when it should be False)
   - Concurrent write risk: If ladder is mutated while _is_prefix runs, result is unreliable

**Concurrent write failure mode** (specific risk):
The ladder passed to __init__ is a tuple (immutable), so the ladder itself cannot be mutated
at runtime. However:
- The evidence files can be mutated between advance() calls (detected by re-validation)
- The ledger file can be mutated externally (detected by verify())
- If canonical_json produces non-deterministic output (e.g., dict ordering), hash mismatches
  will occur on re-validation, incorrectly signaling drift

**Verdict**: Four internal dependencies. All are imported at module load, so absence is caught early.
Staleness in the hash functions (canonical_json, _sha256_bytes) or decision logic (dual_solve) is
the real risk: silent hash mismatches or wrong admissibility decisions.

---

## Summary of Findings

| Question | Answer | Evidence |
|----------|--------|----------|
| 1. Cheapest bypass | No bypass found in ProcessRatchet | advance() is the only entry point; ledger is outside the module |
| 2. Re-validation is real | YES, genuinely recomputes from bytes | line 324: read_bytes() is called every advance |
| 3. Control B is valid | YES, mutation and detection are real | line 91 mutates file, line 324 re-reads, line 326 detects mismatch |
| 4. Gate escape | NO gate can escape | Declared-only gates are caught at line 410-411; all others have GateExecution |
| 5. New dependencies | 4 internal: dual_solve, canonical_json, HashChainLedger, _is_prefix | Failure risk: hash non-determinism, stale backends, ledger verification breaks |

