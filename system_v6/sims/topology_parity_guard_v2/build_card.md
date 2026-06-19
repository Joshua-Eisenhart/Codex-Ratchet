# Build Card - topology_parity_guard_v2

Status: builder packet, scratch_diagnostic, consumer lane only.

## Boundary

`topology_parity_guard_v2` is the second-certificate consumer for the committed
`fiber_augmented_cover_v2` chain complexes. It has NO new construction freedom:
no new cells, no target Betti fitting, no fresh wrong-gluing cell model, and no
Betti citation from the builder packet.

G.2a is active from birth through `topology_parity_guard_v2_boundary.py` and
the shared helper `scripts/builder_audit_boundary.py`. This packet does not
write an `audit_verdict.md`.

## Authority Read

- `cc2f61b2a`: `fiber_augmented_cover_v2` audited `GENUINE` at its scratch
  ceiling. It commits hash-pinned base and total-space cellular chain complexes
  but explicitly emits no Betti.
- `cc2f61b2a`: audit consumer rule says the guard v2 / Betti lane must consume
  the pinned complexes and must not cite Betti from the builder packet.
- `0207fecaf`: `topology_parity_cell_model_v1` rejected because its
  load-bearing cellular model was packet-introduced and target-Betti-load-bearing.
- v0/v1 preregistered profiles are carried unchanged:
  S3-like `[1,0,0,1]`; product S2xS1 `[1,1,1,1]`.

## Source Pins

Committed v2 base complex:

- counts: `C0=33, C1=92, C2=61`
- chi: `2`
- chain hash: `9d6655a51782305f80409cce0bd42a57329fb14ea19b05c32b95ec36016b883c`
- boundary hashes:
  - `d1=e36e2c77badce28030044b39b8128643928c0f38bf5a9c3f515b31c70536399a`
  - `d2=9d0c2669c4172ded9aa64e3c88dfe54669e1bc1bfbd0d2e193489b9a75a9827b`

Committed v2 total-space complex:

- counts: `C0=99, C1=375, C2=459, C3=183`
- chi: `0`
- chain hash: `38e57e928d722046eb0b734ff76d7a636c05e0f292ca59f97a3a3e0588d12a5c`
- boundary hashes:
  - `d1=305b45cb0c7048f794f892531b1244814e4ee650c339670108ca4ca9c13cb1bf`
  - `d2=6c593b1002dc256b78cd59767b4bc5fc91137a82a87b210b186cc3a11e7dcfef`
  - `d3=ed1dc588e4c3a6a80ed674439bbddd9933d6683f5831c1d55d32438bcd67aac7`

Any hash mismatch is a stop condition.

## Method

1. Run the independent reference gate first with explicit reduced Euler-class
   complexes:
   - S3-like degree `1` must recover `[1,0,0,1]`.
   - S2xS1 degree `0` must recover `[1,1,1,1]`.
2. Load the committed v2 result JSON and verify the pinned hashes, counts, chi,
   `d^2=0`, and builder/consumer fence.
3. Compute integer ranks and Smith normal forms for the committed base and
   total-space boundary matrices.
4. Report homology with torsion, because Betti-only is underpowered.
5. Adjudicate the committed total-space homology against the carried profiles:
   `EARNED`, `FAILED`, or `INSUFFICIENT`.
6. Report zero-shift and wrong-gluing only to the level committed by v2 data.

## Current Builder Finding

The committed total-space chain complex computes:

- Betti: `[1,1,1,1]`
- torsion: none in `H0..H3`
- `d^2=0`

Therefore the parity adjudication is `FAILED`, not `EARNED`: the committed v2
total-space complex matches the carried product profile, not the S3-like
profile. This is a real finding against the cover construction at this consumer
guard ceiling.

The committed v2 zero-shift regression emits cover/witness/law-refusal facts
but not a zero-shift chain complex. The wrong-gluing control is also not
committed as a chain complex. Both are reported as `INSUFFICIENT`; no replacement
cell model is introduced here.

## Commands

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_guard_v2/topology_parity_guard_v2.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_guard_v2/topology_parity_guard_v2_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_guard_v2/validate_topology_parity_guard_v2.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/topology_parity_guard_v2/tests
```
