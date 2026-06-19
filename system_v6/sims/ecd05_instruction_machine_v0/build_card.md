# BUILD CARD - ecd05_instruction_machine_v0

Original card copied into this packet:

```text
# BUILD CARD - ecd05_instruction_machine_v0 (the 64-slot instruction-machine discriminator; gate OPEN per the registry scoreboard)
You are codex2 (high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build in system_v6/sims/ecd05_instruction_machine_v0/ (file-disjoint). NO git add/commit. Card into build_card.md; the boundary helper; the standards codex binds (INCLUDING G.2a: validator/tests delegate to builder_audit_boundary FROM BIRTH).
Authority (READ FIRST): the ECD registry row ECD.05 (engine_capability_differentiators_20260612.md 7c3f4b48d) + SUPPLEMENT 1 (ecd_registry_supplement_1_20260612.md, cba57dbab -- BINDING: the TWO-SIDED fair-baseline contract; both v0 deaths were definitional baselines; the baseline gets a search AND the QIT side gets an equivalent search over its admissible configurations) + the audited 64-run (engine_64_stage_full_run_v0, 23cfa5536 -- the substrate, realization-relative, NO substage semantics) + the fingerprint IDs (eng64_stage_fingerprint_ids_v0, fab7b2253 -- the 16 label-free behavioral components = the channel family).
THE DISCRIMINATOR: can the 64-slot schedule be USED as an instruction machine -- distinct slot subsequences (programs) computing distinct label-free output channels -- at a diversity NO fair classical baseline matches?
- THE QIT SIDE (searched, per the two-sided rule): over admissible slot subsequences/programs of pinned length budget (pin the program space in-card, G7), compute the label-free output-channel table via the SAME fingerprint family (the 16 components); report the computed channel diversity max;
- THE BASELINE SIDE (searched): the strongest classical machine with the same alphabet/step budget -- enumerate or search its program space under the same fingerprint family; report ITS diversity max;
- the discriminator: QIT max vs baseline max, margin computed; EITHER OUTCOME = the result (a death is a registry row);
- realization-relativity fence: all programs run on the SAME pinned realization; no substage-semantics claims; cite the 64-run estate by hash.
Controls: commuting/order-blind collapse; a dropped-half program-space sensitivity row on BOTH sides; no identity leak (fingerprints never read slot labels); the scrambled-schedule regression.
Standard contract: three-engine where scoped, envelope, validator, tests, builder_self_assessment.md. Ceiling: scratch_diagnostic; no universal/Turing/admission claims.
```

## Packet Scope

- Build path: `system_v6/sims/ecd05_instruction_machine_v0/`
- Core logic: `ecd05_instruction_machine_v0_common.py`
- Runner: `ecd05_instruction_machine_v0.py`
- Envelope writer: `ecd05_instruction_machine_v0_envelope.py`
- Validator: `validate_ecd05_instruction_machine_v0.py`
- Tests: `tests/test_ecd05_instruction_machine_v0.py`
- Results:
  - `results/ecd05_instruction_machine_v0_results.json`
  - `results/ecd05_instruction_machine_v0_envelope_results.json`
  - `results/ecd05_instruction_machine_v0_validator_results.json`

## G7 Program-Space Pin

This v0 pins `program_length = 3`.

The QIT side exhaustively searches admissible schedule-order subsequences:

- choose 3 slots from the pinned 64-slot realization;
- preserve the pinned schedule order;
- no repeated slot in one QIT subsequence.

The classical baseline side exhaustively searches a stronger same-alphabet machine:

- the same 64 slot-operation alphabet from the same pinned realization;
- 3 steps;
- arbitrary order;
- repetition allowed.

The comparison is therefore not QIT-max vs baseline-single. Both sides search their admissible program spaces under the same label-free output fingerprint family.

## Fingerprint Family

This packet reuses the `eng64_stage_fingerprint_ids_v0` density-channel family:

- deterministic representative L-Weyl density matrix;
- apply slot/channel operations on the same realization;
- flatten output density matrix to 8 real/imag floats;
- round by `FP_TOL = 1e-7`;
- hash only the numeric vector.

Slot labels, engine labels, direction labels, collapse-pair text, and source-stage label strings are excluded from the fingerprint payload.

## Fences

- `classification = scratch_diagnostic`
- `promotion_allowed = false`
- `formal_admission_allowed = false`
- realization-relative only
- no source-admitted substage semantics
- no Turing/universal computation claim
- no QIT-engine admission
- no physics, basin, 64-subsubbasin, or hexagram claim

## Boundary Helper

The packet uses `scripts/builder_audit_boundary.py` as a load-bearing boundary gate from birth.

Builder output must not author `audit_verdict.md`. The validator calls `builder_audit_boundary_errors(...)`, the tests exercise the validator boundary delegation, and result payloads carry:

- `no_builder_audit_verdict = true`
- `no_builder_audit_verdict_envelope_gate = true`
- `TOOL_MANIFEST.builder_audit_boundary.used = true`
- `TOOL_INTEGRATION_DEPTH.builder_audit_boundary = load_bearing`

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd05_instruction_machine_v0/ecd05_instruction_machine_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd05_instruction_machine_v0/ecd05_instruction_machine_v0_envelope.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd05_instruction_machine_v0/validate_ecd05_instruction_machine_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/ecd05_instruction_machine_v0/tests/test_ecd05_instruction_machine_v0.py
```
