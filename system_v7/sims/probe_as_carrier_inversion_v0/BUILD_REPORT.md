# BUILD_REPORT -- probe primary inversion v0

## Bottom Line

BUILD STATUS: PASS

The decisive flip-control holds:

- single-generator control: `class_count=1`, `distinction_count=0`
- all-commuting control: `class_count=1`, `distinction_count=0`
- noncommuting alphabet: `class_count=6`, `distinction_count=5`

The branch remains fenced: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Artifacts

- `spec.json`
- runner Python file in this directory
- result JSON under `results/`
- `BUILD_REPORT.md`

## Checks

Python run:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/probe_as_carrier_inversion_v0/probe_as_carrier_inversion_v0.py
```

Exit code: `0`

Key output:

```json
{
  "build_status": "PASS",
  "failures": [],
  "flip_control": {
    "all_commuting_class_count": 1,
    "all_commuting_distinctions_vanish": true,
    "noncommuting_class_count": 6,
    "noncommuting_distinctions_survive": true,
    "single_generator_class_count": 1,
    "single_generator_distinctions_vanish": true
  },
  "ok": true,
  "smt_ok": true
}
```

SMT relation checks:

- `z3`: all-commuting bad case `unsat`; no-commuting bad case `unsat`; single-generator bad case `unsat`
- `cvc5`: all-commuting bad case `unsat`; no-commuting bad case `unsat`; single-generator bad case `unsat`

Contract lint:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/probe_as_carrier_inversion_v0/probe_as_carrier_inversion_v0.py
```

Exit code: `0`

```json
{
  "checked": 1,
  "violation_total": 0,
  "sims_with_violations": 0,
  "violations_by_type": {},
  "top_offenders": [],
  "violations": []
}
```

Forbidden-token scan requested by the build packet:

- exit code after `|| true`: `0`
- matches: none

Owner-banned object-name scan:

```json
{"object_symbol_hits": []}
```

## Claim Ceiling

Finite probe-word rewrite candidate only. The result shows that order distinctions vanish under the single-generator and all-commuting controls and survive under a noncommuting alphabet. It does not promote the branch, admit a stronger layer, or create a separate support entity.
