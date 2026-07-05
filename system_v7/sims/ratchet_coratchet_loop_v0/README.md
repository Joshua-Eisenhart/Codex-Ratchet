# ratchet_coratchet_loop_v0

Scratch diagnostic for a finite co-ratchet tick loop.

The loop uses the audited v3 separation witness module.  Drive/readout/lift-loop
code is implemented separately in the NumPy, JAX, and Julia legs.  Facts are
measured arrays only; lifts are generated from the current quotient cells by
enumerating coarsest proper refinements of one lossy cell.

Classification: scratch_diagnostic.  Promotion allowed: false.
