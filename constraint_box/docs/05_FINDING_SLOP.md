# Finding slop

## Self-containment gap

The slop gate is `/Users/joshuaeisenhart/Codex-Ratchet/claimgate_plugin/slop_gate.py`. It is outside `constraint_box`.

`constraint_box/claimgate_plugin/` does not contain `slop_gate.py`, `run_slop_regression.py`, or `ci_slop_report.py`. The box therefore cannot perform this documented slop scan by itself. The two ClaimGate trees are diverged duplicates, and the owner has not selected a canonical one.

## What the gate reports

The scanner parses Python and reports narrow static suspects:

| ID | Actual signature |
|---|---|
| S1 | A constant outcome is attached to a named external tool, but the file imports neither that tool nor a process launcher. |
| S2 | A test has no discriminating assertion, only checks that a call does not raise, or asserts only constants. |
| S3 | An exception path in an operation-named function manufactures literal success. |
| S4 | An operation-claiming function has an entirely literal body. |
| S5 | A non-standard-library import binding is never referenced in the module. |
| S6 | A local `pass`, TODO, or `NotImplementedError` stub has a uniquely resolved scanned caller that consumes its return. |

S5 excludes conditional imports, `__init__.py`, `# noqa: F401`, re-exports, and annotation use. S6 excludes abstract methods and ambiguous dispatch.

The CLI accepts paths, `--diff` with a Git ref or file, and `--json`:

```text
slop_gate.py [--diff <ref|file>] [--json] <path> [<path> ...]
```

Exit codes are:

| Exit | Meaning |
|---:|---|
| 0 | no suspects |
| 1 | one or more suspects |
| 2 | usage, input, or parse error |

A nonzero exit is a policy disposition. It is never a scientific verdict.

## Read a finding

Each finding carries:

- `signature_id`: the narrow syntax or data-flow pattern, not a conviction.
- `path` and `line`: where to inspect.
- `excerpt`: the matched source.
- `why`: the exact reason the signature fired.

The honest ceiling inherited from `bc_scan.py` is `SUSPECT`. A name match is never proof. A finding is a place to look. Review the surrounding code, caller, generated inputs, and actual runtime before deciding whether it is slop.

## Real scans

The gate scanned its own source:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 claimgate_plugin/slop_gate.py claimgate_plugin/slop_gate.py
```

Output:

```text
slop_gate: 0 suspect(s)
```

Exit: 0.

The positive S1 fixture produced:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 claimgate_plugin/slop_gate.py claimgate_plugin/fixtures/slop/S1_positive
```

Output:

```text
/Users/joshuaeisenhart/Codex-Ratchet/claimgate_plugin/fixtures/slop/S1_positive/literal_outcomes.py:2: S1 constant tool outcome is adjacent to 'z3', but this file imports no tool or process launcher: z3_receipt = {"z3": {"ran": True, "verdict": "sat", "load_bearing": True}}
/Users/joshuaeisenhart/Codex-Ratchet/claimgate_plugin/fixtures/slop/S1_positive/literal_outcomes.py:3: S1 constant verdict outcome is attached to named tool 'solver', but no launcher is imported: solver.verdict = True
slop_gate: 2 suspect(s)
```

Exit: 1. This is the expected policy disposition for the positive fixture.

## Regression runner

`claimgate_plugin/run_slop_regression.py` declares 12 cases: positive and negative directories for S1-S6.

- A positive case expects `TRIP`: exit 1 and at least one finding for its own signature.
- A negative case expects `CLEAN`: exit 0 and no findings.
- Deviation in either direction fails.
- Distinct reasons include `SIGNATURE_MISSED`, `FALSE_POSITIVE`, `FIXTURE_MISSING`, and `NO_CASES_DECLARED`.
- Exit 0 means every declared fixture matched its recorded expectation.
- Exit 1 means a deviation.
- Exit 2 means usage error.

The runner writes `claimgate_plugin/results/slop_regression_v1.json`, so this documentation lane did not rerun it. The existing result records 12 cases, 32 fixture files, 24 of 24 negative files clean, all six signatures caught, zero deviations, and `promotion_allowed: false`. That result is a retained output, not a fresh run from this lane.

To add a signature, add both `fixtures/slop/SN_positive/` and `fixtures/slop/SN_negative/`, then add explicit `TRIP` and `CLEAN` cases. Do not use an aggregate threshold.

## CI report

`claimgate_plugin/ci_slop_report.py` scans a Git diff with the slop gate and also renders dependency findings.

```text
ci_slop_report.py --base BASE [--head HEAD] [--repo-root PATH]
                  [--summary PATH] [--annotations | --json]
```

Its exits are:

| Exit | Meaning |
|---:|---|
| 0 | no blocking slop findings; dependency advice may remain |
| 1 | blocking slop findings |
| 2 | usage, Git, ref, import, or execution precondition failure |

Only slop findings block in the current implementation. Dependency findings are advisory.

## Head-tree precondition is still broken

At this lane's start, Git reported these files as untracked:

```text
?? claimgate_plugin/ci_slop_report.py
?? claimgate_plugin/run_slop_regression.py
?? claimgate_plugin/slop_gate.py
```

They are absent from `HEAD`. A workflow that checks out the head tree and imports `slop_gate` therefore fails with `ModuleNotFoundError`. A passing scan from the working tree does not close that precondition.

Do not call the workflow load-bearing until the exact head used by CI contains the imported files and the workflow executes them.
