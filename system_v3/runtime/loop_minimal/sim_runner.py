import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import hashlib
from typing import List


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def emit_sim_evidence(sim_id: str, token: str, input_hash_sha256: str) -> str:
    code_hash = _sha256_bytes(b"sim_stub_code")
    output_hash = _sha256_bytes(b"sim_stub_output")
    run_manifest = _sha256_bytes(f"loop_minimal|{sim_id}|{token}|{input_hash_sha256}|{code_hash}".encode("utf-8"))
    lines = [
        "BEGIN SIM_EVIDENCE v1",
        f"SIM_ID: {sim_id}",
        f"CODE_HASH_SHA256: {code_hash}",
        f"INPUT_HASH_SHA256: {input_hash_sha256}",
        f"OUTPUT_HASH_SHA256: {output_hash}",
        f"RUN_MANIFEST_SHA256: {run_manifest}",
        f"EVIDENCE_SIGNAL {sim_id} CORR {token}",
        "END SIM_EVIDENCE v1",
        "",
    ]
    return "\n".join(lines)


def run_pending(state) -> List[str]:
    evidences = []
    input_hash = state.hash() if hasattr(state, "hash") else _sha256_bytes(b"")
    for spec_id, tokens in sorted(state.evidence_pending.items()):
        for token in sorted(tokens):
            evidences.append(emit_sim_evidence(spec_id, token, input_hash_sha256=input_hash))
    return evidences
