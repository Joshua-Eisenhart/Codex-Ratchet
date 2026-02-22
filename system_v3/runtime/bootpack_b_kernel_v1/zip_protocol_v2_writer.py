import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path


_FIXED_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: object) -> bytes:
    # Canonical JSON: sorted keys, stable separators, UTF-8, trailing LF.
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _canonical_text_bytes(text: str) -> bytes:
    # Canonical text: LF newlines, no CR, trailing LF.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Enforce "no trailing spaces per line" canonical form to match validator.
    normalized = "\n".join(line.rstrip(" ") for line in normalized.split("\n"))
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized.encode("utf-8")


def _zip_write_bytes(zf: zipfile.ZipFile, rel_path: str, data: bytes) -> None:
    zi = zipfile.ZipInfo(rel_path)
    zi.date_time = _FIXED_ZIP_DATETIME
    zi.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


@dataclass(frozen=True)
class ZipWriteResult:
    path: str
    manifest_sha256: str


def write_zip_protocol_v2(
    *,
    out_path: str | Path,
    header: dict,
    payload_json: dict[str, object] | None = None,
    payload_text: dict[str, str] | None = None,
) -> ZipWriteResult:
    """
    Produce a ZIP_PROTOCOL_v2 capsule.

    Callers must provide:
    - header fields except manifest_sha256 (computed here)
    - payload files as either canonical JSON (payload_json) or canonical text (payload_text)
    """
    out_path = Path(out_path)
    payload_json = dict(payload_json or {})
    payload_text = dict(payload_text or {})

    if set(payload_json).intersection(payload_text):
        raise ValueError("payload filename cannot be both json and text")

    payload_files: dict[str, bytes] = {}
    for name, obj in payload_json.items():
        payload_files[name] = _canonical_json_bytes(obj)
    for name, text in payload_text.items():
        payload_files[name] = _canonical_text_bytes(text)

    # MANIFEST.json lists payload files only (core files excluded).
    manifest_entries = []
    for rel_path in sorted(payload_files):
        data = payload_files[rel_path]
        manifest_entries.append(
            {
                "rel_path": rel_path,
                "byte_size": len(data),
                "sha256": _sha256_bytes(data),
            }
        )
    manifest_bytes = _canonical_json_bytes(manifest_entries)
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    header = dict(header)
    header["zip_protocol"] = "ZIP_PROTOCOL_v2"
    header["manifest_sha256"] = manifest_sha256
    header_bytes = _canonical_json_bytes(header)

    # HASHES.sha256 covers ZIP_HEADER.json + MANIFEST.json + all payload files; excludes itself.
    hashes: dict[str, str] = {
        "ZIP_HEADER.json": _sha256_bytes(header_bytes),
        "MANIFEST.json": manifest_sha256,
    }
    for rel_path in sorted(payload_files):
        hashes[rel_path] = _sha256_bytes(payload_files[rel_path])

    hash_lines = []
    for rel_path in sorted(hashes):
        hash_lines.append(f"{hashes[rel_path]}  {rel_path}")
    hashes_bytes = _canonical_text_bytes("\n".join(hash_lines))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # Producer ordering is lexicographic by rel_path; validators ignore ZIP metadata.
        for rel_path, data in [
            ("HASHES.sha256", hashes_bytes),
            ("MANIFEST.json", manifest_bytes),
            ("ZIP_HEADER.json", header_bytes),
        ]:
            _zip_write_bytes(zf, rel_path, data)
        for rel_path in sorted(payload_files):
            _zip_write_bytes(zf, rel_path, payload_files[rel_path])

    return ZipWriteResult(path=str(out_path), manifest_sha256=manifest_sha256)
