# CocoIndex and Bloat Cleanup Receipt — 2026-06-17

Status: operational cleanup receipt and policy fence. This is not a sim admission surface and does not promote any result family.

## Scope

This pass addressed local retrieval/cache bloat and LLM findability for `/Users/joshuaeisenhart/Codex-Ratchet` plus the paired wiki. It did not delete authored source, sim evidence, audit verdicts, or legacy/provenance docs.

## Changes made

- Added repo-local ignore fence for CocoIndex cache:
  - `/.cocoindex_code/`
- Created repo MCP wrapper:
  - `/Users/joshuaeisenhart/.local/bin/cocoindex-codex-ratchet-mcp`
- Added Hermes MCP server:
  - `cocoindex_codex_ratchet`
- Reset/rebuilt local CocoIndex DBs with lean settings.
- Removed only local noise:
  - `.DS_Store` files
  - `.pytest_cache`

## Lean CocoIndex profile

Repo settings exclude bulky generated result/evidence JSON from the semantic map where possible:

- `**/results/*.json`
- `**/results/**/*.json`
- `**/*_results.json`
- `**/*_envelope_results.json`
- `**/*_envelope_spec.json`
- `**/*_trajectory_artifact.json`
- `**/*sample_matrices.json`
- `**/evidence/*.json`
- `**/evidence/**/*.json`

The files remain on disk and remain exact-read evidence when needed. They are just not allowed to dominate semantic retrieval by default.

## Measured state

Before cleanup/rebuild:

- repo total: about `2.6G`
- `.cocoindex_code`: about `1.4G`
- top durable content bloat: `system_v6/sims`, about `782M`
- largest generated result observed: `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_results.json`, about `289M`

After initial lean rebuild:

- repo total: `2.3G`
- `.cocoindex_code`: `1.1G`
- chunks: `189047`
- languages: python `138086`, markdown `24561`, json `12938`, text `12102`, javascript `768`, yaml `214`, bash `145`, toml `119`, html `114`

That still missed the requested `400-700M` working-tree target. The corrected sequence was: shrink generated repo payload first, then rebuild CocoIndex over the smaller/current corpus.

After generated-result gzip + current-surface CocoIndex rebuild:

- repo total with CocoIndex kept: `623M`
- `.cocoindex_code`: `63M`
- chunks: `10069`
- files: `771`
- languages: markdown `9979`, toml `90`
- remaining uncompressed generated result JSON files >= `1M`: `0`

Interpretation: the working tree now lands inside the requested `400-700M` size band while keeping a local CocoIndex semantic map. The index is current-surface/router oriented; exact code, legacy docs, JSON specs, and gzipped evidence remain available by file reads.

## Smoke-search receipts

The lean repo index returned strong hits for both conceptual and contract queries.

Query: `geometric constraint manifold M(C) root constraints finitude noncommutation`

Representative hits:

- `system_v4/docs/PROTO_RATCHET_ALLOWED_MATH_CHART.md`
- `system_v5/READ ONLY Reference Docs/Axis 0 rough and drifty. NOT CANON.md`
- `system_v4/docs/PROTO_RATCHET_ROOT_TO_ALLOWED_MATH_HANDOFF.md`
- `system_v5/docs/foundation_build_spine.md`

Query: `promotion_allowed formal_admission_allowed classification scratch diagnostic sim result contract`

Representative hits:

- `system_v5/docs/session_20260606_physics_excavation/17_CODEX_DEEP_AUDIT_CLAUDE_WAVE_RECEIPTS.md`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/audit_verdict.md`
- `system_v6/receipts/promotion_checklist_super_sim_v0_20260612.md`
- `system_v6/sims/matrix64_behavior_match_v0/builder_self_assessment.md`
- `system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md`

## Cleanup classes

| Class | Examples | Policy |
|---|---|---|
| Local cache | `.cocoindex_code/`, `.pytest_cache/`, `.DS_Store` | Safe to delete/reset when no process is using it; keep ignored. |
| Generated evidence | `system_v6/sims/**/results/*.json`, envelope outputs | Do not delete casually; archive/compress only with manifest, checksum, and restore path. |
| Authored source/control | source files, specs, validators, audit verdicts | Keep visible unless explicitly retired. |
| Legacy/provenance | system_v4/v5 docs, read-only legacy docs | Preserve unless a named archive policy supersedes them. |
| Archive candidate | huge result JSON after compact verdict/router exists | Candidate only after summary + checksum + restore command. |

## Archive/compression gate

A large generated result may be moved/compressed only after a manifest records:

1. original path;
2. byte size;
3. SHA-256 checksum;
4. archive destination;
5. restore command;
6. whether any validator/test expects the original path;
7. replacement small router/summary path.

Until that exists, the safe action is to keep the result file in place and exclude it from semantic indexing.

## Next admissible tranche

Start with one folder, probably the largest generated-result family:

- `system_v6/sims/gcm_constraint_carve_6q_v0/`

Dry-run manifest now exists:

- `system_v6/receipts/gcm_constraint_carve_6q_v0_archive_dry_run_manifest_20260617.json`

Observed by manifest:

- file count in target folder: `18`
- hashed candidates: `6`
- largest file: `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_results.json`, `303318038` bytes
- filename reference hits: `7`
- sim-id reference hits: `79`
- mode: `dry_run_no_moves_no_compression`

Recommended dry-run only:

1. inventory files and sizes;
2. hash huge result files;
3. identify validators/readers that reference those paths;
4. write a compression manifest;
5. write or confirm a small `README.md` / audit summary that preserves LLM findability;
6. only then compress/move if the restore path is clean.

Do not run broad recursive deletion or compression across `system_v6/sims` without a reviewed manifest.

## Final compact-size receipt

Final verified state after the approved compact rebuild:

- repo size with CocoIndex kept: `623M`
- CocoIndex size: `63M`
- `system_v6/sims` after gzip: about `144M`
- gzip manifest: `system_v6/receipts/generated_result_json_gzip_manifest_20260617.json`
- gzip records checked by decompressed SHA-256: `58`
- generated-result JSON saved by gzip: `653.4M`

CocoIndex profile now excludes old systems and evidence bulk from semantic indexing:

- excluded from index: `system_v4/**`, `system_v5/**`, `READ ONLY Legacy core_docs/**`, `*.json`, `*.jsonl`, `*.json.gz`, `*.gz`
- included in index: top-level markdown/config, `docs/**/*.md`, `receipts/**/*.md`, `system_v6/**/*.md`, `system_v7/**/*.md`, and small yaml/toml routing files

This does not delete or de-authorize legacy/current exact files. It only stops local semantic indexing from carrying the whole historical/code/evidence estate.
