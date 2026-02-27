from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import PurePosixPath

from containers import parse_export_block, parse_sim_evidence_pack


_RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPORT_BEGIN_RE = re.compile(r"^BEGIN EXPORT_BLOCK v\d+$")
_EXPORT_END_RE = re.compile(r"^END EXPORT_BLOCK v\d+$")

_SIM_BEGIN = "BEGIN SIM_EVIDENCE v1"
_SIM_END = "END SIM_EVIDENCE v1"
_SNAP_BEGIN = "BEGIN THREAD_S_SAVE_SNAPSHOT v2"
_SNAP_END = "END THREAD_S_SAVE_SNAPSHOT v2"

_HEADER_REQUIRED = [
    "zip_protocol",
    "zip_type",
    "direction",
    "source_layer",
    "target_layer",
    "run_id",
    "sequence",
    "created_utc",
    "compiler_version",
    "manifest_sha256",
]


_ZIP_TYPES: dict[str, dict] = {
    "A2_TO_A1_PROPOSAL_ZIP": {
        "direction": "FORWARD",
        "source_layer": "A2",
        "target_layer": "A1",
        "payload_files": ["A2_PROPOSAL.json"],
        "containers": {},
    },
    "A1_TO_A0_STRATEGY_ZIP": {
        "direction": "FORWARD",
        "source_layer": "A1",
        "target_layer": "A0",
        "payload_files": ["A1_STRATEGY_v1.json"],
        "containers": {},
    },
    "A0_TO_B_EXPORT_BATCH_ZIP": {
        "direction": "FORWARD",
        "source_layer": "A0",
        "target_layer": "B",
        "payload_files": ["EXPORT_BLOCK.txt"],
        "containers": {"EXPORT_BLOCK.txt": ("EXPORT_BLOCK", "exactly_one")},
    },
    "B_TO_A0_STATE_UPDATE_ZIP": {
        "direction": "BACKWARD",
        "source_layer": "B",
        "target_layer": "A0",
        "payload_files": ["THREAD_S_SAVE_SNAPSHOT_v2.txt"],
        "containers": {"THREAD_S_SAVE_SNAPSHOT_v2.txt": ("THREAD_S_SAVE_SNAPSHOT_v2", "exactly_one")},
    },
    "SIM_TO_A0_SIM_RESULT_ZIP": {
        "direction": "BACKWARD",
        "source_layer": "SIM",
        "target_layer": "A0",
        "payload_files": ["SIM_EVIDENCE.txt"],
        "containers": {"SIM_EVIDENCE.txt": ("SIM_EVIDENCE_v1", "one_or_more")},
    },
    "A0_TO_A1_SAVE_ZIP": {
        "direction": "BACKWARD",
        "source_layer": "A0",
        "target_layer": "A1",
        "payload_files": ["A0_SAVE_SUMMARY.json"],
        "containers": {},
    },
    "A1_TO_A2_SAVE_ZIP": {
        "direction": "BACKWARD",
        "source_layer": "A1",
        "target_layer": "A2",
        "payload_files": ["A1_SAVE_SUMMARY.json"],
        "containers": {},
    },
    "A2_META_SAVE_ZIP": {
        "direction": "BACKWARD",
        "source_layer": "A2",
        "target_layer": "A2",
        "payload_files": ["A2_META_SAVE_SUMMARY.json"],
        "containers": {},
    },
}


_CORE_FILES = {"ZIP_HEADER.json", "MANIFEST.json", "HASHES.sha256"}

_FORBIDDEN_BY_TYPE: dict[str, set[str]] = {
    # save zips forbid all mutation containers
    "A0_TO_A1_SAVE_ZIP": {"EXPORT_BLOCK", "SIM_EVIDENCE_v1", "THREAD_S_SAVE_SNAPSHOT_v2"},
    "A1_TO_A2_SAVE_ZIP": {"EXPORT_BLOCK", "SIM_EVIDENCE_v1", "THREAD_S_SAVE_SNAPSHOT_v2"},
    "A2_META_SAVE_ZIP": {"EXPORT_BLOCK", "SIM_EVIDENCE_v1", "THREAD_S_SAVE_SNAPSHOT_v2"},
    # proposal/strategy zips forbid all runtime containers
    "A2_TO_A1_PROPOSAL_ZIP": {"EXPORT_BLOCK", "SIM_EVIDENCE_v1", "THREAD_S_SAVE_SNAPSHOT_v2"},
    "A1_TO_A0_STRATEGY_ZIP": {"EXPORT_BLOCK", "SIM_EVIDENCE_v1", "THREAD_S_SAVE_SNAPSHOT_v2"},
    # export zip only allows export container
    "A0_TO_B_EXPORT_BATCH_ZIP": {"SIM_EVIDENCE_v1", "THREAD_S_SAVE_SNAPSHOT_v2"},
    # snapshot zip only allows snapshot container
    "B_TO_A0_STATE_UPDATE_ZIP": {"EXPORT_BLOCK", "SIM_EVIDENCE_v1"},
    # sim zip only allows sim evidence container
    "SIM_TO_A0_SIM_RESULT_ZIP": {"EXPORT_BLOCK", "THREAD_S_SAVE_SNAPSHOT_v2"},
}


_FORWARD_REPLAY_SOURCES = ("A1", "A0")
_PARKED_KEY_PREFIX = "__PARKED__:"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _reject(tag: str, reason: str) -> dict:
    return {"outcome": "REJECT", "tag": tag, "reason": reason}


def _park(reason: str) -> dict:
    return {"outcome": "PARK", "reason": reason}


def _ok(sequence: int) -> dict:
    return {"outcome": "OK", "sequence": int(sequence)}


def _decode_utf8(data: bytes) -> str:
    return data.decode("utf-8")


def _validate_text_canonical(data: bytes) -> bool:
    if b"\r" in data:
        return False
    if not data.endswith(b"\n"):
        return False
    for line in _decode_utf8(data).splitlines():
        if line != line.rstrip(" "):
            return False
    return True


def _container_begins(text: str) -> set[str]:
    found: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if _EXPORT_BEGIN_RE.fullmatch(line):
            found.add("EXPORT_BLOCK")
        if line == _SIM_BEGIN:
            found.add("SIM_EVIDENCE_v1")
        if line == _SNAP_BEGIN:
            found.add("THREAD_S_SAVE_SNAPSHOT_v2")
    return found


def _validate_manifest_path(rel_path: str) -> bool:
    if "\\" in rel_path:
        return False
    if rel_path.startswith("/") or rel_path.startswith("./"):
        return False
    p = PurePosixPath(rel_path)
    if any(part == ".." for part in p.parts):
        return False
    if str(p) != rel_path:
        return False
    return True


def _parse_hashes_file(data: bytes) -> tuple[dict[str, str], str | None]:
    if not _validate_text_canonical(data):
        return {}, "HASHES_MISMATCH"
    lines = _decode_utf8(data).splitlines()
    entries: dict[str, str] = {}
    sorted_paths: list[str] = []
    for line in lines:
        parts = line.split("  ")
        if len(parts) != 2:
            return {}, "HASHES_MISMATCH"
        hash_value, rel_path = parts
        if not _HEX64_RE.fullmatch(hash_value):
            return {}, "INVALID_HASH_FORMAT"
        if rel_path in entries:
            return {}, "HASHES_MISMATCH"
        entries[rel_path] = hash_value
        sorted_paths.append(rel_path)
    if sorted_paths != sorted(sorted_paths):
        return {}, "HASHES_MISMATCH"
    return entries, None


def _count_export_blocks(text: str) -> tuple[int, int]:
    begins = 0
    ends = 0
    for raw in text.splitlines():
        line = raw.strip()
        if _EXPORT_BEGIN_RE.fullmatch(line):
            begins += 1
        if _EXPORT_END_RE.fullmatch(line):
            ends += 1
    return begins, ends


def _count_exact(text: str, begin: str, end: str) -> tuple[int, int]:
    begins = 0
    ends = 0
    for raw in text.splitlines():
        line = raw.strip()
        if line == begin:
            begins += 1
        if line == end:
            ends += 1
    return begins, ends


def _parked_state_key(run_id: str, source_layer: str) -> tuple[str, str]:
    return (run_id, f"{_PARKED_KEY_PREFIX}{source_layer}")


def _read_parked_sequences(
    seq_state: dict[tuple[str, str], object],
    run_id: str,
    source_layer: str,
) -> set[int]:
    raw = seq_state.get(_parked_state_key(run_id, source_layer), [])
    if isinstance(raw, int):
        return {int(raw)}
    if isinstance(raw, (list, tuple, set)):
        out: set[int] = set()
        for value in raw:
            try:
                out.add(int(value))
            except Exception:
                continue
        return out
    return set()


def _mark_deterministic_park(
    seq_state: dict[tuple[str, str], object],
    run_id: str,
    source_layer: str,
    sequence: int,
) -> None:
    parked = _read_parked_sequences(seq_state, run_id, source_layer)
    parked.add(int(sequence))
    seq_state[_parked_state_key(run_id, source_layer)] = sorted(parked)


def _sequence_exists_or_parked(
    seq_state: dict[tuple[str, str], object],
    run_id: str,
    source_layer: str,
    sequence: int,
) -> bool:
    accepted = int(seq_state.get((run_id, source_layer), 0))
    if int(sequence) <= accepted:
        return True
    parked = _read_parked_sequences(seq_state, run_id, source_layer)
    return int(sequence) in parked


def _forward_horizon(
    seq_state: dict[tuple[str, str], object],
    run_id: str,
    source_layer: str,
) -> int:
    accepted = int(seq_state.get((run_id, source_layer), 0))
    parked = _read_parked_sequences(seq_state, run_id, source_layer)
    parked_max = max(parked) if parked else 0
    return max(accepted, parked_max)


def _missing_forward_sequence(
    seq_state: dict[tuple[str, str], object],
    run_id: str,
    source_layer: str,
    required_upto: int,
) -> int | None:
    for required_seq in range(1, int(required_upto) + 1):
        if _sequence_exists_or_parked(seq_state, run_id, source_layer, required_seq):
            continue
        return required_seq
    return None


def validate_zip_protocol_v2(
    zip_path: str,
    last_accepted_sequence: dict[tuple[str, str], int] | None = None,
) -> dict:
    seq_state: dict[tuple[str, str], object] = last_accepted_sequence if last_accepted_sequence is not None else {}

    try:
        zf = zipfile.ZipFile(zip_path, "r")
    except Exception:
        return _reject("FORBIDDEN_FILE_PRESENT", "zip_unreadable")

    with zf:
        names = [name for name in zf.namelist() if not name.endswith("/")]
        if len(set(names)) != len(names):
            return _reject("FORBIDDEN_FILE_PRESENT", "duplicate_archive_entries")
        if "ZIP_HEADER.json" not in names or "MANIFEST.json" not in names or "HASHES.sha256" not in names:
            return _reject("MISSING_HEADER_FIELD", "missing_core_files")

        file_bytes: dict[str, bytes] = {}
        for name in names:
            file_bytes[name] = zf.read(name)

    # Canonical text enforcement for all text files.
    for name, data in file_bytes.items():
        if name.endswith(".json"):
            try:
                obj = json.loads(_decode_utf8(data))
            except Exception:
                if name == "ZIP_HEADER.json":
                    return _reject("MISSING_HEADER_FIELD", "header_json_invalid")
                if name == "MANIFEST.json":
                    return _reject("MANIFEST_HASH_MISMATCH", "manifest_json_invalid")
                return _reject("HASHES_MISMATCH", f"json_invalid:{name}")
            if data != _canonical_json_bytes(obj):
                if name == "ZIP_HEADER.json":
                    return _reject("MISSING_HEADER_FIELD", "header_not_canonical_json")
                if name == "MANIFEST.json":
                    return _reject("MANIFEST_HASH_MISMATCH", "manifest_not_canonical_json")
                return _reject("HASHES_MISMATCH", f"json_not_canonical:{name}")
        else:
            if not _validate_text_canonical(data):
                return _reject("HASHES_MISMATCH", f"text_not_canonical:{name}")

    # Header parse + required fields.
    try:
        header = json.loads(_decode_utf8(file_bytes["ZIP_HEADER.json"]))
    except Exception:
        return _reject("MISSING_HEADER_FIELD", "header_unreadable")
    for field in _HEADER_REQUIRED:
        if field not in header:
            return _reject("MISSING_HEADER_FIELD", f"missing:{field}")

    if header.get("zip_protocol") != "ZIP_PROTOCOL_v2":
        return _reject("MISSING_HEADER_FIELD", "invalid:zip_protocol")

    zip_type = str(header.get("zip_type", ""))
    direction = str(header.get("direction", ""))
    source_layer = str(header.get("source_layer", ""))
    target_layer = str(header.get("target_layer", ""))
    run_id = str(header.get("run_id", ""))
    created_utc = str(header.get("created_utc", ""))
    compiler_version = str(header.get("compiler_version", ""))
    manifest_sha256 = str(header.get("manifest_sha256", ""))

    if not _RUN_ID_RE.fullmatch(run_id):
        return _reject("MISSING_HEADER_FIELD", "invalid:run_id")
    if not _RFC3339_UTC_RE.fullmatch(created_utc):
        return _reject("MISSING_HEADER_FIELD", "invalid:created_utc")
    if zip_type not in _ZIP_TYPES:
        return _reject("ZIP_TYPE_DIRECTION_MISMATCH", "unknown_zip_type")
    if direction not in {"FORWARD", "BACKWARD"}:
        return _reject("ZIP_TYPE_DIRECTION_MISMATCH", "invalid_direction")
    if source_layer not in {"A2", "A1", "A0", "B", "SIM"}:
        return _reject("ZIP_TYPE_DIRECTION_MISMATCH", "invalid_source_layer")
    if target_layer not in {"A2", "A1", "A0", "B", "SIM"}:
        return _reject("ZIP_TYPE_DIRECTION_MISMATCH", "invalid_target_layer")
    if not _HEX64_RE.fullmatch(manifest_sha256):
        return _reject("INVALID_HASH_FORMAT", "invalid_manifest_sha256")

    # compiler_version policy
    if source_layer == "A0":
        if not compiler_version:
            return _reject("MISSING_HEADER_FIELD", "invalid:compiler_version")
    else:
        if compiler_version != "":
            return _reject("MISSING_HEADER_FIELD", "invalid:compiler_version")

    mapping = _ZIP_TYPES[zip_type]
    if direction != mapping["direction"] or source_layer != mapping["source_layer"] or target_layer != mapping["target_layer"]:
        return _reject("ZIP_TYPE_DIRECTION_MISMATCH", "zip_type_mapping_mismatch")

    try:
        sequence = int(header.get("sequence"))
    except Exception:
        return _reject("MISSING_HEADER_FIELD", "invalid:sequence")
    if sequence < 1:
        return _reject("MISSING_HEADER_FIELD", "invalid:sequence")
    last_seq = int(seq_state.get((run_id, source_layer), 0))
    if sequence <= last_seq:
        return _reject("SEQUENCE_REGRESSION", "sequence_regression")
    if sequence > last_seq + 1:
        if direction == "FORWARD":
            _mark_deterministic_park(seq_state, run_id, source_layer, sequence)
        return _park("SEQUENCE_GAP")

    # Manifest parse.
    manifest_bytes = file_bytes["MANIFEST.json"]
    if _sha256_bytes(manifest_bytes) != manifest_sha256:
        return _reject("MANIFEST_HASH_MISMATCH", "manifest_hash_mismatch")
    try:
        manifest = json.loads(_decode_utf8(manifest_bytes))
    except Exception:
        return _reject("MANIFEST_HASH_MISMATCH", "manifest_unreadable")
    if not isinstance(manifest, list):
        return _reject("MANIFEST_HASH_MISMATCH", "manifest_not_list")

    manifest_paths: list[str] = []
    manifest_set: set[str] = set()
    for row in manifest:
        if not isinstance(row, dict):
            return _reject("MANIFEST_HASH_MISMATCH", "manifest_entry_not_object")
        rel_path = row.get("rel_path")
        byte_size = row.get("byte_size")
        row_sha = row.get("sha256")
        if not isinstance(rel_path, str) or not isinstance(byte_size, int) or not isinstance(row_sha, str):
            return _reject("MANIFEST_HASH_MISMATCH", "manifest_entry_schema")
        if not _validate_manifest_path(rel_path):
            return _reject("MANIFEST_PATH_INVALID", rel_path)
        if rel_path in manifest_set:
            return _reject("DUPLICATE_MANIFEST_PATH", rel_path)
        if not _HEX64_RE.fullmatch(row_sha):
            return _reject("INVALID_HASH_FORMAT", f"manifest_sha:{rel_path}")
        if rel_path not in file_bytes:
            return _reject("FORBIDDEN_FILE_PRESENT", f"manifest_missing_file:{rel_path}")
        if rel_path in _CORE_FILES:
            return _reject("FORBIDDEN_FILE_PRESENT", f"core_file_in_manifest:{rel_path}")
        actual_data = file_bytes[rel_path]
        if byte_size != len(actual_data):
            return _reject("HASHES_MISMATCH", f"byte_size:{rel_path}")
        if row_sha != _sha256_bytes(actual_data):
            return _reject("HASHES_MISMATCH", f"manifest_entry_hash:{rel_path}")
        manifest_paths.append(rel_path)
        manifest_set.add(rel_path)

    if manifest_paths != sorted(manifest_paths):
        return _reject("MANIFEST_PATH_INVALID", "manifest_not_sorted")

    expected_payload = set(mapping["payload_files"])
    if manifest_set != expected_payload:
        return _reject("FORBIDDEN_FILE_PRESENT", "manifest_payload_mismatch")

    expected_all_files = _CORE_FILES | expected_payload
    actual_all_files = set(file_bytes.keys())
    if actual_all_files != expected_all_files:
        return _reject("FORBIDDEN_FILE_PRESENT", "zip_file_allowlist_mismatch")

    # HASHES.sha256
    hashes_map, hashes_err = _parse_hashes_file(file_bytes["HASHES.sha256"])
    if hashes_err:
        return _reject(hashes_err, "hashes_parse")
    required_hash_files = {"ZIP_HEADER.json", "MANIFEST.json"} | expected_payload
    if set(hashes_map.keys()) != required_hash_files:
        return _reject("HASHES_MISMATCH", "hashes_coverage_mismatch")
    for rel_path in sorted(required_hash_files):
        if hashes_map[rel_path] != _sha256_bytes(file_bytes[rel_path]):
            return _reject("HASHES_MISMATCH", f"hash_mismatch:{rel_path}")

    # Forbidden-container detection (exact full-line delimiter matching only).
    forbidden_types = _FORBIDDEN_BY_TYPE[zip_type]
    for rel_path, data in file_bytes.items():
        if rel_path.endswith(".json"):
            continue
        text = _decode_utf8(data)
        found = _container_begins(text)
        if found & forbidden_types:
            return _reject("FORBIDDEN_CONTAINER_PRESENT", f"forbidden_container:{rel_path}")

    # Required container-bearing files.
    container_rules = mapping["containers"]
    for filename, rule in container_rules.items():
        container_type, cardinality = rule
        text = _decode_utf8(file_bytes[filename])
        if container_type == "EXPORT_BLOCK":
            begins, ends = _count_export_blocks(text)
            if cardinality == "exactly_one" and (begins != 1 or ends != 1):
                return _reject("CONTAINER_BOUNDARY_INVALID", "export_block_count")
            try:
                parse_export_block(text)
            except Exception:
                return _reject("CONTAINER_BOUNDARY_INVALID", "export_block_parse")
        elif container_type == "SIM_EVIDENCE_v1":
            begins, ends = _count_exact(text, _SIM_BEGIN, _SIM_END)
            if begins < 1 or ends < 1 or begins != ends:
                return _reject("CONTAINER_BOUNDARY_INVALID", "sim_evidence_count")
            try:
                parsed = parse_sim_evidence_pack(text)
            except Exception:
                return _reject("CONTAINER_BOUNDARY_INVALID", "sim_evidence_parse")
            if not parsed:
                return _reject("CONTAINER_BOUNDARY_INVALID", "sim_evidence_empty")
        elif container_type == "THREAD_S_SAVE_SNAPSHOT_v2":
            begins, ends = _count_exact(text, _SNAP_BEGIN, _SNAP_END)
            if cardinality == "exactly_one" and (begins != 1 or ends != 1):
                return _reject("CONTAINER_BOUNDARY_INVALID", "snapshot_count")
            non_empty = [line.strip() for line in text.splitlines() if line.strip()]
            if not non_empty or non_empty[0] != _SNAP_BEGIN or non_empty[-1] != _SNAP_END:
                return _reject("CONTAINER_BOUNDARY_INVALID", "snapshot_boundaries")
        else:
            return _reject("CONTAINER_BOUNDARY_INVALID", "unknown_container_rule")

    if direction == "BACKWARD":
        if zip_type == "B_TO_A0_STATE_UPDATE_ZIP":
            for forward_source in _FORWARD_REPLAY_SOURCES:
                missing = _missing_forward_sequence(seq_state, run_id, forward_source, sequence)
                if missing is None:
                    continue
                _mark_deterministic_park(seq_state, run_id, source_layer, sequence)
                return _park(f"MISSING_FORWARD_SEQUENCE:{forward_source}:{missing}")
        elif zip_type == "SIM_TO_A0_SIM_RESULT_ZIP":
            horizon = _forward_horizon(seq_state, run_id, "A0")
            if horizon < 1:
                _mark_deterministic_park(seq_state, run_id, source_layer, sequence)
                return _park("MISSING_FORWARD_SEQUENCE:A0:1")
            required_upto = min(sequence, horizon)
            missing = _missing_forward_sequence(seq_state, run_id, "A0", required_upto)
            if missing is not None:
                _mark_deterministic_park(seq_state, run_id, source_layer, sequence)
                return _park(f"MISSING_FORWARD_SEQUENCE:A0:{missing}")

    seq_state[(run_id, source_layer)] = sequence
    return _ok(sequence)
