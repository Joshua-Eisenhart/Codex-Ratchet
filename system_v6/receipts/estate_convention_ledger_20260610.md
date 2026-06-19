# Estate Convention Ledger 2026-06-10

Generated: 2026-06-10T19:52:25Z

Outcome: PASS

Scope: committed/current result files for S1/S2/S3/S4/S5/S7, MCT dynamic, Bloch root, and MCT nonassoc weld. This ledger is a convention guard only; it promotes no claim.

| Check | Status | Evidence |
| --- | --- | --- |
| `bloch_basis_mapped` | PASS | `{"s1_s3_basis": "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)", "s4_s5_expected": "source_locked_standard_bloch plus J conversion into pinned basis"}` |
| `holonomy_sense_mapped` | PASS | `{"distinction": "accumulated phi is separated from endpoint/Berry phase", "stokes": "h(eta_j)-h(eta_i)+Phi_ij=0", "target": "h(eta)=-2*pi*cos(2*eta)"}` |
| `entropy_base_mapped` | PASS | `{"auxiliary": "bits/log2 only if labelled", "primary": "nats/natural log"}` |
| `rotation_handedness_mapped` | PASS | `{"s4": "R_x/R_z source-locked standard basis", "s5": "H_L=+H0 and H_R=-H0"}` |
| `octonion_orientation_reconciled_without_reuse` | PASS | `{"bloch_old_to_new": [0, 3, 2, 1, 6, 7, 4, 5], "receipt": "system_v6/receipts/octonion_orientation_reconciliation_20260610.md", "status": "distinct maps documented; no cross-packet reuse claim promoted", "weld_basis_lift": {"perm": [0, 1, 2, 3, 4, 7, 6, 5], "signs": [1, 1, 1, 1, 1, -1, 1, -1]}}` |
| `canon_receipt_path_live` | PASS | `{"path": "system_v6/receipts/canon_algebra_artifact_v1_results_20260610.json"}` |
| `source_hashes_current` | PASS | `{"bloch_root": {"pass": true, "path": "system_v6/sims/bloch_root_admissibility_discriminator_v0/bloch_root_admissibility_discriminator_v0_envelope.py", "sha256": "bd856098f2b56cb22ea74a90166d3bff7887f8348351641bee0729affef27dc5"}, "geo_s1_exact": {"pass": true, "path": "system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_envelope.py", "sha256": "0bf8ac8f5fe280c946ec4032213dba62f683ef3b596d7f7fc70c310335af16c4"}, "geo_s2": {"pass": true, "path": "system_v6/sims/geo_s2_connection_flux_foliation_v0/geo_s2_connection_flux_foliation_v0_envelope.py", "sha256": "f45ea56fe98c1781f45d0f46579b24a1269785ee0dcb8ab363bc5cdf81063d51"}, "geo_s3": {"pass": true, "path": "system_v6/sims/geo_s3_density_observable_v0/geo_s3_density_observable_v0_envelope.py", "sha256": "1e4b9eecad729cf19cfe7efc30cf7a8abe78cf643688b7e06e9dd9adc9a5dde1"}, "geo_s4": {"pass": true, "path": "system_v6/sims/geo_s4_operator_stage_v0/geo_s4_operator_stage_v0_envelope.py", "sha256": "8ede98ed4520dfde382ee82fb648dd9c94d53edcd791981790722ce9042d4230"}, "geo_s5": {"pass": true, "path": "system_v6/sims/geo_s5_terrain_flows_v0/geo_s5_terrain_flows_v0_envelope.py", "sha256": "f627b5026c7d7fec747bff4600fc43026f5f9683c94db3ac452a463afd12c5e6"}, "geo_s7": {"pass": true, "path": "system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_envelope.py", "sha256": "374141367362e6e685f8d7f4b50e84d90affa309563fb9ca81b24f10a4314cc5"}, "mct_dynamic": {"pass": true, "path": "system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_envelope.py", "sha256": "c8f4a55bbd5753cb9696d55fb7b570e6d0bcf52640f37206f15ad055ad19c61c"}, "mct_weld": {"pass": true, "path": "system_v6/sims/mct_nonassoc_weld_packet_v0/mct_nonassoc_weld_packet_v0_envelope.py", "sha256": "e38cc6ea055f7ee7b3f3f584f55e722e77ee3c0e8ec144b0a0e62f9e2af81fbe"}}` |
