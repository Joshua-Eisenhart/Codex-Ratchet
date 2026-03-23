# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_stage3_pro_send_packaging__v1`
Extraction mode: `OUTBOUND_HANDOFF_PACKAGING_PASS`

## T1) tiny coordination lane vs large formal handoff stack
- source markers:
  - `work/INBOX/README.md`: `3-10`
  - `work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__MANIFEST__STAGE3_PRO_RUN__v1_1.json`: `2-155`
- tension:
  - one source insists cross-operator exchange should stay tiny and explicit
  - the adjacent handoff family is a large ten-job serialized packaging program
- preserved read:
  - spillover process uses both a minimal sidechannel and a heavy transport spine

## T2) single attachment per fresh thread vs one logical Stage-3 run with ten jobs
- source markers:
  - manifest: `3-5`
  - send order: `3-5`, `7-55`
- tension:
  - the run is presented as one Stage-3 set
  - execution still requires ten fresh-thread serial attachments rather than one direct multi-job submission
- preserved read:
  - logical bundling and transport execution granularity are intentionally different

## T3) output-only return discipline vs loss of full job-root context
- source markers:
  - send order: `4-5`
  - manifest: `12-152`
- tension:
  - the manifest preserves rich payload membership and job structure
  - the expected return zip keeps only `output/`, dropping the original job-root context from the response contract
- preserved read:
  - result transport is optimized for lean returns, not for round-tripping the full execution package

## T4) manifest/send-order filename spellings vs checksum and actual zip filenames
- source markers:
  - manifest: `10`, `27`, `41`, `55`, `68`, `82`, `97`, `113`, `128`, `143`
  - send order: `8`, `13`, `18`, `23`, `28`, `33`, `38`, `43`, `48`, `53`
  - checksum ledger: `1-10`
- tension:
  - the manifest and send-order plaques name each zip with triple underscores before `v1_1`
  - the checksum ledger and actual child zip files use double underscores before `v1_1`
- preserved read:
  - integrity closure exists, but one control-layer spelling drift remains unresolved

## T5) process-rigid handoff language vs non-law spillover status
- source markers:
  - send order: `1-5`
  - inbox plaque: `3-10`
- tension:
  - the language is operationally strict and sounds protocol-like
  - every source still lives in `work/`, which this lane treats as legacy/test/prototype spillover
- preserved read:
  - do not confuse process usefulness with active authority

## T6) duplicated inventory across JSON and markdown vs divergence risk
- source markers:
  - manifest: `5-154`
  - send order: `7-55`
- tension:
  - the batch list is duplicated in a machine-readable manifest and a human-readable send-order sheet
  - that duplication improves usability but creates a second surface where filename drift can appear
- preserved read:
  - redundancy helps operators, but it also creates a real sync burden
