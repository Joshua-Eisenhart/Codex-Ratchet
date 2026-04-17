"""Core schema constants for visualization replay artifacts."""

SCHEMA_VERSION = "viz_run_v1"
POINT_FRAME_ENTITY_KIND = "point_frame"
MESH_PATCH_ENTITY_KIND = "mesh_patch"
PUBLIC_STATUS_LABELS = (
    "exists",
    "runs",
    "passes local rerun",
    "canonical by process",
)
ADMISSION_STAGE_LABELS = (
    "shell-local",
    "pairwise",
    "coexistence",
    "topology-variant",
    "emergence",
    "bridge-claims",
)
ADMISSION_STAGE_NEXT = {
    "shell-local": "pairwise",
    "pairwise": "coexistence",
    "coexistence": "topology-variant",
    "topology-variant": "emergence",
    "emergence": "bridge-claims",
    "bridge-claims": "bridge-claims",
}
CLAIM_STATE_LABELS = (
    "candidate",
    "proven",
    "open",
    "snapshot-labeled",
)
PROMOTION_STATUS_LABELS = (
    "supporting",
    "candidate",
    "canonical",
)
TRANSPORT_FAMILY = "transport_bundle"
TRANSPORT_SIM_NAME = "parallel_transport_s2_classical"
TRANSPORT_ENTITY_KIND = POINT_FRAME_ENTITY_KIND
HOPF_FAMILY = "transport_bundle"
HOPF_SIM_NAME = "hopf_bundle_lift"
HOPF_ENTITY_KIND = POINT_FRAME_ENTITY_KIND
ATLAS_FAMILY = "atlas_patch"
ATLAS_SIM_NAME = "synthetic_two_patch_atlas"
ATLAS_ENTITY_KIND = MESH_PATCH_ENTITY_KIND
