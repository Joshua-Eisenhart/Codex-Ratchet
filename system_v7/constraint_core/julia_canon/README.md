# Julia-owned exceptional algebra canon

This directory repairs a concrete ownership gap in the 130 bundle. The project architecture assigns algebra definitions, multiplication conventions, bracket order, proof tags, and structural basin labels to Julia. Earlier ZIPs contained Julia engine wrappers but no owned exceptional-algebra source or export contract.

## Ownership boundary

- `src/ExceptionalAlgebraCanon.jl` is the source owner for the Fano orientation, octonion product, associator, commutator order, Malcev/Jacobi primitives, Albert `J3(O)` representation, Jordan product, quadratic representation, proof tags, and structural label registry.
- `scripts/export_canon.jl` is the Julia-owned export path.
- `artifacts/` contains the explicit finite tables and registries consumed by other engines.
- `validate_exceptional_canon.py` independently checks the finite table, norm composition, alternativity, an exact nonassociative witness, the Malcev identity, and agreement with the existing J3(O) receipt.

## Current execution status

The build container used for bundle 131 did not contain a Julia runtime. Therefore the source was authored and the deterministic table was cross-validated by an independent Python mirror, but a local Julia replay was **not** fabricated. The machine status is:

`JULIA_SOURCE_AUTHORED__PYTHON_MIRROR_CROSS_VALIDATED__LOCAL_JULIA_REPLAY_BLOCKED_RUNTIME_ABSENT`

On a machine with Julia 1.10 or newer, run:

```bash
julia --project=julia_canon julia_canon/scripts/export_canon.jl
python julia_canon/validate_exceptional_canon.py --run-julia
```

That overwrites the mirror exports with Julia-produced exports and writes a Julia execution receipt. Until that replay occurs, callers must preserve the blocked status. In either state, algebra export success does **not** admit octonions, Albert geometry, or any exceptional structure into Ratchet canon.

Plain-language guard: successful export does not admit octonions.
