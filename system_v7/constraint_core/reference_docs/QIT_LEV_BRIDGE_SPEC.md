# QIT -> Leviathan Bridge (spec + stub adapter)

**Status:** stub adapter earned (lev_bridge_sim.py, in the harness). NOT yet wired to
the live leviathan repo -- deliberately. This defines the interface foundations-up so the
coupling is reviewable before it touches Lev internals.

## What crosses the boundary

The constraint-core engine (Layers 0-13: it perceives, remembers, learns) exposes ONE
thing to a Leviathan graph: a per-tick **signal stream**. The graph does not see the
density matrix or the superoperators -- only the emitted record:

```
{ "tick":          int,
  "belief_bloch":  [x, y, z],     # current belief state (the engine's model of the world)
  "surprise_bits": float,          # free energy S(observation || belief) -- novelty / error
  "fe_gradient":   float }         # free-energy reduction this tick -- the learning drive
```

`surprise_bits` is the **control signal**. Verified behaviour (lev_bridge_sim.py):
near-zero while the world is predictable (0.006), spikes on a regime shift (1.50), decays
as the engine relearns (0.03). That is the hook a Lev node uses for attention allocation,
novelty detection, and when-to-act.

## Adapter surface (LevBridge)

```
br = LevBridge(rate=0.5)
br.subscribe(node_callback)        # a graph edge subscribes
rec = br.tick(observation_rho)     # advance one tick; returns + pushes the record
```

Minimal by design: `.tick(obs) -> record` and `.subscribe(cb)`. A Leviathan graph node
wraps `br.tick` on its input edge and routes `record` onto its output edges.

## What is deferred (needs the live repo, an owner decision)

- mapping `belief_bloch` onto a concrete Lev graph node type
- routing `surprise_bits` into Lev's attention/priority mechanism
- the reverse edge: letting a Lev action select the next observation (active inference's
  action half -- minimize EXPECTED free energy, not just current). The engine side is
  ready; the world/action model lives in Lev.

Pure QIT throughout (Umegaki relative entropy; no classical KL, no smuggled math).
