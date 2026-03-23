---
id: "A1_CARTRIDGE::ZIP_TEST_FIXTURES"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_TEST_FIXTURES_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_TEST_FIXTURES`

## Description
Multi-lane adversarial examination envelope for ZIP_TEST_FIXTURES

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_test_fixtures is structurally necessary because: [AUDITED] ZIP test fixtures (7 files): test_bundle.zip, tampered_bundle.zip, ZIP_HEADER.json, MANIFEST.json, HASHES.sha2
- **adversarial_negative**: If zip_test_fixtures is removed, the following breaks: none identified
- **success_condition**: SIM produces stable output when zip_test_fixtures is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_test_fixtures
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_TEST_FIXTURES]]

## Inward Relations
- [[ZIP_TEST_FIXTURES_COMPILED]] → **COMPILED_FROM**
