# BUILD CARD - root_randomness_entropy_discriminator_v0

Builder: codex1 (builder, high)
Repo: `/Users/joshuaeisenhart/Codex-Ratchet`
Write boundary: everything inside `system_v6/sims/root_randomness_entropy_discriminator_v0/`; no git add/commit.

## Authority

Primary authority is commit `35ed8142c`, `system_v6/receipts/physics_model_primary_deepread_20260612.md`, safe-order item 2:

`root_randomness_entropy_discriminator_v0`: root entropy/randomness toy with label-shuffle controls.

The consumed Section A root rows are R01, R02, R03, R04, and R05: randomness as least starting axiom, entropy base vocabulary, entropy flow direction, void/possibility basis, and Humean nominalism/relation-first identity.

Shared fence: source quote -> finite witness -> control -> claim ceiling.

## Object

Build a finite root-layer discriminator toy:

- pinned finite random process: seed `1729`, sixteen binary-word samples over `["00", "01", "10", "11"]`;
- derived entropy ladder: counting entropy and a classical diagonal vN proxy over the finite count density;
- label-structured control: same ensemble counts plus a meaningful label quotient;
- label-shuffle control: root rows must stay invariant while label-dependent rows change;
- geometry-first control: impose a finite ring quotient before entropy and require an order/readout change;
- SMT computed bindings over finite count/order predicates, with z3/cvc5/Julia Z3 negated identity UNSAT and perturbed controls SAT.

## Boundary

Classification: `scratch_diagnostic`
Claim ceiling: `root_layer_discriminator_only`
Promotion: `promotion_allowed=false`, `formal_admission_allowed=false`

No physics admission, cosmology conclusion, ontology conclusion, spacetime claim, dark-sector claim, vacuum-energy inference, or downstream packet completion is allowed.

## Required Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/root_randomness_entropy_discriminator_v0/root_randomness_entropy_discriminator_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/root_randomness_entropy_discriminator_v0/root_randomness_entropy_discriminator_v0_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/root_randomness_entropy_discriminator_v0/root_randomness_entropy_discriminator_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/root_randomness_entropy_discriminator_v0/root_randomness_entropy_discriminator_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/root_randomness_entropy_discriminator_v0/validate_root_randomness_entropy_discriminator_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/root_randomness_entropy_discriminator_v0/results/root_randomness_entropy_discriminator_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/root_randomness_entropy_discriminator_v0/tests
```
