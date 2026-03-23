# Community vs Layer Alignment Audit v1

**Total Nodes (Union):** 10524
**Total Edges (Union):** 21934
**Total Communities Found:** 2576

## 1. Manual Layer Alignment

| Layer | Total Nodes | Communities | Dominant Community | Purity % | Internally Diverse? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| HIGH_INTAKE | 8793 | 1750 | 0 | 4.83% | Yes |
| MID_REFINEMENT | 858 | 514 | 2 | 5.94% | Yes |
| LOW_CONTROL | 419 | 267 | 2 | 16.23% | Yes |
| A1_JARGONED | 420 | 48 | 2 | 44.76% | Yes |
| PROMOTED | 296 | 3 | 2 | 85.14% | No |

## 2. Bridge Communities (Spanning Multiple Layers)

Found **3** bridge communities.

| Community ID | Layers Spanned |
| :--- | :--- |
| 2 | PROMOTED, A1_JARGONED, MID_REFINEMENT, LOW_CONTROL |
| 28 | PROMOTED, A1_JARGONED, MID_REFINEMENT |
| 32 | PROMOTED, A1_JARGONED |

## 3. Bridge Nodes (Cross-Layer Anchors)

Found **262** nodes that exist in multiple manual layers.
These nodes are critical junction points in the graph hierarchy.

| Node ID | Layers |
| :--- | :--- |
| A2_2::REFINED::A2_CONTROL_LAW::1b8c6c0982fd8a0d | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::COUPLED_LADDER_RATCHET::5146a4c60d5278bc | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::Chiral Game Theory Operators::89d247f8fe9376cf | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::DUAL_REPLAY_DETERMINISM_REQUIREMENT::e822722a70217ec2 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::ELIMINATION_EPISTEMOLOGY::c318e9d9dda0bf9e | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::FINITUDE_BAN::7fe6a6143217e8bc | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::FOUR_LAYER_TRUST_SEPARATION::14dcea2aaed9c3f4 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::Hash-Embedded Simulation Memory::97f2b38bf41f7193 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::NONCLASSICAL_IMPERATIVE::17b511cb04a0018c | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::Perception as Predictive Projection::114267dec3aaf5de | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::STRUCTURED_NONCLASSICAL_STATE::18eb3da588b1cd4b | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a1_branch_exploration_contract::084e7858fe626fe7 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a1_historical_branch_wiggle_model::bf82bcbada8ae936 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a1_owner_scope_live_vs_legacy::d1d5aa04b14b2238 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a1_queue_status_surface::49e48377c6492e9b | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a1_state_entropy_and_rosetta_docs::e7965dbad033deaf | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a1_wiggle_five_lanes::65d3c7dbd70b3eb8 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a2_append_first_safety::acb9d275e4576ff1 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a2_controller_launch_packet_contract::1d3ef6e71c26a3e2 | PROMOTED, MID_REFINEMENT |
| A2_2::REFINED::a2_refinery_bootpack_execution_contract::71d343be518db9bb | PROMOTED, MID_REFINEMENT |

## Summary Conclusion

Do the algorithmically-discovered communities ALIGN with manual layers?

**Weak Alignment:** Average layer purity is 31.38%. Topology does not strictly respect manual boundaries.
