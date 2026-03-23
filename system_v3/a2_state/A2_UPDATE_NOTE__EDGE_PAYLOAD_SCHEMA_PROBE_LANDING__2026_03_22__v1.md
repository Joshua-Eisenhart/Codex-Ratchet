# A2 Update Note — Edge Payload Schema Probe Landing

- date: `2026-03-22`
- surface_class: `DERIVED_A2`
- scope: `system_v4 graph/control-substrate line / upper-loop controller continuity`

What changed:

- the graph/control-substrate line now has a bounded read-only sidecar probe:
  - `edge-payload-schema-probe`
- current relation is `STRUCTURALLY_RELATED`
- current payload preview count is `3`
- current next step is `hold_probe_as_sidecar_only`

Meaning:

- the edge-payload schema is no longer only a static audit surface; it now has a live payload-preview probe over real low-control edges
- this remains sidecar-only and does not change canonical graph ownership
- this is not permission for training, runtime mutation, or semantic overclaim around axis0 / Hopf / entropy payload meaning

Required continuity:

- front-door corpus and controller surfaces should treat the probe as landed
- the standing fence remains read-only / sidecar-only
