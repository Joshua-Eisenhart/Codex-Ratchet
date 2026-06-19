# Builder Self-Assessment

Builder verdict: scratch diagnostic only.

What was built:

- A 4Q nested geometry-delta result with all 12 nested schema fields.
- Actual alternate-run values for main, alternate registry pin, alternate probe family, scrambled pin, and negative control.
- A three-engine envelope with Julia, JAX, and PyTorch lanes.
- A local validator that runs the nested schema checker and builder/audit boundary helper; the envelope keeps Julia/Python load-bearing and JAX/PyTorch supportive by design.

Claim boundary:

- The delta is carrier-and-pins-relative.
- The expected honest result is relative, not intrinsic. The alternate probe changes the delta hash and the alternate registry pin also changes the delta hash.
- Crossover z3/cvc5 demoted to supportive (decorative per audit); claim rests on Julia+Python geometry recompute + the flip/null controls.
- No `audit_verdict.md` is written by this builder; independent audit remains a separate role.

Write boundary:

- All new files and generated results are confined to `system_v6/sims/gcm_nested_geometry_delta_4q_v0/`.
- No git staging or commit is part of this build.
