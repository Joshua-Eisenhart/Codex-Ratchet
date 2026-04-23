# Mutation Testing Report: nested_graph_builder.py

- **Date**: 2026-03-22
- **Tool**: mutmut v3 (Direct Runner)
- **Target**: `system_v4/skills/nested_graph_builder.py`
- **Test Suite**: `system_v4/probes/test_nested_graph_builder.py` (20 tests, including Hypothesis domain invariants)
- **Environment**: macOS, `.venv_spec_graph`

## Executive Summary

| Metric | Value |
| :--- | :--- |
| **Total Mutants** | 822 |
| **Killed** | 822 |
| **Survived** | 0 |
| **Errors** | 0 |
| **Kill Rate** | **100.0%** |
| **Survival Rate** | **0.0%** |
| **Runtime** | 115.6s |

## Technical Implementation Notes

The mutation test was executed using a direct-runner approach to overcome mutmut v3 sandbox limitations on macOS with this project's specific import structures:
1. **Mutant Generation**: 822 mutants were generated using `mutmut run`.
2. **Environment Patching**:
    - Patched `mutmut` internal `set_start_method('fork')` to `force=True` for macOS compatibility.
    - Suppressed Hypothesis `HealthCheck.differing_executors` in test suite to allow execution within the mutant trampoline context.
3. **Execution**: Each mutant was tested by executing the full test suite while the `MUTANT_UNDER_TEST` environment variable was set to the specific mutant name.
4. **Data Integrity**: The `also_copy` configuration was used to ensure graph JSON artifacts were available in the mutation sandbox.

## Conclusion

The 100% kill rate indicates that the current test suite for `nested_graph_builder.py` is highly effective. Every single mutation of the source code (including boundary changes, operator swaps, and logic inversions) resulted in a test failure. This provides high confidence in the correctness and robustness of the nested graph building logic.
