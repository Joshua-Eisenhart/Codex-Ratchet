# gcm_runtime_flux_3q_v1 Build Card

Declared surface: layer 24 (runtime flux) | integrated | 3Q.

DOCTRINE REPAIR: this packet reruns the runtime/QIT flux test without v0's construction tautology. It consumes the audited 3Q GCM attachment surface `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5` with registry body hash `623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0`.

Independent generators:

- L uses the independent Type1-L generator from the committed `engine_64_stage_full_run_v0` schedule source.
- R uses the independent Type2-R generator from the same committed schedule source.
- R is not reverse(L).
- R is not reflection(L).
- The packet computes `max|R - reflect(L)|` and requires it to be nonzero.

Currents:

- `J_cut`: stepwise delta mutual information across `A|BC`, `B|AC`, and `C|AB`.
- `J_ent`: stepwise delta negativity and log-negativity across the same 3Q cuts.
- `J_chi`: GNVW chirality-current seed from the committed 2Q runner, lifted only as a 3Q survivor orientation row: `L=-2`, `R=+2`.

Controls include static no-evolution, time reversal, a separate scrambled L/R pair, carve erasure, load-bearing z3/cvc5 non-identity flips, and a product-control subset. The product-control subset is deliberately named: the full product lift is not claimed to have zero current under engine dynamics.

Fences: `scratch_diagnostic`; carrier-and-pins-relative; independent-engine doctrine test only; computed transport quantities on this realization, not admitted invariants; not engine admission; not physics; not geometric Hopf flux. NO git add/commit.
