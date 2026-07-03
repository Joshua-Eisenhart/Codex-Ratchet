# manifold_dual_ratchet_foundations_v0

Bottom-up foundations diagnostic for constructing quotient geometry from root
constraints via the dual ratchet. This replaces saliency-level terrain sims for
this question: nothing here consumes installed terrain labels or terrain laws.

Ceiling:

- `classification`: `scratch_diagnostic`
- `claim_ceiling`: `QUARANTINE_EXPLORATORY`
- `promotion_allowed`: `false`
- `formal_admission_allowed`: `false`

Run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/manifold_dual_ratchet_foundations_v0/manifold_dual_ratchet_foundations_v0_numpy.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/manifold_dual_ratchet_foundations_v0/manifold_dual_ratchet_foundations_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/manifold_dual_ratchet_foundations_v0/check_agreement.py
```

Artifacts:

- `results/*_numpy_results.json`
- `results/*_julia_results.json`
- `results/*_graveyard.jsonl`
- `results/*_agreement_results.json`
- `RESULTS.md`
