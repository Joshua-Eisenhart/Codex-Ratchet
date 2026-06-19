# 1Q Registry Body-Hash Drift Investigation (2026-06-12)

## Bottom Line

Classification: H1, benign frozen-body metadata drift, not H2 carve/source math drift.

The rebuilt `gcm_object_id_freeze_v0` registry body differs from the committed body only in the `source_locks.substrate_check_helper` metadata row:

- committed body row: `git_last_commit: null`, `sha256: e4bcfb05d7fd14e28b0a39df2c8f32b93a1a3f33263ad27b37820bbab0bb4a9d`
- rebuilt body row: `git_last_commit: "84bcec53b"`, `sha256: 154308eda0fee494d2bc543028752fa8b29244c1abb97c7fe2ca8db19291ad74`

The math carrier is stable. The committed and rebuilt bodies have byte-identical:

- `gcm_object_id`: `gcmobj_a40e54e13cec01466c9d675028b3574b`
- `pinned_spec_sha256`: `a40e54e13cec01466c9d675028b3574b29263ce3179bea8768970ac490f8245c`
- 16 survivor rows and survivor IDs
- 8 quotient-class rows and quotient-class IDs
- 6 candidate-region rows and candidate-region IDs
- counts: 16 survivors, 8 quotient classes, 6 candidate regions

Fix scope: canonicalize the frozen body contract so mutable helper provenance for `scripts/gcm_substrate_check.py` does not silently change the 1Q frozen object body hash, then repin `EXPECTED_REGISTRY_BODY_SHA256` once after a controlled refresh. Do not re-freeze the carve math; the survivor/class/region content did not drift.

## Hash Input

The freeze packet computes the registry body hash in `system_v6/sims/gcm_object_id_freeze_v0/gcm_object_id_freeze_v0.py`:

```python
def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()
```

`build_registry()` constructs `registry`, then calls:

```python
registry["registry_body_sha256"] = canonical_sha256(registry)
```

So the hashed bytes are the canonical JSON bytes of the full registry object before `registry_body_sha256` is inserted. The hash input has sorted keys, compact separators, ASCII escaping, and no trailing newline.

## Rebuild Versus Committed Body

Command shape used:

```bash
python3 - <<'PY'
# import gcm_object_id_freeze_v0, rebuild in memory, load git show HEAD registry,
# remove registry_body_sha256 from each, canonicalize with the packet's serializer,
# compare bytes and fields
PY
```

Observed hashes:

- committed recorded: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- committed recomputed from committed body bytes: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- rebuilt recorded: `4308e9b76e507ebc0bd7c173e5f46f1a581847e1281905c138501ec794b711c3`
- rebuilt recomputed from rebuilt body bytes: `4308e9b76e507ebc0bd7c173e5f46f1a581847e1281905c138501ec794b711c3`
- committed body length: `14057`
- rebuilt body length: `14064`

Exact first differing byte region:

```text
committed:
..."substrate_check_helper":{"exists":true,"git_last_commit":null,"path":"scripts/gcm_substrate_check.py","sha256":"e4bcfb05d7fd14e28b0a39df2c8f32b93a1a3f33263ad27b37820bbab0bb4a9d"}},"standards_version":"audit_standards_codex_v1"}

rebuilt:
..."substrate_check_helper":{"exists":true,"git_last_commit":"84bcec53b","path":"scripts/gcm_substrate_check.py","sha256":"154308eda0fee494d2bc543028752fa8b29244c1abb97c7fe2ca8db19291ad74"}},"standards_version":"audit_standards_codex_v1"}
```

Normalizing only this row in the rebuilt body back to the committed values makes the full body equal again:

- `normalized_equal: True`
- `normalized_sha: 0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`

This rules out key ordering, float formatting, set iteration, or changed survivor/class/region math as the cause.

## Helper Provenance Check

Current HEAD helper provenance:

```text
git log -n 1 --oneline -- scripts/gcm_substrate_check.py
84bcec53b 4Q FREEZE/CUTS COMMITTED ...
```

Current helper bytes:

```text
git show HEAD:scripts/gcm_substrate_check.py | shasum -a 256
154308eda0fee494d2bc543028752fa8b29244c1abb97c7fe2ca8db19291ad74

shasum -a 256 scripts/gcm_substrate_check.py
154308eda0fee494d2bc543028752fa8b29244c1abb97c7fe2ca8db19291ad74
```

Interpretation: the committed registry body captured `scripts/gcm_substrate_check.py` at an earlier uncommitted helper state (`git_last_commit: null`, sha `e4bc...a9d`). Current in-memory rebuild captures the later committed helper state (`84bcec53b`, sha `1543...ad74`). The registry body hash therefore changed because mutable helper provenance is embedded in the body hash input.

## Math-Stability Check

Fresh in-memory rebuild from current source matched the committed registry on all math-carrying frozen content:

```text
survivor_count 16 16
survivor_ids_equal True
quotient_class_ids_equal True
candidate_region_ids_equal True
frozen_registry_equal True
pinned_spec_sha256_equal True a40e54e13cec01466c9d675028b3574b29263ce3179bea8768970ac490f8245c
object_id_equal True gcmobj_a40e54e13cec01466c9d675028b3574b
```

No H2 source drift was found in the carve source, survivor set, quotient classes, candidate regions, or object ID.

## Blast Radius

Command:

```bash
git grep -l "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed" HEAD -- system_v6 scripts docs Makefile
```

Result: 113 committed files cite or pin the old 1Q body hash across these committed packets/surfaces:

```text
scripts/gcm_substrate_check.py
system_v6/sims/engine_16_stage_correspondence_v1
system_v6/sims/gcm_2q_freeze_and_cut_v0
system_v6/sims/gcm_3q_freeze_and_cuts_v0
system_v6/sims/gcm_4q_freeze_and_cuts_v0
system_v6/sims/gcm_connection_flux_attach_v0
system_v6/sims/gcm_constraint_carve_3q_v1
system_v6/sims/gcm_constraint_carve_4q_v0
system_v6/sims/gcm_constraint_carve_5q_v0
system_v6/sims/gcm_constraint_carve_6q_v0
system_v6/sims/gcm_entropy_family_sweep_v0
system_v6/sims/gcm_flux_strips_v0
system_v6/sims/gcm_g2_licensing_attach_v0
system_v6/sims/gcm_geometry_attach_2q_v0
system_v6/sims/gcm_geometry_attach_2q_v1
system_v6/sims/gcm_geometry_attach_v0
system_v6/sims/gcm_nesting_tower_le2q_v0
system_v6/sims/gcm_nesting_tower_le3q_v0
system_v6/sims/gcm_object_id_freeze_v0
system_v6/sims/gcm_qca_runner_2q_v0
system_v6/sims/gcm_qca_runner_2q_v1
system_v6/sims/gcm_ratchet_order_matrix_v0
system_v6/sims/gcm_ratchet_order_matrix_v1
system_v6/sims/gcm_ring_checkerboard_runner_v0
system_v6/sims/gcm_ring_checkerboard_runner_v1
system_v6/sims/gcm_runtime_flux_3q_v0
system_v6/sims/gcm_runtime_flux_3q_v1
```

If a repin is performed, sweep these surfaces plus the frozen registry and helper pin. Because this is H1 metadata drift, the sweep should be a controlled registry-body/provenance repin, not a scientific re-freeze of the 1Q survivor object.

