# Build Card - ecd07_associative_retrieval_v0

Build in `system_v6/sims/ecd07_associative_retrieval_v0/`. No git add or commit.

## Bottom Line

Build the ECD.07 associative-retrieval discriminator. The live question is whether the committed spinor-network/Hopfield surface pattern family retrieves stored patterns from partial/corrupted cues at an accuracy/capacity the fair searched classical associative class cannot match.

Either outcome is the result. If the searched equal-information classical associative class ties or wins, ECD.07 dies for this carrier, corruption family, and metric.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Read-First Authority

- `system_v6/receipts/engine_capability_differentiators_20260612.md` at `7c3f4b48d`, ECD.07 row.
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`, complete supplement and all five addenda: two-sided search, equal-information parity, fair metrics, bounded deaths.
- `system_v6/receipts/spinor_network_surface_estate_20260611.md`: spinor/Hopfield surface estate and strict missing-object caveats.
- `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md`: v1 floor and v3 partial pre-registered rise.
- `system_v6/sims/spinor_network_surface_v1/audit_verdict.md` at `8c46b87e3`: narrow floor, six spurious attractors in the declared finite abstraction.
- `system_v6/sims/spinor_network_surface_v3/audit_verdict.md` at `b02444162`: partial pre-registered rise and three-pattern extension limits.
- `system_v6/sims/spinor_network_surface_v3/results/spinor_network_surface_v3_envelope_results.json` at `6f8218a8a`: committed surface result consumed by hash.
- `system_v6/receipts/audit_standards_codex_v1.md`: G.2a and no-identity-leak fields bind from birth.

## Binding Contract

1. Witness gates before comparison:
   - storage-nontriviality: both sides must retrieve above chance;
   - information parity: both sides receive the same stored patterns and same corrupted cue, and neither side reads chart cell identity, target labels, row ids, or committed surface structure unavailable to the other.
2. Two-sided search:
   - QIT/surface side searches its admissible retrieval/update variants;
   - classical side searches Hopfield, nearest-neighbor lookup, and trainable classical associative structures from the same stored patterns.
3. Fair metric:
   - compare the full retrieval-accuracy curve across pinned corruption levels;
   - compare capacity before interference using the same threshold;
   - do not pick one favorable point.
4. Controls:
   - spurious-attractor recurrence against the v1 floor's six-row lesson;
   - scrambled-pattern regression;
   - pinned-random base rate;
   - dropped-half cue budget on both sides;
   - no identity leak with `identity_leak_detected`, `identity_leak_excluded_best_accuracy`, and `identity_leak_exclusion_rule`.
5. Deaths are results:
   - `DIES_TIE_v0` or `DIES_CLASSICAL_STRONGER_v0` is a valid close if parity and storage gates pass.

## Files

- `ecd07_associative_retrieval_v0_common.py`: source locks, patterns, corruption family, retrieval policies, controls, SMT relation, result object.
- `ecd07_associative_retrieval_v0_boundary.py`: packet-local G.2a, parity, metric, control, and no-promotion gates.
- `ecd07_associative_retrieval_v0.py`: base result writer.
- `ecd07_associative_retrieval_v0_jax.py`: JAX/tool lane.
- `ecd07_associative_retrieval_v0_pytorch.py`: PyTorch/tool lane.
- `ecd07_associative_retrieval_v0_julia.jl`: Julia strict-carrier lane.
- `ecd07_associative_retrieval_v0_envelope.py`: three-engine envelope builder.
- `validate_ecd07_associative_retrieval_v0.py`: packet validator.
- `tests/test_ecd07_associative_retrieval_v0.py`: regression tests.

## Standard Gates

- G.2a from birth: validator and boundary helper call `builder_audit_boundary_errors(...)`; builder output may not contain a builder-authored audit verdict.
- Three-engine where scoped: `all_three_full_sims` envelope with Julia/JAX/PyTorch lanes, still capped at `scratch_diagnostic`.
- No identity leak: predictors exclude cell identity, row identity, direct target lookup, and output fingerprints.

## Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd07_associative_retrieval_v0/ecd07_associative_retrieval_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd07_associative_retrieval_v0/ecd07_associative_retrieval_v0_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd07_associative_retrieval_v0/ecd07_associative_retrieval_v0_pytorch.py
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/ecd07_associative_retrieval_v0/ecd07_associative_retrieval_v0_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd07_associative_retrieval_v0/ecd07_associative_retrieval_v0_envelope.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd07_associative_retrieval_v0/validate_ecd07_associative_retrieval_v0.py
```

```bash
PYTHONPATH=system_v6/sims/ecd07_associative_retrieval_v0 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/ecd07_associative_retrieval_v0/tests
```
