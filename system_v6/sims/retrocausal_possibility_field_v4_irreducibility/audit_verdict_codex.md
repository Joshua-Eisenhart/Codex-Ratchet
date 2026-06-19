BOTTOM LINE: COMMIT_READY at scratch_diagnostic ceiling.

Binding Codex verdict: rpf_v4 honestly shows "retrocausal NOT robustly earned
(borderline-reducible)" for the v3 global-selection claim. This is commit-worthy as
an honest falsification-attempt receipt, not as a positive retrocausal result.

Claim ceiling:

- classification: scratch_diagnostic
- promotion_allowed: false
- formal_admission_allowed: false
- honest claim: on the primary independent-draw family, the v3 global output
  sequence measure is reducible to a width-N_f forward Markov model under this
  deterministic-embedding TV discriminator; across the family sweep, only 1/7
  families are irreducible, so robustness is not earned.

What I checked:

- No standalone `validate_retrocausal_possibility_field_v4_irreducibility.py` exists
  in this packet. I used the packet test file as the non-writing executable validator
  and did not run the sim `main()`, because `main()` rewrites the result JSON and the
  audit order was read-only except for this verdict file.
- Ran packet tests with the required interpreter:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/retrocausal_possibility_field_v4_irreducibility/tests/test_retrocausal_possibility_field_v4_irreducibility.py`
  Result: ALL TESTS PASS.
- Independently reran the discriminator from module functions for the primary family,
  the negative control, and the seven-family sensitivity sweep.
- Reimplemented the TV-infimum spot-check in a separate audit script: rebuilt empirical
  mu, enumerated deterministic embeddings, built the best-fit forward Markov measure,
  and recomputed TV without calling the packet's `tv_infimum_over_forward_markov`.

Fresh facts:

- N_f is measured from v3 fiber cardinality: per-shell max fibers `[3, 3, 3]`, so
  N_f=3.
- Primary family size: 27.
- Primary distinct global output sequences: 8.
- Primary exhaustive embedding search: 6561 embeddings, matching `3**8`.
- Primary TV infimum: 0.046783625730994205.
- Threshold: 0.05.
- Primary verdict: reducible, because 0.046783625730994205 <= 0.05.
- Negative control TV infimum: 8.326672684688674e-17.
- Negative control verdict: reducible; factors as width-N_f forward Markov.
- Family sweep:
  - irreducible families: 1/7
  - reducible families: 6/7
  - negative control reducible in every swept family: true
- Independent alternative TV recomputation matched the packet exactly:
  - positive TV: 0.046783625730994205
  - negative TV: 8.326672684688674e-17

Arbiter conclusion:

COMMIT_READY. The discriminator is real enough for a scratch_diagnostic
falsification-attempt receipt. Its honest result is negative/borderline-reducible:
the strong retrocausal/global reading is not robustly earned by this test.

Commit hygiene:

Do not stage `__pycache__/` or `.pyc` files. Stage only intended source, tests,
result JSON, and this audit verdict if committing this packet.
