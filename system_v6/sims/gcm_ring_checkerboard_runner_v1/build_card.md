# BUILD CARD: gcm_ring_checkerboard_runner_v1

Claim under test: the frozen GCM survivor/class/region object can be realized as a ring-checkerboard CA run-surface runner with (a) a nontrivial pinned AABB paired schedule, (b) a strict ring-adjacent cell-pair local update variant, and (c) completed finite-object presentation checks.

Ceiling: `scratch_diagnostic`, `carrier-and-pins-relative`, not THE manifold, not terrain admission, not runtime flux, not QCA/GNVW evidence.

Three coordinates:

- layer: CA run-surface, declared run-surface dimension `layers 1-2 + 12 support`;
- nesting: `integrated-onto-the-carve`;
- qubit depth: `1Q`.

Substrate-first gate:

- consumes `gcm_object_id` `gcmobj_a40e54e13cec01466c9d675028b3574b`;
- consumes registry body hash `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`;
- must pass `scripts/gcm_substrate_check.py` on real lineage;
- must fail the lineage-free negative red.

Packet rows:

- support map: frozen survivors as finite ring cells; frozen quotient class and candidate region IDs pinned per cell; carved adjacency retained as the local block graph;
- presentation map: primary presentation is `nested_rings_torus_loops`; the frozen-object rows check `flat_nested_checkerboard <-> nested_rings_torus_loops`, `nested_rings_torus_loops <-> spherical_checkerboard`, and `flat_nested_checkerboard <-> spherical_checkerboard`;
- local update: carved-adjacency alternating row is retained, and the v0 AABB identity row is refused as a dead rule;
- paired schedule: pinned `AABB` phase pattern with four distinct ring-adjacent subphases; periodicity is recomputed and must move survivor states;
- strict ring-site light-cone: the ring-local variant uses only ring-adjacent cell pairs and must pass max one cyclic ring site per half-step;
- dynamics: alternating-vs-paired trajectories, strict ring-local trajectory, phase/block structure, orbit nontriviality, and per-rule dynamic-admissibility reruns for preservation of `M(C)`;
- controls: all-to-all rule, phase-merge single-phase control, carve-erasure anchoring break, strict-ring-locality obstruction row, and dead-rule honest refusals;
- fence: `QCA/GNVW index row = named not run`; this is classical/1Q rung first and geometric only.

Standards:

- standards codex: `system_v6/receipts/audit_standards_codex_v1.md`;
- G.2a: validator uses `scripts/builder_audit_boundary.py`; no hard absence assertion for a future independent `audit_verdict.md`;
- builder does not write `audit_verdict.md`;
- NO git add/commit.

Allowed writes:

- `system_v6/sims/gcm_ring_checkerboard_runner_v1/build_card.md`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/builder_self_assessment.md`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/gcm_ring_checkerboard_runner_v1.py`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/gcm_ring_checkerboard_runner_v1_common.py`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/gcm_ring_checkerboard_runner_v1_envelope.py`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/validate_gcm_ring_checkerboard_runner_v1.py`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/tests/test_gcm_ring_checkerboard_runner_v1.py`
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/results/*.json`
