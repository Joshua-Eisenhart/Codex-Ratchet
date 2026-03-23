---
id: "A1_CARTRIDGE::REFINEMENT_CONTRACT_AND_CANDIDATE_PROPOSAL"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# REFINEMENT_CONTRACT_AND_CANDIDATE_PROPOSAL_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::REFINEMENT_CONTRACT_AND_CANDIDATE_PROPOSAL`

## Description
Multi-lane adversarial examination envelope for REFINEMENT_CONTRACT_AND_CANDIDATE_PROPOSAL

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: refinement_contract_and_candidate_proposal is structurally necessary because: Refinement contract v1.1: formal rules for refinement admission. CANDIDATE_PROPOSAL v1: template for proposing new struc
- **adversarial_negative**: If refinement_contract_and_candidate_proposal is removed, the following breaks: dependency chain on refinement, candidate, proposal
- **success_condition**: SIM produces stable output when refinement_contract_and_candidate_proposal is present
- **fail_condition**: SIM diverges or produces contradictory output without refinement_contract_and_candidate_proposal
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[REFINEMENT_CONTRACT_AND_CANDIDATE_PROPOSAL]]

## Inward Relations
- [[REFINEMENT_CONTRACT_AND_CANDIDATE_PROPOSAL_COMPILED]] → **COMPILED_FROM**
