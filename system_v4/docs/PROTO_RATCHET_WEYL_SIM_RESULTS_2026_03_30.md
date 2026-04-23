# Proto-Ratchet Weyl Sim Results

**Date:** 2026-03-30

## Status

This is a proposal-only controller packet summarizing the implemented Weyl sim lanes.

- not canon
- not an authority promotion surface
- not a replacement for current owner/controller doctrine docs

## Lane A

Source:
- [sim_weyl_ambient_vs_engine_overlay.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_ambient_vs_engine_overlay.py)

Result:
- `PASS`

Controller read:
- ambient geometry variation is real
- engine-overlay variation is also real
- raw local `L|R` remains control-only at initialization

## Lane B

Source:
- [sim_Ax3_Ax4_rebinding_stress.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_Ax3_Ax4_rebinding_stress.py)

Result:
- `PASS`

Controller read:
- Ax3 remains robust under the Weyl-manifold reinterpretation
- Ax4 also remains robust once the exact neutral Clifford anchor is treated as a symmetry seat rather than a torus-wide collapse
- this supports the current Ax3/Ax4 bindings as strong operational bindings, not yet proof of metaphysical finality

## Lane C

Source:
- [sim_weyl_geometry_ladder_audit.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_weyl_geometry_ladder_audit.py)

Result:
- `PASS`

Controller read:
- the Weyl-ambient rung now has an independent witness in the executable stack
- inner/outer torus cases show nontrivial geometric holonomy
- the Clifford midpoint is a neutral witness seat
- ambient witness and engine response are separable rather than numerically collapsed into the same signal
- raw local `L|R` still remains control-only

## Combined Read

The implemented sim program now supports the following proposal-only read:

- Weyl ambient structure is not just empty naming
- engine DOF are not reducible to that ambient witness
- current Ax3/Ax4 locks survive the reinterpretation pressure
- the Weyl-manifold shift is now better supported at the executable level than it was before Lane A/B/C

What this still does **not** establish:

- final canon geometry
- final Ax0 bridge
- final doctrine-level rebinding of all axes

## Best Next Step

The best next bounded step is no longer another geometry proposal packet.

It is one of:

1. a Weyl-aware Ax0 bridge discriminator
2. a direct audit of how the two root constraints ratchet into the now-supported geometry ladder
3. a controller reconciliation pass comparing current doctrine docs against the new Lane A/B/C executable support
