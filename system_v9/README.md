# Codex Ratchet Stack v9

V9 is the first repository release spine that treats the major systems as
independent products instead of one growing Python tree.

| Product | Canonical root | Default runtime | Owns |
|---|---|---|---|
| ConstraintBox | `constraint_box/` | CPython | finite constraint processing and Mini-Lev control |
| ClaimGate | `claimgate_plugin/` | CPython + Node for its existing checks | admission and evidence-policy decisions |
| Sim Engines | `sim_engines/` | Python, Julia, JAX, PyTorch, external binaries | scientific and mathematical computation |
| Codex Ratchet | `system_v9/codex_ratchet/` | controller + explicit bridge processes | staged research orchestration |
| Holodeck | `holodeck/` | lightweight Python shell; PyTorch in an optional profile | trainable predictive/world-model work |

No product becomes part of another merely because it is installed in the same
environment or imported by an old probe. Connections are records in
`bridges/registry.v9.json`; each record names direction, schema, failure
semantics, and a test. A missing or untested bridge is a visible gap, not an
implicit integration.

V9 is a development release. It organizes executable sources and installation
surfaces; it does not promote Manifold, QIT, physics, or Holodeck science claims.

The dated exercised-state report is `CURRENT_STATE_20260806.md`.

## Verify

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v9/verify_stack.py
```

The verifier uses only the Python standard library. Product-specific commands
are listed in `STACK_MANIFEST.json`.
