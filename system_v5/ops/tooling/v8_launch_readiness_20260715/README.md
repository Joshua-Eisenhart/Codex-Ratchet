# V8 code-only launch-readiness audit

This directory implements a deterministic cross-system prelaunch audit. Its
successful result is `HOLD_NOT_READY`: green means that the code observed the
required honest boundaries and kept launch closed.

The auditor does not call NVIDIA, xAI, Claude, or another model provider. It
reads the existing NVIDIA/xAI catalog and quota-preflight receipts, and it uses
Claude Bridge only in `--dry-run` mode. Provider and LLM output is explicitly
non-gating.

## Enforced evidence

- the isolated QIT/Julia integration-repair receipt and independent validation
  are green, current by file hash, and non-promotional;
- V0 is mechanically green but semantic forcing is false, the decision is
  `HOLD_DESIGNED_SURROGATE`, and Ratchet state remains `OPEN`;
- V1 is a sealed preregistration and its Julia/JAX/PyTorch builders remain
  absent;
- NVIDIA and xAI catalogs pass their local validator, while both dispatch
  preflights remain `HOLD` with `quota_unknown`;
- the repo-held Claude Bridge passes its 20 local tests and writes a validated
  non-gating `fable5 -> fable` dry-run receipt;
- the supplied frozen campaign remains nonofficial and red, with the diagnostic
  preserving its unexpected QIT red;
- the supplied Lev worktree is clean, exactly at the caller-supplied commit,
  and contains the three expected evidence-repair paths. This is source-branch
  identity only and is not treated as Lev process admission.

All inputs and relevant validator sources are SHA-256 bound into the readiness
receipt. The independent validator reopens those paths, checks their current
hashes and semantics, confirms the live Lev Git state, and runs eight negative
mutations against itself.

## Run

```bash
python3 -B system_v5/ops/tooling/v8_launch_readiness_20260715/run_readiness_audit.py \
  --frozen-campaign-root /absolute/path/to/system_v7/sims/v8_nonofficial_stress_campaign_20260715 \
  --lev-worktree /absolute/path/to/lev-repair-worktree \
  --expected-lev-commit FULL_40_CHARACTER_SHA

python3 -B system_v5/ops/tooling/v8_launch_readiness_20260715/validate_readiness_receipt.py

python3 -B -m unittest discover \
  -s system_v5/ops/tooling/v8_launch_readiness_20260715 \
  -p 'test_readiness_audit.py' -v
```

The runner and validator return zero only when all expected-state checks are
true and all launch, promotion, admission, release, and science flags remain
false. Missing inputs, changed hashes, a provider quota opening, an LLM gaining
gate authority, a V0 semantic flag flipping, a V1 builder appearing, a frozen
red disappearing, or Lev Git drift fails closed.

## Outputs

- `results/readiness_receipt.json`
- `results/readiness_validation.json`
- `results/claude_dry_run/` prompt, dry output, and non-gating bridge receipt

These artifacts support only a bounded readiness diagnosis. They cannot admit
a Ratchet tooth or authorize an official V8 launch.
