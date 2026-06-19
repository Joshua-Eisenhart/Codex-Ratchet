# Hermes Sim Swarm Plan

Created: `2026-06-18T06:29:48Z`

## Status

- Task cards: `40`
- Runnable now: `10`
- Blocked now: `30`
- Claim ceiling: controller plan / receipt summary only; no promotion.

## Runtime seats

- `codex_cli`: `True` — /Users/joshuaeisenhart/.hermes/node/bin/codex
- `codex1_alias`: `False` — missing executable: codex1
- `openrouter`: `False` — OPENROUTER_API_KEY missing
- `cocoindex_repo_mcp`: `True` — /Users/joshuaeisenhart/.local/bin/cocoindex-codex-ratchet-mcp
- `cocoindex_wiki_mcp`: `True` — /Users/joshuaeisenhart/.local/bin/cocoindex-wiki-mcp
- `sim_stack_python`: `True` — /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
- `julia`: `True` — /opt/homebrew/bin/julia

## Target math summaries

### `probe_quotient_fingerprint_floor_v1`
- status: `runs_receipt_present`
- result: `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/probe_quotient_fingerprint_floor_v1/results/probe_quotient_fingerprint_floor_v1_three_engine_results.json`
- claim ceiling: Q=X/~_P is the FORCED floor, trivially well-defined for the exact supplied finite probe table. The z3/cvc5/Z3.jl checks are consistency checks, not load-bearing structural discovery; the load-bearing forced-vs-installed content lives in the cross-type discriminator, not here. No carrier ontology, no rung above 0, no geometry, no physics, no canonical consumer.
- `erased_class_count`: 4
- `erased_classes`: [["x0", "x2"], ["x1"], ["x3"], ["x4", "x5"]]
- `erased_merge_pair`: ["x0", "x2"]
- `full_class_count`: 5
- `full_classes`: [["x0"], ["x1"], ["x2"], ["x3"], ["x4", "x5"]]
- `persistent_pair`: ["x4", "x5"]
- `smt_flip`: {"cvc5_erased_P": null, "cvc5_full_P": null, "real_vs_erased_flip_confirmed": null, "z3_erased_P": null, "z3_full_P": null}
- `solver_role`: supportive consistency only, not structural discovery
- `support`: null

### `forced_or_installed_carrier_comparison_v0`
- status: `runs_receipt_present`
- result: `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/forced_or_installed_carrier_comparison_v0/results/forced_or_installed_carrier_comparison_v0_three_engine_results.json`
- claim ceiling: FORCED here = no second carrier with DIFFERENT (a,b,c) coordinates reproduces the table = COORDINATE-uniqueness vs the reference, NOT isomorphic/ontological uniqueness; no gauge quotient is applied in v0. For these fixtures only: installed means a second density carrier reproduces the measured incomplete probe table. No rho exclusion, no Hilbert exclusion, no Rung-0.5 collapse, no promotion.
- `carrier_type`: qubit_density_2x2_real_coordinates
- `decision_rule`: solver status sat => installed because a valid coordinate-distinct C2 exists; solver status unsat => forced because no such C2 exists; unknown fails the build
- `forced_fixture_statuses`: {"jax_cvc5": "unsat", "jax_z3": "unsat", "julia_z3": "unsat", "pytorch_cvc5": "unsat", "pytorch_z3": "unsat"}
- `installed_C2_witness`: null
- `installed_fixture_statuses`: {"jax_cvc5": "sat", "jax_z3": "sat", "julia_z3": "sat", "pytorch_cvc5": "sat", "pytorch_z3": "sat"}
- `non_isomorphism_predicate`: C2 is coordinate-distinct iff at least one of a,b,c differs from C1; no gauge quotient is applied in v0.
- `reproduce_on_off`: null

### `carrier_type_admissibility_matrix_v0`
- status: `runs_receipt_present`
- result: `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/carrier_type_admissibility_matrix_v0/results/carrier_type_admissibility_matrix_v0_three_engine_results.json`
- claim ceiling: For these finite fixtures only: multiplicity across non-isomorphic carrier categories means the carrier type is installed, while UNSAT rows give fixture-local exclusions. The quotient carrier is a near-trivial null baseline with one bounded free variable per measured probe. The load-bearing carrier-type negative is the order_gap_clean classical_noncontextual exclusion: ZX=1/4 versus XZ=3/8 violates the non-disturbing classical joint. The y_phase real_rebit exclusion is by_construction because a real-symmetric rebit has Y=1/2 identically; it is a boundary/control, not load-bearing. The Luders readout maps encode one chosen measurement geometry, so the clean order-gap exclusion is fixture-local contextuality-flavored evidence under that geometry, not a general contextuality theorem. This does not exclude rho, does not promote beyond scratch_diagnostic, and leaves the Rung-0.5 Boolean/counting fork held.
- `allowed_excluded_summary`: null
- `claim`: For these finite fixtures, solver existence over free per-type carrier variables yields an allowed/excluded matrix. Multiplicity means installed. The load-bearing carrier-type negative is order_gap_clean for classical_noncontextual; y_phase_exclusion for real_rebit is by construction and kept as a boundary/control only.
- `fixtures`: {}
- `known_boundary`: real_rebit Y exclusion is by_construction boundary/control, not load-bearing negative
- `load_bearing_negative`: order_gap_clean excludes classical_noncontextual via non-disturbing joint contradiction, per BUILD_REPORT

## Holes observed

- codex1 seat name requested by prior workflow is not a real executable here; only `codex` CLI is present.
- OpenRouter fanout is blocked in this shell: OPENROUTER_API_KEY missing.
- probe_quotient_fingerprint_floor_v1 runs locally but validate_v7_admission fails gates: ['math-only', 'name-math-correlation', 'two-tier-authority']
- forced_or_installed_carrier_comparison_v0 runs locally but validate_v7_admission fails gates: ['math-only', 'name-math-correlation', 'two-tier-authority']
- carrier_type_admissibility_matrix_v0 runs locally but validate_v7_admission fails gates: ['math-only', 'name-math-correlation', 'two-tier-authority']
- Existing forced-vs-installed v0 proves coordinate-uniqueness inside chosen rho coordinates, not gauge/ontological uniqueness or cross-type foundation closure.
- Actual nesting remains open until an order/bracket/second-layer sim shows a structural SAT/UNSAT flip with stated math and controls.
