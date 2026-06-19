# Estate Lineage Remediation 2026-06-10

Outcome: PASS with scoped caveat for active mutation folders.

## `/tmp` Directive Refs

The missing-things audit named two `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md` source refs inside `geo_s3_density_observable_v0` and `geo_s4_operator_stage_v0` result surfaces. The current card forbids touching `geo_s3_density_observable_v0` and `geo_s4_operator_stage_v0`, so those result JSONs were not edited.

External-prompt marker applied by ledger, not by result rewrite:

- marker: `external_prompt_source_unavailable_for_committed_hash_claim`
- scope: `geo_s3_density_observable_v0`, `geo_s4_operator_stage_v0`
- consequence: these refs are not treated as committed source-hash evidence by the estate convention/value scripts.
- next admissible edit when folders are released: replace the `/tmp` source path with the committed `directive_addendum.md` path or a committed copied-source path and regenerate the affected packet.

## MCT Wiki Source Hash Receipts

The MCT dynamic packet cites absolute wiki sources. This receipt captures file-level hashes for the cited wiki slices; the result JSON remains unchanged.

| Key | Cited ranges | File SHA-256 |
| --- | --- | --- |
| `field_wide_contract` | `123-203,211-232,288-305` | `e3ad53635175132bdcfb0630bdf1c63a26ffac8ae874d6159cc468c4f861650e` |
| `formal_geometry` | `78-88,157-166` | `5bc364ba80e00c46845fa2eb769dc727cb5c6cb9958b223d18158699eb6ddf84` |
| `terrain_math` | `43-49,51-152` | `4ac153b4da35e80b4ae64fcb7cc96a89edf49f7efce271e22b0bcef89b918875` |
| `runbook` | full cited file | `24668e05a649427a622fe929971dc354ec22d20f0820b5d6bbe096625e78c9ed` |

## Canon Algebra Artifact Receipt

The broken ignored result-estate path is retargeted to a commit-visible receipt:

- legacy ignored path: `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json`
- commit-visible receipt: `system_v6/receipts/canon_algebra_artifact_v1_results_20260610.json`
- artifact hash: `824a0a2c794a949a83e4bd650c9620464b96eb0d1dcb3d0fe4901a4e86d05f2c`
- generator hash: `029907bc4729cac16a69579a5a1291674adb25f18582e65ad48d5bae48b10a09`
- retargeted receipt hash: `f2330380ede51ffeb0c04a6ab62fa8243d59c995aecda8b012b18de759a0e947`
- added consumer-facing aliases: `proof_tag`, `table_version`, `bracket_convention`
