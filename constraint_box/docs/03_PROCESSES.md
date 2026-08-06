# Processes

All results below were run on 2026-07-27 with:

`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`

The outputs are host-local observations. They do not promote the package.

## Run the unit suite

This form suppresses JSON dispositions printed by tests and retains the unittest summary. `pipefail` keeps a suite failure nonzero.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && set -o pipefail
PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m unittest discover -s tests 2>&1 | grep -E '^(Ran [0-9]+ tests|OK$|FAILED)'
```

Output:

```text
Ran 213 tests in 42.920s
OK
```

Exit: 0.

## Run the finite demo

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m constraintbox demo
```

Output:

```json
{
  "bounded_solver": {
    "reason": "finite_witness_found",
    "status": "BOUNDED_SAT",
    "witness": {
      "x": 0,
      "y": 1
    }
  },
  "claim_ceiling": "finite runtime demonstration only",
  "compatible_histories": 3,
  "extension_fibres": {
    "a": 2,
    "b": 1
  },
  "present_projection": [
    [
      "a"
    ],
    [
      "b"
    ]
  ],
  "promotion_allowed": false,
  "schema": "constraintbox.demo.v1"
}
```

Exit: 0.

## Gate one receipt

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m constraintbox gate claimgate_plugin/fixtures/receipt_honest.json
```

Selected output:

```json
{
  "chain_exit_code": 1,
  "chain_root": "/Users/joshuaeisenhart/Codex-Ratchet",
  "chain_root_inside_box": false,
  "chain_verdict": "REJECTED",
  "disposition": "REFUSED",
  "promotion_allowed": false,
  "required_unmet": [
    "tier0"
  ],
  "tier0_checker": "/Users/joshuaeisenhart/Codex-Ratchet/claimgate/claimgate.py",
  "verified_tiers": [
    "tier1"
  ]
}
```

Exit: 1. Here 1 means the chain ran and `constraintbox gate` classified the process result as `REFUSED`. The resolved chain root is outside the box, which is the in-repository self-containment defect recorded in `PROVENANCE.md`.

## Run the S1 acceptance tier

No `--output` argument is used, so this command does not rewrite a retained receipt.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m constraintbox estate --pack-root . --manifest ../external_sim_estate/legacy_estate_v2/sim_estate_v2.json --fixture ../external_sim_estate/legacy_estate_v2/fixtures/manifold_fixture_v1.json --tier S1 --mode acceptance --python /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 --enforce
```

Selected output:

```json
{
  "controller_sha256": "ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7",
  "environment": {
    "expected_lock_sha256": "fc8ad6f3c2d22123c89cb325359ed7beab3b5b258b5fed507d6450a5c4c60aef",
    "missing": [
      "cvc5==1.3.4",
      "numpy==2.5.1",
      "scipy==1.18.0",
      "z3-solver==5.0.0.0"
    ],
    "state": "DRIFT",
    "tested_lock": "requirements/locks/e0-py312-linux.lock"
  },
  "layer_id": "S1",
  "mode": "acceptance",
  "promotion_allowed": false,
  "python_version": "3.13.6",
  "state": "DRIFT"
}
```

Every capability row also reported:

```json
{
  "expected_controller_sha256": "9ce0edb4d109de1935574f4f01943310b1e6d30710ac076e3a7199f1b83e3500",
  "observed_controller_sha256": "ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7",
  "reason": "controller_source_digest_mismatch",
  "state": "DRIFT"
}
```

Exit: 1. This run found both Darwin-versus-Linux environment drift and a stale controller pin. The digest mismatch stopped capability controls from running. Do not describe this S1 run as a capability pass.

## Run the slop gate

The gate lives at the repository root, outside `constraint_box`.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 claimgate_plugin/slop_gate.py claimgate_plugin/slop_gate.py
```

Output:

```text
slop_gate: 0 suspect(s)
```

Exit: 0. This means the scanned path matched no slop signature. It is not a scientific verdict or a proof that the file is correct.

## Add a check

1. Name one narrow defect class and one producer behavior it is meant to distinguish.
2. Decide whether the producer can identify the probe. If it can, lower the claimed meaning of a pass.
3. Return a distinct reason code for each failure class. Do not collapse missing input, evaluation error, policy refusal, and an observed counterexample.
4. Add a minimal positive fixture that the check must catch.
5. Add an honest nearby negative fixture that it must leave alone.
6. Record the expected disposition per case in JSON.
7. Make deviation in either direction fail. Closing a known hole and reopening one are different movements and need different reason codes.
8. Demonstrate teeth in a throwaway copy: revert the implementation change while retaining the test, then show that the test fails.
9. If a source digest is pinned, re-pin it after the final source edit and verify the pin against the file.
10. Record unrun controls in `controls_not_measured`. Do not infer them from an aggregate state.

`claimgate_plugin/run_bypass2_regression.py` is the house-style reference for per-case expectations, bidirectional deviation, missing-fixture handling, and distinct reason codes. Its `COVERAGE_MISMATCH` branch is recorded as dead in `PROVENANCE.md`; do not copy that inert guard.

## Add a fixture

1. Put the smallest input that demonstrates the behavior under the appropriate fixture family.
2. Add a paired honest input when a false positive is plausible.
3. Bind each case to an explicit expected outcome in the runner's JSON or case table.
4. Give each deviation a reason code. An unexpected block is not the same event as an unexpected admission.
5. Keep the fixture independent of existing generated ledgers where possible. `run_bypass2_regression.py` is not side-effect-free because one case appends to the gate ledger.
6. Run the specific regression and inspect its result JSON before citing it.
7. Confirm the runner is actually wired to a hook or CI command before calling the corpus load-bearing.

## Claim ceiling

This package is not promoted. `promotion_allowed: false`. The strongest unit-suite label from this lane is `passes local rerun` on one host. `constraint_box/PROVENANCE.md` is the authority on broken, unmeasured, duplicated, and open surfaces.
