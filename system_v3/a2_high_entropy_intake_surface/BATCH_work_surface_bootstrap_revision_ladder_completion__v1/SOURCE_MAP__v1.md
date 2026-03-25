# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_work_surface_bootstrap_revision_ladder_completion__v1`
Extraction mode: `BOOTSTRAP_REVISION_LADDER_PASS`
Batch scope: remaining `work/out` bootstrap revision ladder from `SYSTEM_REPAIR_BOOTSTRAP_v3__rev4` through `rev9` plus `SYSTEM_REPAIR_BOOTSTRAP_v4__rev2`
Date: 2026-03-09

## 1) Folder-Order Selection
- primary bootstrap revision family:
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev4.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev5.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev6.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev7.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev8.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev9.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev9.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v4__rev2.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v4__rev2.zip.sha256`
- bundling reason:
  - this is one contiguous spillover bootstrap ladder with explicit outer revisioning
  - `v3__rev4` through `v3__rev8` behave like a stable plateau:
    - same entry count
    - same embedded `00_READ_FIRST.md` hash
    - same embedded `SYSTEM_SAVE_PROFILE_MANIFEST_v1.json` hash
    - different outer zip hashes and byte sizes
  - `v3__rev9` is the first internal-content break:
    - read-first label changes from `v2` to `v3`
    - save-profile hash changes
    - three `system_v3` payload files are added
  - `v4__rev2` is the next break:
    - save-profile file count drops back to `641`
    - bootstrap layer gains a larger runtime-lock/control spine
    - sidecar adoption becomes explicit
- deferred next docs in folder order:
  - no additional `SYSTEM_REPAIR_BOOTSTRAP*` files remain in `work/out` after `SYSTEM_REPAIR_BOOTSTRAP_v4__rev2.zip.sha256`

## 2) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev4.zip`
  - sha256: `2bdba4bd8215d3a59f6db0d7fce240e5aa89981bc7609aeb17fe61fad33f57bb`
  - size bytes: `2964961`
  - entry count: `689`
  - readable status in this batch: bootstrap ladder plateau member
  - source-class note:
    - first remaining `v3` revision in the ladder; embedded read-first still self-labels as `SYSTEM_REPAIR_BOOTSTRAP_v2`
- source 2:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev5.zip`
  - sha256: `cbffa31c4e1f0eb918d847525bc9c5fcfb4150069c6aa732bb5a628fcdf9ca75`
  - size bytes: `2964674`
  - entry count: `689`
  - readable status in this batch: bootstrap ladder plateau member
  - source-class note:
    - same embedded read-first and save-profile hashes as `rev4` despite a different outer zip hash
- source 3:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev6.zip`
  - sha256: `98bd5ac7bdc205510d39269ccea06687276d28641a2963d053fe7c67ab67e02b`
  - size bytes: `2965063`
  - entry count: `689`
  - readable status in this batch: bootstrap ladder plateau member
  - source-class note:
    - still on the same internal plateau
- source 4:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev7.zip`
  - sha256: `0b100d8a38f6e2ce01322ce3d39044088a482ad128b7a58b4b52e2435b239277`
  - size bytes: `2965093`
  - entry count: `689`
  - readable status in this batch: bootstrap ladder plateau member
  - source-class note:
    - same key embedded control hashes as `rev4` through `rev6`
- source 5:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev8.zip`
  - sha256: `9bcc8cbcc50c1ee2281ae228d264fbb663e559d739d6825c683a669cb109d9f3`
  - size bytes: `2964982`
  - entry count: `689`
  - readable status in this batch: bootstrap ladder plateau member
  - source-class note:
    - last plateau revision before the internal-content break at `rev9`
- source 6:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev9.zip`
  - sha256: `ee9f3dbf05592973f4b0e4e976b87a26cd890813668aac3adae819991d99047e`
  - size bytes: `2982798`
  - entry count: `691`
  - readable status in this batch: bootstrap ladder break revision
  - source-class note:
    - embedded read-first now says `SYSTEM_REPAIR_BOOTSTRAP_v3`
    - embedded save-profile manifest changes from `641` to `644`
    - three `system_v3` payload files are added relative to the plateau
- source 7:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v3__rev9.zip.sha256`
  - sha256: `07fe67c16b42c40a5bed0efc61acd0f376b1835be7bc5f00d02ff1575e0ad050`
  - size bytes: `65`
  - line count: `1`
  - readable status in this batch: detached checksum sidecar
  - source-class note:
    - first bootstrap sidecar present in the remaining `v3` ladder
- source 8:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v4__rev2.zip`
  - sha256: `3fb1e3be9bdc144c6c6226320db6db63ba0adb0daa2d2792e0f6216dcdb1b981`
  - size bytes: `3181248`
  - entry count: `714`
  - readable status in this batch: `v4` bootstrap ladder continuation
  - source-class note:
    - keeps the `v4` read-first label and save-profile `641` count while expanding the bootstrap control layer beyond `v3__rev9`
- source 9:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/SYSTEM_REPAIR_BOOTSTRAP_v4__rev2.zip.sha256`
  - sha256: `edb6610e6cb2ea1973c216e8f17efb48986c4304e48af7e4b49549aa011ced19`
  - size bytes: `65`
  - line count: `1`
  - readable status in this batch: detached checksum sidecar
  - source-class note:
    - shows the same one-line digest style as other `work/out` sidecars

## 3) Structural Map
### Segment A: stable `v3` plateau with drifting outer archives
- sources:
  - `v3__rev4`
  - `v3__rev5`
  - `v3__rev6`
  - `v3__rev7`
  - `v3__rev8`
- key markers:
  - all have `689` entries
  - all have identical embedded `00_READ_FIRST.md` hash:
    - `38088b664c6d71a540d022599a6f9c4d0fd77e127f182f6878da22cbef47e841`
  - all have identical embedded `SYSTEM_SAVE_PROFILE_MANIFEST_v1.json` hash:
    - `9ee31fc22b75413f8cea95bbac71cc75b2b989e8c4c648c389277e0f60537d7e`
  - outer zip sizes and hashes still vary
- strongest read:
  - this plateau behaves like packaging churn around a stable embedded payload set

### Segment B: long-lived internal self-label lag
- source:
  - embedded `SYSTEM_REPAIR_BOOTSTRAP_v3/BOOTSTRAP/00_READ_FIRST.md` in `rev4` through `rev8`
- key markers:
  - top line remains `SYSTEM_REPAIR_BOOTSTRAP_v2 (built 2026-03-04 06:02:08Z UTC)`
  - no runtime-canon or append-log read-first sections
- strongest read:
  - five successive `v3` revisions preserve an outdated internal identity surface

### Segment C: `rev9` internal-content break
- sources:
  - `v3__rev9`
  - normalized diff against the plateau save-profile membership
- key markers:
  - entry count rises from `689` to `691`
  - read-first top line becomes `SYSTEM_REPAIR_BOOTSTRAP_v3`
  - save-profile `file_count` rises from `641` to `644`
  - added save-profile members:
    - `system_v3/runtime/bootpack_b_kernel_v1/a1_autowiggle.py`
    - `system_v3/runtime/bootpack_b_kernel_v1/tests/test_state_seed_sets.py`
    - `system_v3/tools/build_pro_boot_job_zip.py`
- strongest read:
  - `rev9` is the first remaining `v3` revision where the internal bootstrap story and saved system payload both change

### Segment D: `v4__rev2` split between leaner save profile and richer bootstrap spine
- sources:
  - `v4__rev2`
  - normalized diff against `v3__rev9`
- key markers:
  - read-first label remains `SYSTEM_REPAIR_BOOTSTRAP_v4`
  - save-profile `file_count` returns to `641`
  - save-profile drops the three `v3__rev9` additions
  - bootstrap layer adds:
    - `BOOTSTRAP/CORE/APPEND_LOG_ARCHITECTURE_v1.md`
    - `BOOTSTRAP/CORE/APPEND_LOG_PROTOCOL_v1.md`
    - `BOOTSTRAP/CORE/BATCH_GENERATION_PROTOCOL_v1.md`
    - `BOOTSTRAP/CORE/CANON_LOCK_CROSSCHECK_v1.md`
    - `BOOTSTRAP/CORE/DEGREE_OF_FREEDOM_DISCOVERY_PROTOCOL_v1.md`
    - `BOOTSTRAP/CORE/INTEGRATION_MAP__GROUND_TRUTH_TO_RUNTIME__v1.md`
    - `BOOTSTRAP/CORE/PATH_FAMILY_PROTOCOL_v1.md`
    - `BOOTSTRAP/CORE/SPINNER_ENGINE_PROTOCOL_v1.md`
    - `BOOTSTRAP/CORE/SYSTEM_RUNTIME_CANON_v1.md`
- strongest read:
  - `v4__rev2` tightens the overlay/control shell while slimming the saved system payload back down

### Segment E: late and uneven sidecar adoption
- sources:
  - `v3__rev9.zip.sha256`
  - `v4__rev2.zip.sha256`
- key markers:
  - one-line digests only
  - no adjacent sidecars exist for `v3__rev4` through `v3__rev8`
- strongest read:
  - bootstrap sidecar integrity shows up late in the ladder and remains minimally descriptive

## 4) Structural Quality Notes
- this batch is useful because it isolates a complete bootstrap revision subfamily:
  - stable plateau
  - `rev9` break
  - `v4__rev2` control-spine expansion
- the family is not current law:
  - every artifact is a `work/out` spillover export
  - read-first and verify plaques describe intended bundle discipline, not proof of downstream installation
  - embedded save-profile manifests are sampled as packaging evidence, not active runtime truth surfaces
- important contradictions preserved:
  - five `v3` revisions keep a `v2` internal label
  - `rev9` increases saved payload count, but `v4__rev2` reduces it again while still making the outer bundle larger
  - sidecar integrity arrives late and remains weaker than self-describing ledgers

## 5) Source-Class Read
- best classification:
  - bootstrap packaging revision archaeology
  - migration-debt and export-scope evolution packet
- not best classified as:
  - active bundle law
  - proof that any bootstrap revision was executed successfully
  - semantic admission of every bundled source file under `SYSTEM/`
- likely trust placement under current A2 rules:
  - useful for mapping packaging stabilization attempts, internal label lag, and bootstrap-vs-save-profile scope splits
  - not sufficient to outrank active `system_v3` control surfaces
