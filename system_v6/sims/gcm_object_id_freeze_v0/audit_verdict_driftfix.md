# Drift-Fix Fresh-Context Audit Verdict

Bottom line: FIX_SOUND.

The five-file drift fix preserves the frozen 1Q math identity, makes the 1Q body hash immune to later helper source edits, keeps 2Q/3Q/4Q registry hashes unchanged, and does not drop substrate verdict coverage. I found no math-content drift and no anti-tamper bypass.

Scope audited:

- `system_v6/sims/gcm_object_id_freeze_v0/gcm_object_id_freeze_v0.py`
- `system_v6/sims/gcm_object_id_freeze_v0/validate_gcm_object_id_freeze_v0.py`
- `system_v6/sims/gcm_2q_freeze_and_cut_v0/validate_gcm_2q_freeze_and_cut_v0.py`
- `system_v6/sims/gcm_3q_freeze_and_cuts_v0/validate_gcm_3q_freeze_and_cuts_v0.py`
- `system_v6/sims/gcm_4q_freeze_and_cuts_v0/validate_gcm_4q_freeze_and_cuts_v0.py`

Interpreter used:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
```

Important audit boundary: I did not run validator scripts as CLI entrypoints because they write `*_validator_results.json`. I imported the same validator functions and called them directly so the checkout stayed read-only except for this verdict file. The no-write harness rebuilt packets with `write=False`, monkeypatched helper behavior in memory, and used temporary files only for tamper checks.

## Falsifier 1 - Math Identity Preserved

PASS.

Evidence:

- Rebuilt 1Q `registry_body_sha256`: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- Recomputed 1Q body hash from rebuilt body bytes: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- Current committed-result 1Q body hash: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- Git HEAD 1Q body hash: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- `gcm_object_id`, `pinned_spec_sha256`, `frozen_registry`, and `counts` are byte-identical to git HEAD.
- Counts remain 16 survivors, 8 quotient classes, 6 candidate regions.
- Frozen helper source lock in rebuilt 1Q registry remains:
  - path: `scripts/gcm_substrate_check.py`
  - sha256: `e4bcfb05d7fd14e28b0a39df2c8f32b93a1a3f33263ad27b37820bbab0bb4a9d`
  - `git_last_commit: null`

Baseline validator-function errors:

```text
1Q: []
2Q: []
3Q: []
4Q: []
```

Downstream registry body hashes are unchanged:

- 2Q: `57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`
- 3Q: `623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0`
- 4Q: `bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de`

Result-file status check:

```bash
git diff --name-only -- system_v6/sims/gcm_object_id_freeze_v0/results system_v6/sims/gcm_2q_freeze_and_cut_v0/results system_v6/sims/gcm_3q_freeze_and_cuts_v0/results system_v6/sims/gcm_4q_freeze_and_cuts_v0/results
```

Observed: empty output. No result JSON diff was created by this audit.

## Falsifier 2 - Drift-Immunity Real

PASS.

Helper output-schema growth was simulated by monkeypatching every in-process `gcm_substrate_check` binding to return an extra nested field:

```text
new_schema_growth_field = {"added_by_audit": true, "nested": {"extra": "value"}}
```

The field appeared inside rebuilt helper-output controls for 2Q/3Q/4Q, proving the test actually exercised schema growth. All validators still returned empty errors:

```text
1Q: []
2Q: []
3Q: []
4Q: []
```

Pure helper source-sha/comment drift was simulated with a temporary helper copy containing only an appended audit comment:

- live helper sha256: `154308eda0fee494d2bc543028752fa8b29244c1abb97c7fe2ca8db19291ad74`
- temporary commented helper sha256: `13d6499eb3f5f97052ac8f4f0c63ff023613c06fa46c86b5ec246a1434a8a966`
- rebuilt 1Q body under the simulated helper path: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- frozen lock still: `e4bcfb05d7fd14e28b0a39df2c8f32b93a1a3f33263ad27b37820bbab0bb4a9d`

Validator-function errors under this pure helper-sha simulation:

```text
1Q: []
2Q: []
3Q: []
4Q: []
```

## Falsifier 3 - No Science Lost

PASS.

The excluded 2Q control subtrees are only raw helper return payloads:

- `substrate_positive_1q`
- `substrate_positive_2q`
- `substrate_lineage_free_negative_1q`
- `substrate_lineage_free_negative_2q`

Observed keys in those committed 2Q subtrees are only helper-return keys:

```text
errors, gcm_object_id, ok, registry_body_sha256, registry_path
```

The excluded 3Q and 4Q control subtrees are only the helper matrix:

- `controls.substrate_positive`
- `controls.substrate_negatives`

Observed keys are helper-return keys only:

```text
ok, errors, error_codes, registry_path, gcm_object_id, gcm_2q_object_id, gcm_3q_object_id, gcm_4q_object_id, registry_body_sha256
```

Rung-computed math remains outside the exclusions and still compared/asserted:

- 2Q still asserts counts, entropy rows, product/entangled separation, `one_q_regression`, and substrate positive/negative verdicts at validator lines 124-172.
- 3Q still asserts cut-table shapes, entropy fields, anchor profile, CKW, `two_q_regression`, substrate positives/negatives, and a live helper rerun at validator lines 109-159.
- 4Q still asserts cut-state availability, cut entropy/state fields, anchor profile, monogamy, `three_q_regression`, cut-state caveat resolution, substrate positives/negatives, and a live helper rerun at validator lines 113-170.

The exclusion does not remove math checks; it removes helper diagnostic-output shape from byte-reproduce comparison while retaining verdict assertions and live helper reruns.

## Falsifier 4 - Anti-Tamper Preserved

PASS.

Tamper A: changed the registry's frozen helper-lock sha to a wrong value.

Validator errors:

```text
registry drift against rebuilt output
substrate_check_helper frozen-at-birth lock mismatch
```

Tamper B: changed a survivor row in the 1Q registry.

1Q validator errors:

```text
registry drift against rebuilt output
unknown survivor in qcls_830aa0cdc681784fa290
valid substrate check failed
```

The helper also rejected the tampered registry with:

```text
ok: false
error_codes:
- GCM_REGISTRY_BODY_HASH_MISMATCH
- GCM_REGISTRY_IDENTITY_MISMATCH
- UNKNOWN_SURVIVOR_ID
- UNKNOWN_SURVIVOR_ID
- GCM_LINEAGE_CONSUMPTION_MISSING
```

Tamper C: fed wrong-substrate lineage to the helper.

Helper result:

```text
ok: false
error_codes:
- GCM_OBJECT_ID_MISMATCH
- UNKNOWN_SURVIVOR_ID
- UNKNOWN_SURVIVOR_ID
- GCM_LINEAGE_CONSUMPTION_MISSING
```

## Falsifier 5 - Not Papering Over Original Drift

PASS.

I executed the git-HEAD, unfixed `gcm_object_id_freeze_v0.py` source in memory and compared its naive rebuild against the committed registry body. The only differing paths were:

```text
source_locks.substrate_check_helper.git_last_commit
source_locks.substrate_check_helper.sha256
```

Naive unfixed rebuild body hash:

```text
4308e9b76e507ebc0bd7c173e5f46f1a581847e1281905c138501ec794b711c3
```

Committed body hash:

```text
0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed
```

Naive helper lock:

```text
git_last_commit: 84bcec53b
sha256: 154308eda0fee494d2bc543028752fa8b29244c1abb97c7fe2ca8db19291ad74
```

Committed helper lock:

```text
git_last_commit: null
sha256: e4bcfb05d7fd14e28b0a39df2c8f32b93a1a3f33263ad27b37820bbab0bb4a9d
```

After normalizing only `source_locks.substrate_check_helper` back to the committed row, the full body compared equal again:

```text
normalized_equal_after_helper_lock_restore: true
```

Math-carrying fields all matched:

```text
counts: true
frozen_registry: true
gcm_object_id: true
pinned_spec_sha256: true
```

This supports the H1 classification. I found no survivor/class/region/object/spec math byte drift.

## Overall Verdict

FIX_SOUND.

The fix should be committed as a registry body-hash drift fix that freezes helper provenance for the 1Q birth registry and excludes helper-output diagnostic schema from downstream byte-reproduce comparisons. It should not be described as a re-freeze, math refresh, new substrate, new registry identity, canonical-science promotion, or evidence that any stronger manifold/axis/engine claim now holds.

Commit must NOT claim:

- "re-froze the 1Q substrate"
- "updated the 1Q object identity"
- "changed survivor/class/region math"
- "revalidated downstream scientific claims"
- "promoted the packet beyond scratch_diagnostic"
- "canonical by process"
- "THE manifold"


---

## CONTROLLER ADDENDUM (2026-06-12) — grok blind panel + hardening (post-audit delta)

The FIX_SOUND verdict above audited the fix BEFORE a hardening pass. A grok-4.3 blind panel
(pre-registered falsifier) flagged a residual gap: excluding the helper-output control subtrees
from the byte-reproduce check removed the only coverage that would catch a helper REGRESSION that
stops rejecting lineage-free negatives — the validators re-ran only POSITIVES live. Confirmed in code
(2Q/3Q/4Q live re-runs asserted ok is True only; negatives were asserted against the frozen control).

HARDENING (in the committed version): added a LIVE negative-rejection re-run to the 2Q/3Q/4Q
validators — `gcm_substrate_check(common.lineage_free_variant(packet), registry).get("ok") is False`.
Strictly additive (more checking, cannot weaken anything).

EMPIRICAL PROOF (controller): injecting a helper regression (force ok=True / errors=[]) makes all 3
downstream validators go RED with the "live ... lineage-free negative did not fail" error; restoring
the helper returns all four to green; zero results.json drift throughout. The committed version is
STRONGER than both the pre-fix baseline (which had NO live negative gate) and the pre-hardening
version codex2 audited. Anti-collapse note: codex2 FIX_SOUND and the grok gap are BOTH real within
scope — the hardening closes the grok gap without disturbing the FIX_SOUND properties.
