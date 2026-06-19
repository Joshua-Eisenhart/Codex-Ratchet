# BUILD CARD - engine_64_stage_full_run_v0

Original card copied into this packet:

```text
# BUILD CARD - engine_64_stage_full_run_v0 (the engines through ALL 64 stages, one computed run)
You are codex2 (xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build in system_v6/sims/engine_64_stage_full_run_v0/ (file-disjoint). NO git add/commit. Card into build_card.md; boundary helper FULLY; the codex binds.
Authority: the owner disciplined path ("the engines running through all 64 engine stages") + the Matrix64 structure (the matrix64_mine receipt: 4 strokes (axis1xaxis2) x 4 substages (axis5xaxis6) x 2 directions (axis4) = 32 per engine family, total 64 = 2^6; the eng_64_hexagram julia estate - find + consume by hash); the committed stage-word machinery (the readout automaton, the alternating/paired disciplines); the substage convention's status (UNPINNED - the mining receipt: so THE RUN'S substage transition realization = the committed v2/v3 cyclic convention AS A DECLARED REALIZATION CHOICE, labeled realization-relative per the registration discipline, NEVER source-admitted).
THE OBJECT: ONE engine (Type1-L, then Type2-R) stepped through ALL 64 schedule slots (the 2^6 bit-structure: the 6 axis bits as the slot coordinates per the Matrix64 row) on a pinned finite carrier: per slot the state, the active operator/terrain per the slot's axis bits, the typed ledger entry; the FULL 64-slot trajectory = the first complete engine schedule run; the L-vs-R full-run comparison (the chirality difference over the whole schedule, computed); the slot-coordinate consistency rows (each slot's realized operator family matches its axis-bit coordinates - the Matrix64 structure verified in the run, or divergences reported).
Controls: a shuffled-schedule control (the 64 slots permuted -> the trajectory must differ, N01); a truncated-schedule boundary (32 slots = one engine family); the bit-coordinate erasure control. FENCES: realization-relative (the substage convention declared not admitted); no hexagram/IChing claims (that is the separate match lane); no 64-subsubbasin claims (the basin question is separate and adjudicated). Standard contract.
```

## Packet Shape

- Build path: `system_v6/sims/engine_64_stage_full_run_v0/`
- Runner: `engine_64_stage_full_run_v0.py`
- Shared logic: `engine_64_stage_full_run_v0_common.py`
- Validator: `validate_engine_64_stage_full_run_v0.py`
- Result: `results/engine_64_stage_full_run_v0_results.json`

## Claimed Scope

This is a finite, realization-relative schedule trajectory on a pinned Bloch-vector carrier.

It computes:

- 64 schedule slots in the declared order `Type1-L` then `Type2-R`;
- 32 slots per engine family;
- per-slot axis bits, active terrain, active operator family, precedence, state before/after, and typed ledger entry;
- Type1-L vs Type2-R independent half-run comparison from the same pinned initial state;
- shuffled-schedule, truncated-schedule, and bit-coordinate erasure controls;
- z3/cvc5 structural gates over computed coordinate counts and controls.

## Fences

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `realization_relative_only=true`
- `substage_convention.source_admitted=false`
- no I Ching / match-lane claims
- no basin, subbasin, or 64-subsubbasin claim
- no canonical source admission of the cyclic substage convention

## Boundary Helper

The packet uses `scripts/builder_audit_boundary.py` as a load-bearing boundary gate.

Builder output must not author `audit_verdict.md`. The validator calls `builder_audit_boundary_errors(...)` and the result carries:

- `no_builder_audit_verdict=true`
- `no_builder_audit_verdict_envelope_gate=true`
- `TOOL_MANIFEST.builder_audit_boundary.used=true`
- `TOOL_INTEGRATION_DEPTH.builder_audit_boundary=load_bearing`

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/engine_64_stage_full_run_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_64_stage_full_run_v0/validate_engine_64_stage_full_run_v0.py
```
