# loop_runner — Grok+Opus+Runner harness with frozen-manifest goal-stability

Codex's compiler-pipeline architecture. Roles:

| Role | Owner | Files |
|---|---|---|
| Acceptance (hard pass/fail) | Runner | `runner.py`, `contracts/phase_*.py` |
| Truth (test design + diagnosis) | Opus | `prompts/auditor_prompt.md` (hidden), `prompts/teacher_prompt.md` |
| Generation (implementation only) | Grok | `candidates/candidate_*.py` |

## Core invariants

1. **Hidden harness.** Grok sees only `prompts/public_api_contract.md`. The phase
   contracts in `contracts/` are hidden — Grok learns the math spec, not the
   regex. Numeric thresholds and pass criteria live in the contracts; the public
   contract describes only the math intent.
2. **Function-call testing.** The runner imports the candidate as a Python module
   and calls its functions. It does NOT parse stdout. Print whatever you want
   for debugging — has no effect on pass/fail.
3. **Goal-stability enforced by frozen manifest.** Each run writes
   `_frozen_manifest.json` recording SHA-256 of the runner, candidate, and every
   phase contract, plus command, cwd, git HEAD/branch/dirty, python version. A
   passing phase in one run is only equivalent to a passing phase in another
   run when all relevant hashes match. The runner compares against the most
   recent prior manifest and reports drift before running phases.
4. **Side-quest fencing.** Every receipt declares `classification:
   "side_quest_only"`, `promotion_allowed: false`, `admission_scope:
   "noncanonical_exploration"`, plus `phase_file_sha256`, `candidate_sha256`,
   and a pointer to the `frozen_manifest`. The 10-field receipt schema matches
   canonical sims structurally, but the fence prevents accidental admission.
5. **Phase-aware sanitized Teacher prompts.** `loop_driver.py` maps the
   failing phase id to a human-readable name (`PHASE_HUMAN_NAMES`) and strips
   raw check ids + audit thresholds (`_sanitize_failure_list`,
   `_sanitize_failure_msg`) before sending diagnoses to Grok. The auditor's
   numeric thresholds and check ids never appear in Grok's input.

## Layout

```
loop_runner/
├── runner.py                       Main orchestrator. Frozen manifest + drift check + per-phase receipts.
├── receipts.py                     10-field receipt builder with side-quest fence + provenance hashing
├── loop_driver.py                  Full Grok+Opus+Runner loop with phase-aware sanitized prompts
├── contracts/                      Phase tests (hidden from Grok). 49 contracts as of 2026-05-16.
│   ├── phase_00_smoke.py           Importability + function existence + return types
│   ├── phase_01_axioms.py          M-equivalence + finitude + non-commutation
│   └── phase_NN_*.py               (43 more contracts; see contracts/ for the full set)
├── prompts/
│   ├── public_api_contract.md      Public API spec shown to Grok (numeric thresholds stripped)
│   ├── auditor_prompt.md           Hidden — Opus's diagnostic template
│   └── teacher_prompt.md           Sent to Grok — patch request shape (phase-aware, sanitized)
├── research_notes/                 Carrier-scaling probes + frozen-falsifier docs + retrospective
└── receipts/                       Per-run receipt directories
    └── <run_id>/
        ├── _frozen_manifest.json   Runner/candidate/phase SHAs + command + git state
        ├── _summary.json           Run-level pass/fail + drift report
        └── phase_<id>_results.json Per-phase receipt with provenance fields
```

## Usage

```bash
cd /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/grok_sim
python loop_runner/runner.py --candidate candidates/candidate_iter_02_20260513T092900Z.py
```

With phase filter:
```bash
python loop_runner/runner.py --candidate candidates/candidate_iter_02_20260513T092900Z.py --phases 00_smoke,01_axioms
```

Full loop with Grok generation (requires `XAI_API_KEY`):
```bash
python loop_runner/loop_driver.py --candidate candidates/candidate_iter_02_20260513T092900Z.py --max-iters 4
```

## Current state (as of 2026-05-13)

- **49 phase contracts** in `contracts/` (Phase 00-47 + Phase 98 prime resonance)
- **43 phases passing** + **3 frozen falsifiers** (Phase 32 axis-cliff bound, Phase 42
  factorization-at-scale, Phase 44 closed-system denoise) on
  `candidates/candidate_iter_02_20260513T092900Z.py`
- **Six capability primitives**: `prime_resonance`, `classify_state`, `process_state`,
  `explain_state`, `signature_to_density_matrix`, `denoise_pipeline`,
  `project_to_manifold`
- **Two verified chains**: prime → classifier (92% prime sensitivity at n=2..100);
  noisy → explain → denoise (in-distribution)
- **Three carrier-scaling probes** at 8-qubit (256-dim) — see `research_notes/`
- See `research_notes/SESSION_RETROSPECTIVE_2026_05_13.md` and
  `research_notes/CAPABILITY_AND_BOUNDS_MATRIX.md` for the operational envelope

## What the runner returns (exit codes)

- `0` — all phases passed
- `1` — at least one phase failed (runner stopped at first failure)
- `2` — candidate file not found

## Goal-stability via frozen manifest

Goal-stability is enforced at the receipt level, not by trust:

1. Each run hashes the runner, candidate, and every selected phase contract,
   writes `_frozen_manifest.json` BEFORE running any phase.
2. Receipts reference the manifest path + carry their own
   `phase_file_sha256`, `candidate_sha256`.
3. The runner compares against the most recent prior manifest and reports drift
   (in `_summary.json` under `drift_vs_prior`) before phases run.

If a contract changes between runs, that change shows up explicitly. A "passing
phase" with a different `phase_file_sha256` than a prior "passing phase" is NOT
equivalent — the receipt carries the evidence.

## Why this loop is harder to game than the old one

The old `grok_opus_loop_v*.py` family had four structural failure modes; this
loop fixes all four:

1. **Stdout scraping** → Grok learned to print the right string regardless of math.
   Fix: function-call testing only; stdout has no effect on pass/fail.
2. **Audit growth (goalpost-moving)** → new requirements added mid-iteration.
   Fix: phase contracts are frozen by SHA-256 hash; new requirements only via
   new phase numbers.
3. **Whole-engine rewrites each iter** → regressions on previously-working pieces.
   Fix: phased iteration; only the failing function gets touched; passing
   phases run as regression checks each iter.
4. **Audit-internal language leaking into Grok's prompts** → Grok learns to
   satisfy regexes instead of math. Fix: phase-aware sanitized Teacher prompts
   strip raw check ids and numeric thresholds before any prompt is built.

## Promotion gating

This harness is `side_quest_only`. To promote to canonical, the candidate would
need: SIM_TEMPLATE conformance, TOOL_MANIFEST, classification: "canonical",
at least one load-bearing tool, and external replication. None of these are in
scope for the side-quest harness.
