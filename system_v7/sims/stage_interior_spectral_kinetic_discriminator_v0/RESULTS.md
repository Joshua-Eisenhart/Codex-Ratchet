# Results

Fresh run: **GREEN** (`scratch_diagnostic` only).

Scientific verdict:
`finite_two_order_spectral_kinetic_discrimination_survives_heldout_probes_and_collapses_under_controls`.

The test used 36 held-out labeled trajectories from three seeds, with six
probes per seed for each of the two candidates. Training and held-out seeds are
disjoint. Both candidates use the same pooled four-position weight vector, so
cycle order is the only candidate-varying input.

| Lane | Clean accuracy | Shuffle | Within-block permutation | Reversal | Clean mean margin |
|---|---:|---:|---:|---:|---:|
| PyDMD BOPDMD + HankelDMD | 1.0000 | 0.5000 | 0.5000 | 0.5278 | 16.8348 |
| deeptime linear VAMP | 0.9444 | 0.5000 | 0.5556 | 0.5000 | 1.0868 |

All lane gates passed:

- clean accuracy `>= 0.75`;
- clean mean paired margin `>= 0.02`;
- every control absolute accuracy advantage over chance `<= 0.10`;
- every control absolute mean margin `<= 35%` of its lane's clean margin;
- clean accuracy advantage is positive.

Contract and validation gates also passed: source hashes current, NPZ/manifest
hashes exact, runtime launchers and versions exact, independent lanes bound to
the same contract, no cross-lane receipt reads, controls are exact temporal
permutations preserving per-trajectory marginals, no four-state latent request,
and all admission/promotion/stage flags remain false.

Contract hashes from this run:

- manifest SHA-256: `53b995b58d82a9d704d42e451675902472f15d044614e0b87f8fd5ef89b974b4`
- NPZ SHA-256: `44d5c54b29e3a426523513a501ef4e9c30a09d3599a6a6e7cc8612a973a5d68a`

Machine-readable authority:

- `results/stage_interior_spectral_kinetic_discriminator_v0_results.json`
- `results/stage_interior_spectral_kinetic_discriminator_v0_validation.json`
- `receipts/pydmd_receipt.json`
- `receipts/deeptime_vamp_receipt.json`

This result shows only that the two generated finite candidate orders are
distinguishable by the declared spectral/kinetic procedure under held-out
probes and seeds, with the advantage removed by the controls. It does not select
which order is true outside this fixture, derive four operators, establish a
unique or universal order, admit engines or Axis0, support perception or object
claims, move a stage, or permit promotion.
