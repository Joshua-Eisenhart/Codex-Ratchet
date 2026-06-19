# BUILD CARD - malcev_akivis_tangent_micro_v0

Source request: old-estate item 13, panel 6 q4 pre-registered.

Build in `system_v6/sims/malcev_akivis_tangent_micro_v0/` only. Do not stage or commit.

Object:

- Consume `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` exactly by hash.
- Build the anticommutative commutator algebra on the seven imaginary octonion basis elements.
- Compute a nonzero Jacobiator witness exactly.
- Verify the Malcev identity exactly in both pre-registered forms:
  - compact form: `J(x,y,xz)=J(x,y,z)x`;
  - expanded form: `((xy)(xz)) + ((y(xz))x) + (((xz)x)y) = (((xy)z)x) + (((yz)x)x) + (((zx)y)x)`.
- Verify the quaternion subalgebra control has Jacobi identity exactly.
- Perturb one product deliberately and verify the Malcev identity fails.

Fences:

- Claim ceiling: `tool_function_micro_only`.
- Classification: `scratch_diagnostic`.
- Nonassociativity is a diagnostic readout here, not a physics/engine/bridge claim.
- Julia owns the committed structure constants; Python/JAX mirrors the exact finite calculation.
- PyTorch is omitted because no autograd, graph, tensor-network, or neural surface is scoped.

Expected commands:

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/malcev_akivis_tangent_micro_v0/malcev_akivis_tangent_micro_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/malcev_akivis_tangent_micro_v0/malcev_akivis_tangent_micro_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/malcev_akivis_tangent_micro_v0/malcev_akivis_tangent_micro_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/malcev_akivis_tangent_micro_v0/validate_malcev_akivis_tangent_micro_v0.py
```
