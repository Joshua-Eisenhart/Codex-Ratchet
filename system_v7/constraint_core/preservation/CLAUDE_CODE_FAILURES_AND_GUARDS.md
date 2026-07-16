# Claude Code failures and executable guards

This file answers why the recent mathematics disappeared from Claude Code's apparent project state and makes the same failure harder to repeat.

## Failure 1 — registration was mistaken for existence

`generate_bundle_docs.py` derived its mathematics inventory only from scripts registered in `run_all.py`. The tree contained 190 top-level simulation scripts, but only 144 matched that registry parser. The 46 unregistered scripts included the newest Jordan, Albert, octonion, Malcev, Spin(9)/OP2, field-of-engines, and attractor-basin work. They survived as files but became dark to the generated front door.

**Guard:** `reports/SIM_REGISTRATION_LEDGER.json` inventories all 190 scripts and records registration separately from result and promotion status. `preservation/verify_preservation.py` fails if the 190/144/46 partition or ledger changes without explicit regeneration.

## Failure 2 — category output was truncated

The old generated math inventory printed at most 12 filenames per category and had no attractor-basin category. This created a false sense of completeness while hiding exactly the work the user was asking about.

**Guard:** the v0.7 generator scans all scripts, has dedicated exceptional/nonassociative and basin reports, and does not truncate complete machine ledgers.

## Failure 3 — physical preservation was mistaken for surfaced memory

Most 129 mathematics remained byte-present in 130, but it was reduced to a couple of sentences under an `L15+` umbrella. A file that an agent is not instructed to find is not functional project memory.

**Guard:** mandatory read order begins with dedicated reports. The preservation manifest names those reports as required surfaces and hashes every non-cache file.

## Failure 4 — four artifacts were silently dropped

The 130 archive omitted three external-review documents and one field-pair result that were present in 127.

**Guard:** all four are restored byte-for-byte. Their 127 hashes are fixed in the manifest and verified on every lint.

## Failure 5 — green scripts were allowed to sound like canon

Earlier summaries blurred “the script ran,” “a finite fixture passes,” “this branch is constructible,” and “the Ratchet provisionally admitted this object.” This is the project’s central category error.

**Guard:** every report separates source, local execution, finite observation, constructibility, exclusion, and Ratchet admission. Registration and green output never self-promote. The wiki and this ZIP are proposal/evidence memory, not canon.

## Failure 6 — an LLM summary substituted for an execution receipt

Claims were made about manifold ratcheting without showing candidate populations, controls, gradients, MSS fronts, or layer-by-layer state. A later pasted report also described missing evidence as if it had been audited.

**Guard:** no summary may change project state unless it points to a shipped, parseable receipt. Missing source is `CLAIM_ONLY__SOURCE_MISSING`, never “clean.” The actual manifold report remains separate and says both what ran and what was admitted.

## Failure 7 — Julia ownership was asserted but not materialized

The architecture says Julia owns algebraic definitions, multiplication tables, bracket order, proof tags, and basin labels. The 130 ZIP had Julia engine wrappers but no exceptional-algebra source or owned export contract.

**Guard:** `julia_canon/` now contains the source module, export program, Project file, explicit Fano convention, proof tags, basin-label registry, and a Python cross-validator. Because Julia is absent in the current build container, the status is explicitly `JULIA_SOURCE_AUTHORED__LOCAL_REPLAY_BLOCKED_RUNTIME_ABSENT`. No Julia run is fabricated.

## Mandatory startup protocol for Claude Code

A missing source is not a clean audit. It is a blocked claim boundary.

1. Run `python preservation/verify_preservation.py`.
2. Run `python ratchet/bundle_ratchet_lint.py`.
3. Read the preservation index, simulation ledger, exceptional report, basin report, and actual manifold report in that order.
4. For every asserted state, cite the exact receipt and distinguish execution status from admission status.
5. Search all scripts and receipts; never infer absence from `run_all.py`.
6. Treat rung ordering, substeps, objects, and proposed mathematics as searchable hypotheses unless an admission receipt says otherwise.
7. If a required source/runtime is missing, stop the claim—not the exploration—and record the blocked replay honestly.
