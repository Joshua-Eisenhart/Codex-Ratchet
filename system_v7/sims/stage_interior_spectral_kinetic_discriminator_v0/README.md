# Stage-Interior Spectral/Kinetic Discriminator v0

This bounded `scratch_diagnostic` asks whether canonical PyDMD and isolated
deeptime linear VAMP can distinguish two finite `Type2_right` cycle orders on
held-out probes and seeds:

- `Ti > Te > Fi > Fe`
- `Ti > Te > Fe > Fi`

It imports the source eight-slot `Type2_right` schedule and the existing
stage-interior terrain/operator channels. The four operators are a tested input
premise. No four-state latent model is requested: PyDMD chooses numerical rank,
and VAMP runs with `dim=None`.

## Runtime boundary

`build_contract_and_pydmd.py` runs only with canonical PyDMD 2025.8.1 from the
sim-stack interpreter. It writes a hashed JSON/NPZ trajectory contract and its
own receipt. `run_deeptime_vamp.py` runs only with deeptime 0.4.5 from the
isolated interpreter; it verifies and reads that contract, never the PyDMD
receipt or assembled result. `assemble_results.py` verifies contract identity
and combines independent lane verdicts without claiming interpreter parity or
cross-confirmation.

## Gates

Each lane must achieve held-out accuracy at least `0.75` and mean paired margin
at least `0.02`. Temporal shuffle, exact within-block permutation, and full reversal
preserve every held-out trajectory's marginals. Each control must reduce the
absolute accuracy advantage over chance to at most `0.10` and its absolute mean
margin to at most `35%` of the clean mean margin.

Run:

```sh
sh system_v7/sims/stage_interior_spectral_kinetic_discriminator_v0/run_all.sh
```

## Claim ceiling

This packet may discriminate only the two declared finite candidate orders on
the cited generated fixture. It cannot derive four operators, establish a
unique or universal order, admit engines, Axis0, perception, or objects, move a
stage, or promote any result.

The fresh measured outcome is recorded in `RESULTS.md`; both runtime lanes and
the packet validator pass the declared gates.
