"""Capability names used by the visualization replay contract."""

BASE_POINT = "base_point"
FRAME = "frame"
TRANSPORT_PATH = "transport_path"
HOLONOMY = "holonomy"
S3_STATE = "s3_state"
FIBER_PHASE = "fiber_phase"
FIBER_SAMPLES = "fiber_samples"

TRANSPORT_CAPABILITIES = [BASE_POINT, FRAME, TRANSPORT_PATH, HOLONOMY]
HOPF_CAPABILITIES = [BASE_POINT, FRAME, TRANSPORT_PATH, S3_STATE, FIBER_PHASE, FIBER_SAMPLES]
