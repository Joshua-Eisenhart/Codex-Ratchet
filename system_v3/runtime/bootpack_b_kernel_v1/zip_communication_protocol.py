import hashlib
import json
from pathlib import Path


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_zip_packet(
    root: Path,
    run_id: str,
    sequence: int,
    kind: str,
    source: str,
    target: str,
    payload: dict,
) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    envelope = {
        "zip_protocol": "ZIP_PACKET_v1",
        "run_id": run_id,
        "sequence": int(sequence),
        "kind": kind,
        "source": source,
        "target": target,
        "payload": payload,
    }
    manifest_hash = _sha256_bytes(_canonical_bytes(envelope))
    envelope["manifest_sha256"] = manifest_hash
    final_text = json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n"
    filename = f"{sequence:06d}_{kind}.json"
    path = root / filename
    path.write_text(final_text, encoding="utf-8")
    return {"path": str(path), "manifest_sha256": manifest_hash}


def read_zip_packet(path: Path) -> dict:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    stored_hash = str(envelope.get("manifest_sha256", ""))
    check = dict(envelope)
    check.pop("manifest_sha256", None)
    computed = _sha256_bytes(_canonical_bytes(check))
    if stored_hash != computed:
        raise ValueError(f"zip_manifest_mismatch:{path}")
    return envelope

