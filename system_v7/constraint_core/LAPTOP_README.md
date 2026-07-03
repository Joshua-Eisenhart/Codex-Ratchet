# Laptop runner — constraint-core bundle

Everything here runs on your laptop with one command. No repo access, no cloud,
no network beyond the initial pip install. The bundle is the audited model +
the pure-math sims + the aligned-substrate engines (JAX / Julia / PyTorch).

## One command

```bash
bash LAPTOP_RUN.sh            # full: makes a venv, installs deps, runs everything
bash LAPTOP_RUN.sh --fast     # quick: skips jax/torch install, long sims, engines lane
```

Exit code 0 = GREEN (every check passed). Exit 1 = a finding — report the
numbers, do NOT edit an expected value to force green (several checks are
HONEST FAILURES that must stay failing; a flipped one is a regression).

Machine-readable result is written to `run_all_report.json`.

## What it runs

1. **23 pure-math sims** (`sims_and_scripts/`) via `run_all.py` — each asserts its
   headline invariants with explicit tolerances. Includes the newly derived
   `admissibility_two_operator_sim.py` (why exactly 2 operators per terrain).
2. **engines/ cross-substrate lane** — the 16-stage engine contract computed by
   the numpy RK4 oracle, then by the JAX exact-superoperator kernel (and PyTorch
   if installed), cross-checked by `validate_engines.py`. Agreement to 1e-6 by
   two independent methods (integration vs matrix-exp) is the validity mechanism.
3. **Julia route** (if `julia` is on PATH) — the 3rd independent substrate. This
   is the one route not yet run in-house; if it disagrees, that is a finding.

## Your sim runner

The engine contract that any substrate must reproduce is `engines/targets.json`
(written by `engines/oracle_targets.py`). To plug in your own production engine,
emit results in the same schema as `engines/jax_engine.py` writes, then:

```bash
cd engines
python your_engine.py          # writes your_results.json in the targets schema
python validate_engines.py     # compares every *_results.json to targets; exit 0 = GREEN
```

Model constants are the single source of truth in `targets.json`
(`model_constants`: G, KAP, Q, TH, T_FLOW, PROBE) — read them, never hardcode.

## Requirements

- Python 3.9+ (`numpy`, `scipy`, `sympy` required; `jax[cpu]`, `torch` optional).
- Julia (optional, for the 3rd substrate): install from julialang.org, then the
  runner adds the JSON package automatically.

## Where the model is written down

- `ORIENTATION.md` — start here.
- `MODEL_LAYER_LEDGER.md` — the model, layer by layer, each component's math +
  earned/candidate/open status + computed value.
- `spec_and_reports/CONSTRAINT_CORE_FORMAL_SPEC.md` — the full formal spec.
- `spec_and_reports/PURE_MATH_CORE.md` — the de-jargoned proposition ledger.
- `data_json/rosetta_layer.json` — the label layer (jargon lives here, not in the math).
- `CLAUDE.md` — the agent contract (hard rules, withdrawn claims, open decisions).
