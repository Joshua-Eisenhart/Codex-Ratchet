# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_spec_stage2_public_conformance__v1`
Extraction mode: `ACTIVE_SPEC_STAGE2_AND_PUBLIC_BOUNDARY_PASS`
Batch scope: second bounded active-system pass over `specs/20..30`, spec-adjacent baseline/schema surfaces, the full `conformance/fixtures_v1` pack, and `public_facing_docs/`
Date: 2026-03-09

## 1) Folder-Order Selection
- prior bounded batch ended with:
  - top-level `system_v3` docs
  - `specs/00..19`
  - `specs/ZIP_PROTOCOL_v2.md`
- this bounded continuation selects:
  - `specs/20..30`
  - `specs/_normative_hash_baseline.json`
  - `specs/schemas/*.schema.json`
  - `conformance/fixtures_v1/*`
  - `public_facing_docs/*`
- bundling reason:
  - these files stay in the same low-entropy active packet:
    - tuning/build/release gates
    - run-surface scaffolding
    - naming freeze
    - bootpack worker bootpacks
    - controller process
    - schema stubs
    - conformance fixture pack
    - public explanatory boundary docs
  - the conformance and public-facing surfaces are small and heavily coupled to this late-spec packet
  - the schema stubs and baseline digest are spec-adjacent source-like surfaces and should not be silently skipped
- deferred next docs in priority order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_INPUT_TRUST_AND_QUARANTINE_MAP__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/ALT_MODEL_MINING_PLAYBOOK.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/COUPLED_RATCHET_AND_SIM_LADDERS__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/DOC_INDEX_STATUS_CAUTION__v1.md`

## 2) Source Membership By Family
- late spec-owner and build packet:
  - `specs/20..23`
- naming, worker-bootpack, controller, schema-flow, and browser-automation packet:
  - `specs/24..30`
  - `specs/_normative_hash_baseline.json`
  - `specs/schemas/*.schema.json`
- conformance fixture pack:
  - `conformance/fixtures_v1/README.md`
  - `expected_outcomes.json`
  - `manifest.json`
  - `observed_results.template.json`
  - twelve minimal fixture payloads
- public-facing explanatory packet:
  - three `public_facing_docs/*.md` surfaces
- full hashes, sizes, and line counts are preserved in `MANIFEST.json`

## 3) Tuning / Build / Run-Surface Contract Packet
- `specs/20_CONTROLLED_TUNING_AND_UPGRADE_CONTRACT.md:9-127`
  - tuning proposal schema, class gates, replay contract, tuning graveyard, and promotion gate
- `specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md:12-128`
  - phased build sequence `P0..P7`, survivor significance gate, release checklist, and loop-health addendum
- `specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md:9-299`
  - deterministic run-surface scaffolding, gate-producer tools, phase-pipeline tool, real-loop helper, and fail-closed conditions
- `specs/23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md:12-103`
  - fixture-pack schema, required rule families, runner output contract, and promotion blocking behavior

## 4) Naming / Bootpack / Controller / Stage Packet
- `specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md:20-140`
  - batch-first naming grammar, field order, length limits, and immediate adoption targets
- `specs/25_BOOTPACK_A2_REFINERY__v1.md:10-73`
  - strict A2 extraction lane bootpack with invariant-lock and completeness requirements
- `specs/26_BOOTPACK_A1_WIGGLE__v1.md:10-61`
  - A1 multi-lane wiggle bootpack with graveyard update contract
- `specs/27_BOOTPACK_RATCHET_FUEL_MINT__v1.md:9-49`
  - strict fuel-packet packaging contract
- `specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md:16-209`
  - active/provisional controller role for fresh-thread worker dispatch and weak-lane correction
- `specs/28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md:10-27`
  - schema-stub inventory and fail-closed Stage-2 expectations
- `specs/29_STAGE_3_TEMPLATE_AND_SCHEMA_GATE_FLOW__v1.md:9-47`
  - one concrete bundle path and schema-gate flow
- `specs/30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md:13-50`
  - local browser automation protocol for ZIP-in/ZIP-out Web UI reasoning

## 5) Baseline And Schema-Stubs Packet
- `_normative_hash_baseline.json`
  - tiny detached digest surface with:
    - `clause_count`
    - `normative_hash_sha256`
- schema stubs:
  - `A1_BRAIN_ROSETTA_UPDATE_PACKET_STAGE2_v1.schema.json`
  - `A2_BRAIN_UPDATE_PACKET_STAGE2_v1.schema.json`
  - `RATCHET_FUEL_CANDIDATE_PACKET_STAGE2_v1.schema.json`
  - `ZIP_JOB_MANIFEST_STAGE2_v1.schema.json`
- best read:
  - these are Stage-2 hardening surfaces for proposal/job packets
  - they are validation-oriented and still explicitly below active compile-law status

## 6) Conformance Fixture Pack
- pack-level surfaces:
  - `README.md`
  - `expected_outcomes.json`
  - `manifest.json`
  - `observed_results.template.json`
- fixture families actually present:
  - dependency forward reference
  - derived-only primitive use
  - evidence ingest pass/reject
  - formula glyph reject
  - lexeme undefined-component park
  - message discipline pass/reject
  - near-duplicate park
  - probe pressure park
  - schema header reject
  - undefined-term reject
- source-class read:
  - concrete minimal test-vector surface, not prose doctrine
  - high reuse value for later comparison against runtime and bootpack-B claims

## 7) Public-Facing Boundary Packet
- `00_PUBLIC_FACING_SYSTEM_INTENT_AND_CONSTRAINTS_ON_INTERPRETATION_v1.md:7-50`
  - newcomer-facing description of what the system is and is not
- `01_PUBLIC_FACING_LAYERED_ARCHITECTURE_AND_ENTROPY_BOUNDARY_v1.md:7-62`
  - public description of A2/A1/A0/B/SIM roles and entropy compression boundary
- `02_PUBLIC_FACING_FLOWMIND_A3_HOSTING_INTERFACE_CONTRACT_v1.md:7-49`
  - public host/substrate interface contract that keeps A3 orchestration above the sealed kernel boundary
- source-class read:
  - public explanatory overlays
  - useful for boundary communication
  - not authoritative over active internal control surfaces

## 8) Source-Class Read
- best classification:
  - active low-entropy extension packet around release/build discipline, worker packaging, test fixtures, and outward-facing explanation
- strongest direct value:
  - concrete bridge from owner-model specs into run scaffolding and fixture validation
  - explicit worker-lane packaging bootpacks
  - explicit controller-thread process surface
  - concrete public explanation of the entropy boundary
- caution:
  - several surfaces are explicitly stubs, projections, public docs, or provisional controller process
  - the conformance pack reveals behavior assumptions that should later be checked against actual B/runtime implementations rather than simply trusted
  - `work/` paths reappear inside some late spec surfaces and should remain visible as cross-surface tension
