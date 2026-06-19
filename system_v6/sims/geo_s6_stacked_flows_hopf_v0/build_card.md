# BUILD CARD v2: geo_s6_stacked_flows_hopf_v0

Status: rebuild after `REJECT AS CLAIMED`; builder packet only. Separate audit required before using this as audit evidence.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Rebuild in place under `system_v6/sims/geo_s6_stacked_flows_hopf_v0/`.
- Leave `audit_verdict.md` untouched.
- Keep the v1 card under `SUPERSEDED/`.
- Keep K1 `dz/dt` lineage, K3 placements, and K4 `g_DI` stable where not touched by the `chi0` repin.
- Rerun all engine legs and the envelope fresh.

Binding gates:
- V1 transported loops: for pure-Hopf rows, compute terrain action on `A/F/h/Phi_ij` by flowing the full loop with `Phi_t`, numerically transporting along the flowed loop, and integrating `A/F`; local connection-delta sampling is not a substitute.
- V2 round-trip and mutation gates: P10 must differentiate symbolic leakage and finite-time shell updates back to exported `A*r+b`, rerun `Phi_D/Phi_I` map rows, and rerun every mutation through the same gates with failing values emitted.
- V3 pin fix: use generic `chi0=pi/7`, with a genericity check that no special trig zeros remain on the claim path.
- V4 blind comparison: values legitimately changed by the repin must be compared against `/tmp/s6_blind_expected_20260610.md` formulas evaluated at the new pin.
- Preserve the scratch ceiling even when all rebuild gates pass.

Engine roles:
- Julia: carrier-side matrix/signature computation plus Z3 bound contradiction.
- JAX/SymPy: symbolic leakage, transported-loop action, placement rows, overlay rows, loop-order gap, P10 round-trip, and executed mutation reruns.
- PyTorch: tensor/autograd mirror for load-bearing leakage and loop-order signatures plus SMT controls.
