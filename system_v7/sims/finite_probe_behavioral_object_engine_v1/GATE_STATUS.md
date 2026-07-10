# Gate Status

## Passed

- Wizard v4.3 object-preservation validation.
- Wizard v4.3 self-tests.
- Independent preregistration, symmetry-orbit, fixture, structural-holdout,
  and leakage-sentinel validation.
- Julia parse and exact execution.
- JAX syntax and exact execution.
- PyTorch/PyG syntax and full three-seed/control execution.
- Independent controller artifact validation.
- Four controller corruption tests: symmetry leakage, source hash, raw metric,
  and ceiling removal.
- `git diff --check` for the packet.

## Scientific Red

- Two of three PyTorch seeds fail the frozen global threshold.
- Shuffled-label control remains strongly positive.
- T9 adaptive replacement matrix was not run.
- Fabrication audit rejects learned-perception wording.

## Mechanical Red Or Drift

`scripts/lint_sim_contract.py` reports three `C5_missing_probe` findings for
`jax.numpy`, `jax.vmap`, and `jax.lax.fori_loop`. The packet carries executed
function-level receipts, but the repo linter additionally requires separately
registered capability-probe artifacts for those names. No decorative probe was
added to hide this requirement.

The sim-audit skill names `scripts/per_sim_contract.py` and
`scripts/max_deep_lego_gate.py`, but neither path exists in the current repo.
This is gate-documentation drift, not a green result.

## Leviathan

A read-only `lev exec` Sonnet review was launched. The Lev event stream records
`exec.started`, but no completion or receipt was emitted and `lev exec --status`
reported no active sessions. The attempt does not count as review evidence.
