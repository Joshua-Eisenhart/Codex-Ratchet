# Dual-Ratchet Four-Count Nonforcing SMT v0

## Status

`scratch_diagnostic`; `promotion_allowed: false`; `formal_admission_allowed: false`.

This packet asks a narrow cardinality question: within one declared finite
formalization and the search window `L=2..8`, do the current explicit
count-free dual-ratchet properties force a cycle of length four?

It does not repeat the operator-family search in
`dual_ratchet_substage_survivor_discovery_v0`. That packet found a conditional
four-class quotient inside a finite Pauli registry and then blocked universal
four with generic axes. This packet instead tests temporal cycle length.

## Read Locks

The preregistration hashes and roles for the source correction, rejected
UP-130 construction, fabrication audit, and survivor-discovery packet are in
`spec.json`. In particular:

- the source correction says UP-130 fixed two `A` and two `B` legs before its
  scan;
- the fabrication audit found commuting channels, invariant entropy, and the
  same cardinality leak;
- the survivor packet explicitly did not earn temporal four or per-stage four
  substages.

## Finite Object

The phase carrier is `Z3_geometry x Z3_entropy`, encoded as nine states. Nine
was selected because it can represent a simple cycle at every searched length
through eight and does not privilege four.

For each Axis-6 sign, the solver synthesizes two anonymous total maps on this
carrier:

```text
G_sign : phase -> phase
E_sign : phase -> phase
```

A word of externally queried length `L` selects `G` or `E` at each leg. One
Boolean Axis-6 sign is shared by all legs and selects the applied map table.

The baseline asserts only:

1. both distinct work kinds are used;
2. the selected maps differ and do not commute on at least one carrier state;
3. at least one visited `G` leg advances the geometry coordinate;
4. at least one visited `E` leg advances the entropy coordinate;
5. the finite ordered trace closes;
6. every leg uses the one shared sign;
7. no desired count, source operator names, or `16 x 4` schedule enters the
   solver.

The full formulas and preregistered branch table are in `spec.json`.

## Additional Axioms

Ten count-free candidates are tested one at a time, never cumulatively:

- cyclic alternation;
- primary-coordinate progress on every leg;
- a simple phase cycle;
- no early return;
- a noncommutation witness on the visited cycle;
- failure of closure under the opposite shared sign;
- bijective selected maps;
- failure of closure after any one kind flip;
- failure of closure after any one leg deletion;
- failure of closure under word reversal.

Four deliberately rejected controls test that the harness can recognize a
forcing premise:

- exactly two legs of each kind;
- exact binary-by-binary coverage;
- an explicit four-step word;
- exactly four legs.

These controls are evidence of cardinality contamination, not candidate
explanations.

## Solver Independence

`dual_ratchet_four_count_nonforcing_smt_v0_z3.py` and
`dual_ratchet_four_count_nonforcing_smt_v0_cvc5.py` contain separate encodings.
Neither imports the other or reads its result. Agreement means every
scenario/length SAT or UNSAT status matches. The two solvers may choose
different models; every SAT model is independently replayed by
`validate_dual_ratchet_four_count_nonforcing_smt_v0.py` without importing Z3
or cvc5.

## Run

From the repository root, use the Makefile interpreter:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/run_dual_ratchet_four_count_nonforcing_smt_v0.py
```

The controller runs this sequence twice:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/wizard_v4_3_object_card.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/dual_ratchet_four_count_nonforcing_smt_v0_z3.py --output <RUN_DIR>/z3_raw_solver_receipt.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/dual_ratchet_four_count_nonforcing_smt_v0_cvc5.py --output <RUN_DIR>/cvc5_raw_solver_receipt.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/validate_dual_ratchet_four_count_nonforcing_smt_v0.py --z3 <RUN_DIR>/z3_raw_solver_receipt.json --cvc5 <RUN_DIR>/cvc5_raw_solver_receipt.json --output <RUN_DIR>/agreement_validation.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/dual_ratchet_four_count_nonforcing_smt_v0/validate_dual_ratchet_four_count_nonforcing_smt_v0.py --z3 <RUN_DIR>/z3_raw_solver_receipt.json --cvc5 <RUN_DIR>/cvc5_raw_solver_receipt.json --self-test --self-test-output <RUN_DIR>/malformed_input_selftest.json
```

The runner fails closed if either Python solver module is missing, either
solver returns `unknown`, a model fails replay, a status differs, a malformed
receipt is accepted, or any rerun hash differs. The cvc5 Python API is the
load-bearing cvc5 surface; a standalone `cvc5` executable is not required.

## Artifacts

- `results/z3_raw_solver_receipt.json`: 105 Z3 query receipts and all SAT
  models;
- `results/cvc5_raw_solver_receipt.json`: 105 cvc5 query receipts and all SAT
  models;
- `results/agreement_validation.json`: solver-free model replay and status
  agreement;
- `results/malformed_input_selftest.json`: six intentional corruption tests;
- `results/deterministic_rerun_hashes.json`: pass-A/pass-B hashes and exact
  commands;
- `results/wizard_v4_3_validation.json`: object-preservation preflight.

## Claim Ceiling

A nonforcing result means only that the encoded baseline and the ten listed
one-at-a-time additions do not select four over other admitted lengths on this
nine-state carrier for `L=2..8`. It is not a theorem over every carrier, every
possible dual-ratchet axiom, continuous dynamics, or unbounded words.

The source still defines 16 source slots, each expanded across four operator
substages sharing one Axis-6 sign. If this scout is nonforcing, that `16 x 4`
schedule remains a source-defined rule or candidate carrier; the multiplier
four is not independently earned by the tested count-free temporal axioms.
