# TOOLS, SOLVERS, LIBRARIES & REPOS
_Regenerated 2026-07-12 03:00 UTC. Versions read from the live environment._

## Solver & library versions (this environment)
- **numpy**: 2.3.4
- **scipy**: 1.17.1
- **sympy**: 1.14.0
- **sklearn**: 1.8.0
- **pysindy**: 2.1.0
- **z3**: 4.16.0
- **cvc5**: 1.3.3
- **mpmath**: 1.3.0

Python: 3.13.6. Env: constraintcore (conda). Numba cache: /tmp/numba_cache.

## Dependency contract
THREE-ENGINE DEPENDENCY CONTRACT (load-bearing gates): z3 AND cvc5 must agree on the same
structural claim with erased controls that flip it; numpy/scipy/mpmath are CONTROL-LANE only, never load-bearing; at
least one tool outside the array baseline must gate a verdict. Sims carry NO jargon -- pure real math and structure;
a rosetta layer maps earned structure to labels afterward.

## Repos (source of truth)
- **codex-ratchet repo** (system_v7/constraint_core/): the v7 sim runner + working docs. Provenance and live code, not a truth database.
- **Wiki** (Joshua-Eisenhart/Joshua-Eisenhart-Wiki, projects/codex-ratchet/): synced reports, ledger, changelog, sims.
- **leviathan** (github.com/lev-os/leviathan): a CS-version reference of many concepts; REFERENCE not canon.
- **LevRatchet** (Joshua-Eisenhart/LevRatchet): private convergence/coordination repo; role must be earned per claim.
- **Sofia** (Kingly-Agency/Sofia): adjacent private agent/runtime work; relevance must be demonstrated.
- **Leviathan-Arbitrage** (Joshua-Eisenhart/Leviathan-Arbitrage): public application repo, not foundations authority.
- This bundle mirrors the audit-engine sim set; the codex app consumes these zips + runs its own sims.
- `GITHUB_REPO_CONTEXT_2026-07-10.md` records the connector snapshot and the local-vs-published boundary.

## How the pieces run
- `run_all.py` -- the full harness (each sim is a subprocess; a row PASSES on a 'contains' string match). No jargon in sims.
- `sims_and_scripts/` -- 196 python sim files (some are withdrawn scaffolds, not registered).
- `panel_adversarial_review.py` -- cross-family LLM panel (Gemini/Grok/Qwen/GLM) as an ADVISORY adversarial reviewer; never gates.
- `MODEL_LAYER_LEDGER.md` / `CHANGELOG_HARDENING.md` -- append-only rung record + hardening log.
