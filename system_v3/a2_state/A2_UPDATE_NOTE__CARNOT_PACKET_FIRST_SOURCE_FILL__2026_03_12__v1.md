# A2_UPDATE_NOTE__CARNOT_PACKET_FIRST_SOURCE_FILL__2026_03_12__v1

Status: PROPOSED / NONCANONICAL / A2 UPDATE NOTE
Date: 2026-03-12
Role: bounded A2 controller note for the first real source-bearing fill of `carnot_primary`

## AUDIT_SCOPE
- corrected external boot workspace:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v3`
- target packet:
  - `sources/external/carnot_primary/`
- supporting control surfaces:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/EXTERNAL_BOOT_READINESS_AUDIT__ENTROPY_CARNOT_SZILARD__2026_03_12__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/NEXT_PRO_BOOT_PACKET_SCAFFOLD__ENTROPY_CARNOT_SZILARD__2026_03_11__v1.md`

## FINDINGS
- repo-local residue alone was not enough to satisfy `CARNOT_PRIMARY_PACKET`
- a first real source-bearing Carnot file is now added using stable public-domain source locators:
  - Carnot `Chapter 3` on Wikisource
  - 1911 Britannica `Heat` Carnot section on Wikisource
- the packet is no longer empty-stub only
- the packet is still incomplete because:
  - fuller state/efficiency extraction is still missing
  - Maxwell-demon and FEP first-priority packets remain stub-only

## A2_UPDATE_NOTE
- preserve this boundary:
  - first source-bearing floor crossed for `carnot_primary`
  - overall external lane still held
- preserve this exact next move:
  - add another direct Carnot source-bearing file or equivalent deeper extract before treating Carnot as adequately filled
- preserve this higher-level controller consequence:
  - the readiness blocker has narrowed from:
    - empty first packet
  - to:
    - partially filled first packet plus remaining first-priority gaps

## OFF_PROCESS_FLAGS
- off-process if a later note:
  - treats one Carnot extract as full first-wave completion
  - reclassifies Maxwell or FEP as started when they remain stub-only
  - widens this packet-fill step into `A1` readiness

## SAFE_TO_CONTINUE
- yes, for one more bounded fill pass on `carnot_primary`
- yes, for later Maxwell-demon packet fill after Carnot is stronger
- no, for external launch yet
- no, for fresh `A1`
