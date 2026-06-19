# Builder Self-Assessment: gcm_entropy_family_sweep_v0

## Verdict

`builder_self_verdict`: useful scratch diagnostic, carrier-and-pins-relative.

This is not an independent audit verdict and does not promote the packet beyond
`scratch_diagnostic`.

## What Was Built

- A deterministic entropy-family sweep over the frozen GCM 1Q geometry attach.
- Tables over all 16 survivor lineage IDs.
- Class-level mixed-state entropy rows for all 8 quotient classes.
- Shell-weighted rows over the 5 occupied shell strata.
- Nesting-constraint rows for admissible versus not-yet-enabled entropy families.
- Survival rows showing class/shell separation counts and degeneracy.
- Substrate positive and lineage-free negative controls via `scripts/gcm_substrate_check.py`.
- G.2a builder/audit boundary flags in the envelope.

## Claim Ceiling

The strongest honest claim is:

The frozen GCM 1Q attached carrier admits scalar spectrum entropy-family
computations, and on this object those scalar 1Q families are degenerate across
the survivor/class rows. Shell occupancy is available, but shell-log-surprisal
separates only occupancy-count bins, not the five shell labels.

Blocked stronger claims:

- Axis0 cut entropy.
- Mutual information.
- Conditional entropy.
- Coherent information.
- 2Q+ entanglement measures.
- Runtime engine entropy.
- Bridge/history/transport weighted entropy families.
- Full geometric constraint manifold.

## Fresh Checks Expected

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_entropy_family_sweep_v0/gcm_entropy_family_sweep_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_entropy_family_sweep_v0/validate_gcm_entropy_family_sweep_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_entropy_family_sweep_v0/tests/test_gcm_entropy_family_sweep_v0.py -q
```
