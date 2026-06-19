#!/usr/bin/env python3
"""Two-queue + atomic-claim infrastructure.

Lanes:
    lane_A  — tool-capability queue (nonclassical, gated)
    lane_B  — classical baseline queue

States transition via os.rename (atomic on POSIX same-filesystem):
    queue/lane_X/<hash>.json
      -> queue/claimed/<orig_name>.<pid>.<host>
      -> queue/done/<orig_name>  OR  queue/blocked/<orig_name>

Functions:
    enqueue(lane, sim_path)
    claim(lane, worker_id) -> claimed_path | None
    complete(claim_path, exit_code, artifact_path)
    block(claim_path, reason)
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
QUEUE_ROOT = ROOT / "system_v4" / "probes" / "a2_state" / "queue"
STAGE_GATE_SCRIPT = ROOT / "scripts" / "stage_gate.py"
WIZARD_ADMISSION_SCRIPT = SCRIPT_DIR / "wizard_sim_admission.py"
STRICT_WIZARD_QUEUE_ADMISSION = os.environ.get("STRICT_WIZARD_QUEUE_ADMISSION", "1") == "1"
ADMISSION_BYPASS_SENTINEL = (
    ROOT / "system_v5" / "ops" / ".allow_admission_bypass_recovery"
)
ALLOW_ADMISSION_BYPASS_RECOVERY = (
    os.environ.get("ALLOW_ADMISSION_BYPASS_RECOVERY", "0") == "1"
)


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "on", "enabled"}


def _admission_bypass_marker_allows_recovery() -> bool:
    if not ALLOW_ADMISSION_BYPASS_RECOVERY:
        return False
    if not ADMISSION_BYPASS_SENTINEL.exists():
        return False
    try:
        raw = json.loads(ADMISSION_BYPASS_SENTINEL.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(raw, dict):
        return False
    scope = str(raw.get("scope", "")).strip().lower()
    if scope and scope not in {"all", "queue", "queue_claim", "queue-claim", "overnight"}:
        return False
    if not _is_truthy(raw.get("enabled", raw.get("allow", ""))):
        return False

    expires_at = raw.get("expires_at")
    if expires_at is not None:
        try:
            expiry = float(expires_at)
        except (TypeError, ValueError):
            return False
        if time.time() > expiry:
            return False

    return True


CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION = (
    STRICT_WIZARD_QUEUE_ADMISSION
    and not _admission_bypass_marker_allows_recovery()
)

LANES = ("lane_A", "lane_B")
PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}
PLAN_BUCKET_RANK = {"core_ladder": 0, "exploratory": 1, "framework_doctrine": 2}
PLAN_STAGE_RANK = {"early_core": 0, "late_info": 1, "late_axis": 2}
CORE_LADDER_FAMILIES = {
    "axis",
    "axis0",
    "bridge",
    "capability",
    "clifford",
    "cvc5",
    "geom",
    "geomstats",
    "gerbe",
    "gtower",
    "gudhi",
    "integration",
    "lego",
    "pure",
    "pyg",
    "qit",
    "rustworkx",
    "spectral",
    "toponetx",
    "torch",
    "weyl",
    "xgi",
    "z3",
}
FRAMEWORK_DOCTRINE_FAMILIES = {"fep", "holodeck", "iching", "igt", "leviathan"}
LATE_INFO_KEYWORDS = (
    "bipartite",
    "entanglement",
    "mutual_information",
    "mutual_info",
    "coherent_information",
    "coherent_info",
    "concurrence",
    "negativity",
    "schmidt",
    "entropy",
    "capacity",
    "capacities",
    "carnot",
    "szilard",
    "landauer",
    "thermo",
)
BRIDGE_RUNNER_TOKENS = (
    "bridge",
    "coupling",
    "pairwise",
    "coexistence",
    "engine",
    "qit",
    "mega",
    "mega_sim",
    "nonclassical",
    "tool_serving_lego",
    "xi",
    "rho_ab",
    "phi0",
    "cut",
    "emergence",
)


def _ensure_dirs() -> None:
    for sub in ("lane_A", "lane_B", "claimed", "blocked", "done"):
        (QUEUE_ROOT / sub).mkdir(parents=True, exist_ok=True)


def _lane_dir(lane: str) -> Path:
    if lane not in LANES:
        raise ValueError(f"unknown lane: {lane}")
    return QUEUE_ROOT / lane


def _result_json_path(sim_path: str | Path) -> Path:
    stem = Path(sim_path).stem
    return ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / f"{stem}_results.json"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _wizard_admission_report(sim_path: str, admission_file: str | None = None) -> dict[str, object]:
    stem = Path(sim_path).stem
    proc = subprocess.run(
        [
            sys.executable,
            str(WIZARD_ADMISSION_SCRIPT),
            "--basename",
            stem,
            "--sim-path",
            str(sim_path),
            "--repo-root",
            str(ROOT),
            *(["--admission-file", admission_file] if admission_file else []),
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        check=False,
    )
    try:
        report = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        report = {"ok": False, "reason": "invalid_admission_report", "stderr": proc.stderr[-1000:]}
    report["returncode"] = proc.returncode
    return report


def _wizard_admission_allows_sim(sim_path: str, admission_file: str | None = None) -> bool:
    return bool(_wizard_admission_report(sim_path, admission_file).get("ok"))


def enqueue(lane: str, sim_path: str, admission_file: str | None = None) -> Path:
    _ensure_dirs()
    claim = _stage_gate_claim_for_sim(sim_path)
    if claim is not None and not _stage_gate_allows_claim(claim):
        return _write_blocked_payload(lane, sim_path, "stage_gate_blocked", claim)
    if (STRICT_WIZARD_QUEUE_ADMISSION or admission_file) and not _wizard_admission_allows_sim(
        sim_path,
        admission_file,
    ):
        return _write_blocked_payload(lane, sim_path, "wizard_admission_blocked", claim)
    ld = _lane_dir(lane)
    payload = {
        "sim_path": str(sim_path),
        "result_json_path": str(_result_json_path(sim_path)),
        "lane": lane,
        "enqueued_at": time.time(),
    }
    if admission_file:
        payload["wizard_admission_file"] = str(admission_file)
    h = hashlib.sha1(f"{lane}:{sim_path}".encode()).hexdigest()[:16]
    target = ld / f"{h}.json"
    tmp = ld / f".{h}.json.tmp"
    tmp.write_text(json.dumps(payload, sort_keys=True))
    os.rename(tmp, target)  # atomic publish
    return target


def _write_blocked_payload(lane: str, sim_path: str, reason: str, claim: str | None = None) -> Path:
    _ensure_dirs()
    payload = {
        "blocked_at": time.time(),
        "blocked_reason": reason,
        "blocked_stage_claim": claim,
        "sim_path": str(sim_path),
        "result_json_path": str(_result_json_path(sim_path)),
        "lane": lane,
        "plan_bucket": _plan_bucket_from_sim_path(sim_path),
        "plan_stage": _plan_stage_from_sim_path(sim_path),
    }
    h = hashlib.sha1(f"{lane}:{sim_path}:{reason}:{claim}".encode()).hexdigest()[:16]
    target = QUEUE_ROOT / "blocked" / f"{h}.json"
    target.write_text(json.dumps(payload, sort_keys=True))
    return target


def _sim_family(sim_path: str) -> str:
    stem = Path(sim_path).stem
    if stem.startswith("sim_"):
        stem = stem[4:]
    head = stem.split("_", 1)[0]
    return head or "other"


def _plan_bucket_from_sim_path(sim_path: str) -> str:
    family = _sim_family(sim_path)
    if family in CORE_LADDER_FAMILIES:
        return "core_ladder"
    if family in FRAMEWORK_DOCTRINE_FAMILIES:
        return "framework_doctrine"
    return "exploratory"


def _priority_for_bucket(bucket: str) -> str:
    if bucket == "core_ladder":
        return "high"
    if bucket == "framework_doctrine":
        return "low"
    return "normal"


def _plan_stage_from_sim_path(sim_path: str) -> str:
    stem = Path(sim_path).stem
    if stem.startswith("sim_"):
        stem = stem[4:]
    if stem.startswith("classical_baseline_"):
        return "early_core"
    family = _sim_family(sim_path)
    if family in {"axis", "axis0"}:
        return "late_axis"
    if any(token in stem for token in LATE_INFO_KEYWORDS):
        return "late_info"
    return "early_core"


def _stage_gate_claim_for_sim(sim_path: str | Path) -> str | None:
    result = _load_json(_result_json_path(sim_path))
    if (
        result.get("classification") == "tool_lego_fit_probe"
        and result.get("promotion_allowed") is False
    ):
        return None
    stem = Path(sim_path).stem.lower()
    if stem.startswith("sim_"):
        stem = stem[4:]
    if stem.startswith("classical_baseline_"):
        return None
    family = _sim_family(str(sim_path))
    if "tier_d" in stem or "boundary_flux" in stem or (
        "boundary" in stem and "admissibility" in stem
    ):
        return "tier_d"
    if family in {"axis", "axis0"}:
        return "axis"
    if any(token in stem for token in BRIDGE_RUNNER_TOKENS):
        return "scientific_coupling"
    if any(token in stem for token in LATE_INFO_KEYWORDS):
        return "default_late_stage"
    return "off_program"


def _stage_gate_allows_claim(claim: str) -> bool:
    try:
        proc = subprocess.run(
            [sys.executable, str(STAGE_GATE_SCRIPT), "--claim", claim],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except Exception:
        return False
    return proc.returncode == 0


def _effective_priority(priority: str | None, bucket: str) -> str:
    desired = _priority_for_bucket(bucket)
    if not priority:
        return desired
    given = str(priority).lower()
    if PRIORITY_RANK.get(given, PRIORITY_RANK["normal"]) > PRIORITY_RANK[desired]:
        return desired
    return given


def _claim_order(item: Path) -> tuple[int, int, int, float, str]:
    try:
        data = json.loads(item.read_text())
    except Exception:
        return (
            PRIORITY_RANK["normal"],
            PLAN_BUCKET_RANK["exploratory"],
            PLAN_STAGE_RANK["early_core"],
            0.0,
            item.name,
        )
    bucket = str(data.get("plan_bucket") or _plan_bucket_from_sim_path(str(data.get("sim_path", ""))))
    stage = str(data.get("plan_stage") or _plan_stage_from_sim_path(str(data.get("sim_path", ""))))
    priority = _effective_priority(data.get("priority"), bucket)
    try:
        enqueued_at = float(data.get("enqueued_at", 0))
    except Exception:
        enqueued_at = 0.0
    return (
        PRIORITY_RANK.get(priority, PRIORITY_RANK["normal"]),
        PLAN_BUCKET_RANK.get(bucket, PLAN_BUCKET_RANK["exploratory"]),
        PLAN_STAGE_RANK.get(stage, PLAN_STAGE_RANK["early_core"]),
        enqueued_at,
        item.name,
    )


def _base_done_id(claim_path: Path) -> str:
    name = claim_path.name
    if ".json." not in name:
        return name
    return name.split(".json.")[0]


def _done_duplicate_candidates(claim_path: Path) -> list[Path]:
    base = _base_done_id(claim_path)
    pattern = f"{base}.json.*"
    return sorted((QUEUE_ROOT / "done").glob(pattern))


def claim(lane: str, worker_id: str) -> Path | None:
    """Atomic claim via os.rename. Returns claimed path or None if queue empty."""
    _ensure_dirs()
    ld = _lane_dir(lane)
    claimed_dir = QUEUE_ROOT / "claimed"
    pid = os.getpid()
    host = socket.gethostname().split(".")[0]
    blocked_barrier_order: tuple[int, int] | None = None
    # Snapshot then race; os.rename on same fs is atomic and fails if src missing
    for item in sorted(ld.glob("*.json"), key=_claim_order):
        item_order = _claim_order(item)
        if blocked_barrier_order and item_order[:2] > blocked_barrier_order:
            return None
        target = claimed_dir / f"{item.name}.{pid}.{host}.{worker_id}"
        try:
            os.rename(item, target)
        except FileNotFoundError:
            continue  # another worker got it
        # append claim metadata
        data = json.loads(target.read_text())
        data.setdefault("result_json_path", str(_result_json_path(str(data.get("sim_path", "")))))
        data["claimed_by"] = worker_id
        data["claimed_pid"] = pid
        data["claimed_host"] = host
        data["claimed_at"] = time.time()
        target.write_text(json.dumps(data, sort_keys=True))
        claim = _stage_gate_claim_for_sim(str(data.get("sim_path", "")))
        if claim is not None and not _stage_gate_allows_claim(claim):
            data["blocked_reason"] = "stage_gate_blocked"
            data["blocked_stage_claim"] = claim
            data["blocked_at"] = time.time()
            _write_terminal(target, data, "blocked")
            blocked_barrier_order = item_order[:2]
            continue
        if CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION and not _wizard_admission_allows_sim(
            str(data.get("sim_path", "")),
            data.get("wizard_admission_file"),
        ):
            data["blocked_reason"] = "wizard_admission_blocked"
            data["blocked_at"] = time.time()
            _write_terminal(target, data, "blocked")
            blocked_barrier_order = item_order[:2]
            continue
        return target
    return None


def _write_terminal(claim_path: Path, data: dict, subdir: str) -> Path:
    if subdir == "done":
        duplicates = _done_duplicate_candidates(claim_path)
        if duplicates:
            data["blocked_reason"] = "done_duplicate_conflict"
            data["blocked_done_ids"] = [str(d) for d in duplicates]
            data["blocked_at"] = time.time()
            return _write_terminal(claim_path, data, "blocked")

    target = QUEUE_ROOT / subdir / claim_path.name
    tmp = claim_path.with_suffix(claim_path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, sort_keys=True))
    os.rename(tmp, target)
    claim_path.unlink(missing_ok=True)
    return target


def _validate_receipt(result_json_path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_receipt.py"),
            "--strict-scope",
            "--require-executable",
            "--require-run-boundary",
            result_json_path,
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def complete(
    claim_path: str | Path,
    exit_code: int,
    artifact_path: str,
    *,
    require_receipt: bool = False,
) -> Path:
    claim_path = Path(claim_path)
    if claim_path.parent.name != "claimed":
        raise ValueError(f"claim_path must be inside queue/claimed: {claim_path}")
    data = json.loads(claim_path.read_text())
    data["exit_code"] = exit_code
    data["artifact_path"] = str(artifact_path)
    data["completed_at"] = time.time()
    data.setdefault("result_json_path", str(_result_json_path(str(data.get("sim_path", "")))))
    if exit_code != 0:
        data["blocked_reason"] = f"exit_code_{exit_code}"
        data["blocked_at"] = time.time()
        return _write_terminal(claim_path, data, "blocked")
    if require_receipt:
        receipt = _validate_receipt(str(data.get("result_json_path") or ""))
        data["receipt_validation_exit_code"] = receipt.returncode
        data["receipt_validation_stdout"] = receipt.stdout[-8000:]
        data["receipt_validation_stderr"] = receipt.stderr[-8000:]
        if receipt.returncode != 0:
            data["blocked_reason"] = "receipt_validation_failed"
            data["blocked_at"] = time.time()
            return _write_terminal(claim_path, data, "blocked")
        data["receipt_admission"] = "strict_executable_run_boundary"
    else:
        data["receipt_admission"] = "not_required"
    return _write_terminal(claim_path, data, "done")


def block(claim_path: str | Path, reason: str) -> Path:
    claim_path = Path(claim_path)
    data = json.loads(claim_path.read_text())
    data["blocked_reason"] = reason
    data["blocked_at"] = time.time()
    return _write_terminal(claim_path, data, "blocked")


def counts() -> dict:
    _ensure_dirs()
    return {
        sub: len(list((QUEUE_ROOT / sub).glob("*.json*")))
        for sub in ("lane_A", "lane_B", "claimed", "blocked", "done")
    }


def _claimed_matches(worker: str | None) -> list[Path]:
    claimed_dir = QUEUE_ROOT / "claimed"
    if not worker:
        return []
    return sorted(claimed_dir.glob(f"*.{worker}"))


def _resolve_claim_path(*, claim_path: str | None, worker: str | None) -> Path:
    if claim_path:
        return Path(claim_path)

    matches = _claimed_matches(worker)
    if not matches:
        raise FileNotFoundError(f"no claimed item found for worker={worker!r}")
    if len(matches) > 1:
        raise RuntimeError(
            f"ambiguous claimed item for worker={worker!r}; pass --claim-path explicitly"
        )
    return matches[0]


def _parse_flags(argv):
    flags = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                flags[key] = argv[i + 1]
                i += 2
            else:
                flags[key] = True
                i += 1
        else:
            i += 1
    return flags


def _lane_from_queue(queue_arg: str) -> str:
    base = Path(queue_arg).name
    if base in LANES:
        return base
    raise ValueError(f"unknown lane: {queue_arg}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "counts"
    rest = sys.argv[2:]
    flags = _parse_flags(rest)

    if cmd == "counts":
        print(json.dumps(counts(), indent=2))
    elif cmd == "enqueue":
        lane = flags.get("lane") or rest[0]
        sim = flags.get("sim") or rest[1]
        print(enqueue(lane, sim, flags.get("admission-file")))
    elif cmd == "claim":
        if "queue" in flags:
            lane = _lane_from_queue(flags["queue"])
            worker = flags.get("worker", "w0")
        else:
            lane, worker = rest[0], rest[1]
        p = claim(lane, worker)
        if p:
            data = json.loads(Path(p).read_text())
            data["claim_path"] = str(p)
            data["sim"] = data.get("sim_path", "")
            print(json.dumps(data))
        # empty -> print nothing; runner treats empty stdout as "no work"
    elif cmd == "complete":
        worker = flags.get("worker")
        claim_path = flags.get("claim-path")
        exit_code = int(flags.get("exit", 0))
        artifact = flags.get("artifact", "")
        terminal = complete(
            _resolve_claim_path(claim_path=claim_path, worker=worker),
            exit_code,
            artifact,
            require_receipt=bool(flags.get("require-receipt", False)),
        )
        terminal_payload = _load_json(terminal)
        print(
            json.dumps(
                {
                    "blocked_reason": terminal_payload.get("blocked_reason"),
                    "terminal_path": str(terminal),
                    "terminal_state": terminal.parent.name,
                }
            )
        )
    elif cmd == "block":
        worker = flags.get("worker")
        claim_path = flags.get("claim-path")
        reason = flags.get("reason", "unspecified")
        block(_resolve_claim_path(claim_path=claim_path, worker=worker), reason)
    else:
        sys.exit(f"unknown cmd: {cmd}")
