# ConstraintBox Integrated — read this first

This package contains one ConstraintBox system with explicit internal
boundaries:

- deterministic Light finite gates;
- stateless ZIP Agent transport/execution;
- a curated wave/skill/MMM pack;
- thin host/provider adapter source;
- a separate JAX capability route;
- full prompt/plan/progress context plus a compact boot projection.

It does **not** put JAX into Light, activate model providers, promote the
manifold campaign, or call generic noncommutation chirality.

Read `SYSTEM_ARCHITECTURE.md`, `HOW_TO_RUN.md`, and `WHAT_IS_PROVEN.md` for the
human overview. They separate the architecture, commands, measured results,
and current limits.

## First commands

If the extracted package does not yet have a Light environment, create it with
the tested macOS-arm64/Python-3.13 lock (network access is required for the
first install):

```text
python3 bin/cb bootstrap-light
```

Then bind the separate JAX interpreter already installed on this machine:

```text
export CB_LIGHT_PYTHON="$PWD/PROJECT/constraint_box/.venv/bin/python"
export CB_JAX_PYTHON=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
```

Then:

```text
python3 bin/cb doctor
python3 bin/cb context
python3 bin/cb light-seed
python3 bin/cb structured-probe --engine exact --output runs/structured-exact.json
python3 bin/cb structured-probe --engine dual --output runs/structured-dual.json
python3 bin/cb jax-wave --output-dir runs/light-jax-wave
python3 bin/cb verify --output runs/VERIFY.json
```

For the source checkout use `constraint_box/integrated_system/bin/cb`; in the
release ZIP use root `bin/cb`.

Read `context/current/OWNER_OBJECT.md`, `CURRENT_PLAN.md`, and
`FAILURE_MEMORY.md` before changing the system. Use the full JSONL corpus only
when the compact projection lacks needed intent.

Claim ceiling: local integrated source/bundle candidate; no portable
installation, provider execution, Light/Heavy admission, scientific result, or
promotion.
