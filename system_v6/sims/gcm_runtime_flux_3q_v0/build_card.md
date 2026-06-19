# gcm_runtime_flux_3q_v0 Build Card

Declared surface: layer 24 (runtime flux) | integrated-onto-the-carve | 3Q.

This packet builds the first runtime/QIT flux computation on the audited 3Q GCM attachment surface, consuming `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5` with registry body hash `623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0`.

Currents:

- `J_cut`: stepwise delta mutual information across `A|BC`, `B|AC`, and `C|AB`.
- `J_ent`: stepwise delta negativity and log-negativity across the same 3Q cuts.
- `J_chi`: GNVW chirality-current seed from the committed 2Q runner, lifted only as a 3Q survivor orientation row: `L=-2`, `R=+2`.

Controls include static no-evolution, time reversal, scrambled dynamics, carve erasure, and a product-control subset. The product-control subset is deliberately named: the full product lift is not claimed to have zero current under the entangling local update.

Fences: `scratch_diagnostic`; carrier-and-pins-relative; computed transport quantities on this realization, not admitted invariants; not engine admission; not physics; not geometric Hopf flux. NO git add/commit.
