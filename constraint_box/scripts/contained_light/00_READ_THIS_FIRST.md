# ConstraintBox contained Light — 16 August 2026

This zip is a finite Light slice. Extract it. Run it.
It is not a theory of everything, not an engine, and not a promotion.

## Start

First verb, no venv:

```text
sh seed-check
```

The default receipt is `RUNS/seed-check/SEED_CHECK.json`.
`verify.sh` still writes focused receipts under `receipts/` with `--out`.

For the remaining verbs you need a Python that already has pytest, pydantic,
z3-solver, and cvc5. Do not use Homebrew or `/usr/bin` `python3` for those.

On this machine:

```text
export CB_PYTHON=/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/.venv/bin/python
```

```text
./bin/cb seed
```

```text
./bin/cb feasibility
```

```text
./bin/cb quotient
```

```text
./bin/cb surface
```

```text
./bin/cb status
```

```text
./bin/cb verify
```

`seed-check` is the stdlib first verb from the lean-system contract.
`seed` writes the same recompute as a contained receipt.
`feasibility` runs the honest SAT compiler. Solver witnesses are not quotients.
`quotient` induces S/~_P from bound observation rows only.
`surface` lists static supports, constraints, probe packets, and bound packets.
`status` reads the append-only receipt journal.
`verify` runs the verbs and the focused tests.

## What this is

Light holds the finite seed. Models may propose packets. Code decides.
ZIP/waves are later forms. They are not in this zip.

Honest name of the SAT compiler: `finite_probe_assignment_feasibility.v1`.
It is not measured distinguishability.
Honest name of the quotient: `bound_observation_quotient.v1`.
Static supports and basins are leftovers of a finite relation. They are not attractors.

## Layout

- `light/src/constraintbox` — Light verbs only
- `light/fixtures` — time-first seed, collapsed negative, feasibility packets, bound rows
- `light/tests` — focused tests
- `light/mmm/packs` — six CB MMM packs
- `LIGHT_CONTRACT.md` — first-layer object and refuse rules
- `seed-check` — stdlib first verb
- `bin/cb` — seed-check / seed / feasibility / surface / quotient / status / verify
- `receipts` — last local rerun and sqlite journal
- `STATE` — claim ceiling and git head

## Claim ceiling

Local contained source overlay. Not the installed Light wheel. Not `python -I`
admission. Not Heavy. Not attractors or engines.
