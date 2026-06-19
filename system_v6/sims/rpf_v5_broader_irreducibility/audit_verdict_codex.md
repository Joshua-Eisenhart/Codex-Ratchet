BOTTOM LINE: COMMIT_READY at scratch_diagnostic ceiling.

This packet is commit-worthy as a falsification receipt. It closes the strong
retrocausal/global irreducibility reading downward: the global selection measure is
reducible to a bounded forward stochastic HMM on both toy v3 and grounded M(C), with
negative controls fitting near zero.

Validator:

- Command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 validate_rpf_v5_broader_irreducibility.py`
- Exit: 0
- Output: `ok=true`, `status=KILLED`, `toy_tv=1.845164436154782e-09`, `grounded_tv=0.002290602336863`

Fresh TV check:

- Command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... build_result(restarts=8,max_iter=220) ...`
- Toy v3 global: `tv=1.845164436154782e-09`, reducible.
- Grounded M(C) global: `tv=0.002290602336863`, reducible.
- Toy v3 negative control: `tv=1.1999912372421653e-11`, passes near-zero control.
- Grounded M(C) negative control: `tv=1.4015772511461833e-11`, passes near-zero control.
- `negative_controls_pass=true`, `strong_status=KILLED`, `all_pass=true`.

Stored result check:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `all_pass=true`
- `strong_retrocausal_global_claim_status=KILLED`
- `negative_controls_pass=true`

Honest ceiling:

This earns only a finite sequence-measure reducibility/falsification receipt against
a fitted bounded stochastic HMM forward model. It supports the owner decision that
"retrocausal" is not earned here and reduces to forward explanation on these
carriers. It does not prove physics, temporal retrocausation, Axis0, manifold
structure, canonical status, or formal irreducibility.

Commit gate:

- Verdict: `COMMIT_READY`
- Commit as: negative/falsification scratch receipt.
- Exclude: `__pycache__/`.
