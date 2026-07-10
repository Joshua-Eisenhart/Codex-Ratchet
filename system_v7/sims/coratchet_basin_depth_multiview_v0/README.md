# coratchet_basin_depth_multiview_v0

Historical name retained for receipt stability. The claim audit found that
`coratchet` and `basin_depth` overstate the measured result.

Preregistered scratch diagnostic for one explicitly installed set of sixteen
ordered terrain/operator channel slots.

The packet asks two different questions and keeps them separate:

1. Does the explicitly installed finite CPTP cycle have a mathematically real
   global attracting fixed point?
2. Does the Ratchet select this cycle or make its contraction distinctive?

Julia is the semantic owner and constructs terrain generators with
`QuantumToolbox.liouvillian`. JAX independently reconstructs the channels and
performs the 1,024-state, parameter, schedule, covariance, and random-channel
sweeps. Neither lane reads the other's result.

The sixteen slot formulas are:

```text
Se: TiSe, SeTi, FiSe, SeFi
Ne: TiNe, NeTi, FiNe, NeFi
Ni: TeNi, NiTe, FeNi, NiFe
Si: TeSi, SiTe, FeSi, SiFe
```

Axis 6 is composition precedence only. It never changes the four operator
formulas.

## Run

```text
/opt/homebrew/bin/julia --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/coratchet_basin_depth_multiview_v0/run_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/coratchet_basin_depth_multiview_v0/run_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/coratchet_basin_depth_multiview_v0/validate_coratchet_basin_depth_multiview_v0.py
```

## Ceiling

`scratch_diagnostic`, `promotion_allowed:false`, and
`formal_admission_allowed:false` throughout.

Even a strict global contraction proves only a property of this installed
channel. It cannot derive four substages, select the sixteen-slot order, admit
either engine type, close Axis0, or support perception, object, MMM, ontology,
mesh, business, or physics claims.

The post-run fabrication audit further blocks co-ratchet, basin-depth, pawl,
schedule-advantage, and engine-personality language. See
`FABRICATION_AUDIT.md`.
