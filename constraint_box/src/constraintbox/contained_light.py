"""Contained Light OS slice: seed, feasibility, surface, receipt journal.

This module runs the finite Light verbs and writes receipts. It does not
install a wheel, launch Heavy, compute attractors, or measure distinguishability.
The SAT compiler remains ``finite_probe_assignment_feasibility.v1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from constraintbox.bound_quotient import decide_bound_packet
from constraintbox.distinguishability import decide_packet
from constraintbox.manifold_foundation import (
    ManifoldFoundationError,
    validate_foundation,
    validate_foundation_file,
)


SURFACE_SCHEMA = "constraintbox.contained-light-surface.v1"
STATUS_SCHEMA = "constraintbox.contained-light-status.v1"
JOURNAL_SCHEMA = "constraintbox.contained-light-journal.v2"
CLAIM_CEILING = (
    "contained Light source overlay; seed + feasibility + bound quotient; "
    "solver-chosen obs are not measured distinguishability; "
    "not Light-wheel admission; not Heavy"
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


class ContainedLightJournalError(ValueError):
    """A receipt or journal failed a deterministic integrity check."""


def _receipt_digest(receipt: dict[str, Any]) -> str:
    material = dict(receipt)
    material.pop("receipt_sha256", None)
    return _sha256(material)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_root() -> Path:
    env = Path(__file__).resolve()
    # light/src/constraintbox/contained_light.py -> light/
    if env.parent.name == "constraintbox" and env.parent.parent.name == "src":
        light = env.parents[2]
        if (light / "fixtures").is_dir():
            return light.parent if (light.parent / "bin" / "cb").exists() else light
    return Path.cwd()


def journal_path(root: Path) -> Path:
    return root / "receipts" / "light_receipts.sqlite"


def seed_fixture(root: Path) -> Path:
    for candidate in (
        root / "light" / "fixtures" / "cr" / "manifold_time_first_seed_v1.json",
        root / "fixtures" / "cr" / "manifold_time_first_seed_v1.json",
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("time-first seed fixture is missing")


def collapsed_seed_fixture(root: Path) -> Path:
    for candidate in (
        root / "light" / "fixtures" / "cr" / "manifold_time_first_seed_collapsed_v1.json",
        root / "fixtures" / "cr" / "manifold_time_first_seed_collapsed_v1.json",
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("collapsed seed fixture is missing")


def packet_dir(root: Path) -> Path:
    for candidate in (
        root / "light" / "fixtures" / "distinguishability",
        root / "fixtures" / "distinguishability",
    ):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("distinguishability fixtures are missing")


def bound_dir(root: Path) -> Path:
    for candidate in (
        root / "light" / "fixtures" / "bound_observation",
        root / "fixtures" / "bound_observation",
    ):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("bound observation fixtures are missing")


def open_journal(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY,
            ts TEXT NOT NULL,
            verb TEXT NOT NULL,
            status TEXT NOT NULL,
            operation TEXT,
            source_sha256 TEXT,
            receipt_sha256 TEXT,
            prev_receipt_sha256 TEXT,
            path TEXT NOT NULL,
            receipt_json TEXT NOT NULL
        )
        """
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)"
    )
    for key, value in (("schema", JOURNAL_SCHEMA), ("promotion_allowed", "false")):
        con.execute(
            "INSERT INTO meta(k, v) VALUES(?, ?) ON CONFLICT(k) DO NOTHING",
            (key, value),
        )
        stored = con.execute("SELECT v FROM meta WHERE k = ?", (key,)).fetchone()
        if stored != (value,):
            con.close()
            raise ContainedLightJournalError(
                f"REFUSE_JOURNAL_META_MISMATCH:{key}"
            )
    for table in ("operations", "meta"):
        for action in ("UPDATE", "DELETE"):
            trigger = f"refuse_{table}_{action.lower()}"
            con.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS {trigger}
                BEFORE {action} ON {table}
                BEGIN
                    SELECT RAISE(ABORT, 'REFUSE_CONTAINED_LIGHT_APPEND_ONLY');
                END
                """
            )
    con.commit()
    return con


def record_receipt(
    root: Path,
    verb: str,
    receipt: dict[str, Any],
    output: Path,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    body = dict(receipt)
    computed_digest = _receipt_digest(body)
    claimed_digest = body.get("receipt_sha256")
    if claimed_digest is not None and claimed_digest != computed_digest:
        raise ContainedLightJournalError(
            "REFUSE_CALLER_RECEIPT_DIGEST_MISMATCH"
        )
    body["receipt_sha256"] = computed_digest
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    output.write_text(text, encoding="utf-8")
    body = json.loads(output.read_text(encoding="utf-8"))
    digest = _receipt_digest(body)
    if body.get("receipt_sha256") != digest:
        raise ContainedLightJournalError("REFUSE_WRITTEN_RECEIPT_DIGEST_MISMATCH")
    receipt_json = _canonical_bytes(body).decode("ascii")
    con = open_journal(journal_path(root))
    try:
        prev = con.execute(
            "SELECT receipt_sha256 FROM operations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_digest = prev[0] if prev else None
        con.execute(
            """
            INSERT INTO operations
            (ts, verb, status, operation, source_sha256, receipt_sha256,
             prev_receipt_sha256, path, receipt_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now(),
                verb,
                str(body.get("status", "UNKNOWN")),
                body.get("operation"),
                body.get("source_sha256") or body.get("packet_sha256"),
                digest,
                prev_digest,
                str(output),
                receipt_json,
            ),
        )
        con.commit()
    finally:
        con.close()
    return output


def list_operations(root: Path, limit: int = 20) -> list[dict[str, Any]]:
    path = journal_path(root)
    if not path.is_file():
        return []
    con = open_journal(path)
    try:
        rows = con.execute(
            """
            SELECT id, ts, verb, status, operation, source_sha256,
                   receipt_sha256, prev_receipt_sha256, path
            FROM operations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        con.close()
    keys = (
        "id",
        "ts",
        "verb",
        "status",
        "operation",
        "source_sha256",
        "receipt_sha256",
        "prev_receipt_sha256",
        "path",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


def verify_journal(root: Path) -> dict[str, Any]:
    path = journal_path(root)
    if not path.is_file():
        return {
            "status": "PASS",
            "reason_codes": [],
            "row_count": 0,
            "head_receipt_sha256": None,
        }
    con = open_journal(path)
    reasons: list[str] = []
    try:
        rows = con.execute(
            """
            SELECT id, receipt_sha256, prev_receipt_sha256, path, receipt_json
            FROM operations ORDER BY id ASC
            """
        ).fetchall()
        trigger_names = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            ).fetchall()
        }
    finally:
        con.close()
    required_triggers = {
        "refuse_operations_update",
        "refuse_operations_delete",
        "refuse_meta_update",
        "refuse_meta_delete",
    }
    if not required_triggers.issubset(trigger_names):
        reasons.append("HOLD_JOURNAL_APPEND_ONLY_TRIGGER_MISSING")
    previous: str | None = None
    latest_by_path: dict[str, tuple[int, str]] = {}
    for row_id, digest, prev_digest, output_path, receipt_json in rows:
        try:
            body = json.loads(receipt_json)
        except (TypeError, json.JSONDecodeError):
            reasons.append(f"HOLD_JOURNAL_RECEIPT_JSON_INVALID:{row_id}")
            body = {}
        if _receipt_digest(body) != digest or body.get("receipt_sha256") != digest:
            reasons.append(f"HOLD_JOURNAL_RECEIPT_DIGEST_MISMATCH:{row_id}")
        if prev_digest != previous:
            reasons.append(f"HOLD_JOURNAL_CHAIN_MISMATCH:{row_id}")
        previous = digest
        latest_by_path[output_path] = (row_id, receipt_json)
    for output_path, (row_id, receipt_json) in latest_by_path.items():
        candidate = Path(output_path)
        if not candidate.is_file():
            reasons.append(f"HOLD_JOURNAL_OUTPUT_MISSING:{row_id}")
            continue
        try:
            current = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            reasons.append(f"HOLD_JOURNAL_OUTPUT_INVALID:{row_id}")
            continue
        if _canonical_bytes(current).decode("ascii") != receipt_json:
            reasons.append(f"HOLD_JOURNAL_OUTPUT_MISMATCH:{row_id}")
    return {
        "status": "PASS" if not reasons else "HOLD",
        "reason_codes": reasons,
        "row_count": len(rows),
        "head_receipt_sha256": previous,
    }


def packet_surface(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "schema": raw.get("schema"),
        "query": raw.get("query"),
        "theory": raw.get("theory"),
        "probes": list(raw.get("probes") or []),
        "candidates": list(raw.get("candidates") or []),
        "demand_ids": [edge.get("id") for edge in raw.get("demand_D") or []],
        "constraint_ids": [item.get("id") for item in raw.get("constraints_C") or []],
        "caller_claim_ceiling": raw.get("claim_ceiling"),
        "honest_operation": "finite_probe_assignment_feasibility.v1",
    }


def build_surface(root: Path) -> dict[str, Any]:
    seed_path = seed_fixture(root)
    seed_receipt = validate_foundation_file(seed_path)
    packets = []
    for path in sorted(packet_dir(root).glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        packets.append(packet_surface(path, raw))
    bound_packets = []
    try:
        bound_root = bound_dir(root)
    except FileNotFoundError:
        bound_root = None
    if bound_root is not None:
        for path in sorted(bound_root.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            bound_packets.append(
                {
                    "path": str(path),
                    "schema": raw.get("schema"),
                    "candidates": list(raw.get("candidates") or []),
                    "probes": list(raw.get("probes") or []),
                    "row_count": len(raw.get("rows") or []),
                    "honest_operation": "bound_observation_quotient.v1",
                }
            )
    return {
        "schema": SURFACE_SCHEMA,
        "operation": "static_light_surface.v1",
        "status": "PASS",
        "promotion_allowed": False,
        "claim_ceiling": (
            "static Light inventory of supports, constraints, probe packets, "
            "and bound-observation packets; not attractors; not engines; not TDA"
        ),
        "bound_packets": bound_packets,
        "seed": {
            "path": str(seed_path),
            "foundation_id": seed_receipt.get("foundation_id"),
            "status": seed_receipt.get("status"),
            "surface": seed_receipt.get("surface"),
            "capacity_bits_recomputed": seed_receipt.get("checks", {}).get(
                "capacity_bits_recomputed"
            ),
            "delta_capacity_bits_recomputed": seed_receipt.get("checks", {}).get(
                "delta_capacity_bits_recomputed"
            ),
        },
        "packets": packets,
    }


def seed_receipt_for(path: Path) -> dict[str, Any]:
    try:
        return validate_foundation_file(path)
    except (OSError, ManifoldFoundationError, ValueError) as exc:
        return {
            "schema": "constraintbox.manifold-foundation-validation.v1",
            "operation": "finite_time_first_seed_validation.v1",
            "status": "REFUSE",
            "reason": str(exc),
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "source_path": str(path),
        }


def feasibility_receipt_for(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return decide_packet(raw)


def status_receipt(root: Path) -> dict[str, Any]:
    integrity = verify_journal(root)
    return {
        "schema": STATUS_SCHEMA,
        "operation": "contained_light_status.v1",
        "status": integrity["status"],
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "root": str(root),
        "journal": str(journal_path(root)),
        "journal_integrity": integrity,
        "recent": list_operations(root),
    }


def _write_stdout(receipt: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m constraintbox.contained_light")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="contained Light root (bin/ + light/ or repo constraint_box/)",
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        default=None,
        help="dynamic receipt/journal root; defaults to --root",
    )
    sub = parser.add_subparsers(dest="verb", required=True)
    seed_p = sub.add_parser("seed")
    seed_p.add_argument("path", nargs="?", type=Path)
    seed_p.add_argument("--out", type=Path)
    feas_p = sub.add_parser("feasibility")
    feas_p.add_argument("path", nargs="?", type=Path)
    feas_p.add_argument("--out", type=Path)
    surf_p = sub.add_parser("surface")
    surf_p.add_argument("--out", type=Path)
    quot_p = sub.add_parser("quotient")
    quot_p.add_argument("path", nargs="?", type=Path)
    quot_p.add_argument("--out", type=Path)
    stat_p = sub.add_parser("status")
    stat_p.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    root = (args.root or Path.cwd()).expanduser().resolve()
    state_root = (args.state_root or root).expanduser().resolve()

    if args.verb == "seed":
        path = (args.path or seed_fixture(root)).expanduser().resolve()
        receipt = seed_receipt_for(path)
        dest = args.out or (state_root / "receipts" / "seed.json")
        record_receipt(state_root, "seed", receipt, dest)
        _write_stdout(receipt)
        return 0 if receipt.get("status") == "PASS" else 2
    if args.verb == "feasibility":
        path = (
            args.path or (packet_dir(root) / "positive_distinguish.json")
        ).expanduser().resolve()
        receipt = feasibility_receipt_for(path)
        dest = args.out or (state_root / "receipts" / "feasibility.json")
        record_receipt(state_root, "feasibility", receipt, dest)
        _write_stdout(receipt)
        return 0 if receipt.get("status") != "HOLD" else 5
    if args.verb == "surface":
        receipt = build_surface(root)
        dest = args.out or (state_root / "receipts" / "surface.json")
        record_receipt(state_root, "surface", receipt, dest)
        _write_stdout(receipt)
        return 0
    if args.verb == "quotient":
        path = (
            args.path or (bound_dir(root) / "bound_split.json")
        ).expanduser().resolve()
        receipt = decide_bound_packet(json.loads(path.read_text(encoding="utf-8")))
        dest = args.out or (state_root / "receipts" / "quotient.json")
        record_receipt(state_root, "quotient", receipt, dest)
        _write_stdout(receipt)
        return 0 if receipt.get("status") == "PASS" else 5
    receipt = status_receipt(state_root)
    dest = args.out or (state_root / "receipts" / "status.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_stdout(receipt)
    return 0 if receipt.get("status") == "PASS" else 5


if __name__ == "__main__":
    raise SystemExit(main())
