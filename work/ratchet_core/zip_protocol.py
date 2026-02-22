"""ZIP protocol: the universal container for everything crossing a thread boundary.

A ZIP is a JSON file on disk. It has a fixed schema. It's hashed.
It's the only way threads communicate. No chat, no prose, no side channels.

ZIP kinds:
  A2_FUEL       — A2 → A1: compressed fuel entries from doc processing
  A1_STRATEGY   — A1 LLM → A1 expander: strategy (nondeterministic output)
  A1_BATCH      — A1 expander → A0: expanded proposals (deterministic output)
  EXPORT_BLOCK  — A0 → B: compiled block (already exists in containers.py)
  SIM_REQUEST   — A0 → SIM: sim to execute
  SIM_EVIDENCE  — SIM → B: evidence back
  FEEDBACK      — A1 → A2: what B accepted/rejected, rosetta updates

Every ZIP is saved to disk the moment it's created. The trail of ZIPs
IS the save system. No separate save operation needed.
"""

import hashlib
import json
import time
from pathlib import Path


ZIP_DIR = Path(__file__).resolve().parent.parent / "runs" / "zips"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_zip(kind: str, source: str, target: str, payload: dict,
               out_dir: Path = None) -> Path:
    """Create a ZIP file on disk. Returns the path."""
    out = out_dir or ZIP_DIR
    out.mkdir(parents=True, exist_ok=True)

    envelope = {
        "kind": kind,
        "source": source,
        "target": target,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": payload,
    }
    raw = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("ascii")
    envelope["manifest_sha256"] = _hash(raw)

    final = json.dumps(envelope, sort_keys=True, indent=2).encode("ascii")
    filename = f"{kind}_{envelope['manifest_sha256'][:12]}.json"
    path = out / filename
    path.write_bytes(final)
    return path


def read_zip(path: Path) -> dict:
    """Read and verify a ZIP file."""
    data = json.loads(path.read_text("ascii"))
    stored_hash = data.pop("manifest_sha256", "")
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("ascii")
    if stored_hash and _hash(raw) != stored_hash:
        raise ValueError(f"ZIP manifest mismatch: {path}")
    data["manifest_sha256"] = stored_hash
    return data


def list_zips(kind: str = None, zip_dir: Path = None) -> list:
    """List all ZIPs, optionally filtered by kind."""
    d = zip_dir or ZIP_DIR
    if not d.exists():
        return []
    zips = sorted(d.glob("*.json"))
    if kind:
        zips = [z for z in zips if z.name.startswith(kind)]
    return zips
