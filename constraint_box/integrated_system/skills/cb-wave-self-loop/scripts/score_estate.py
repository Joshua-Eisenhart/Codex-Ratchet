#!/usr/bin/env python3
"""Score the CB wave estate through CB validators and Light gates."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path


SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
BOX = Path(os.environ.get("CB_BOX_ROOT", Path(__file__).resolve().parents[4]))
PY = Path(os.environ.get("CB_LIGHT_PYTHON", BOX / ".venv" / "bin" / "python"))
V1 = SKILLS / "cb-wave-author" / "scripts" / "validate_wave.py"
ZIP_VAL = SKILLS / "zip-failure-wave" / "scripts" / "validate_wave.py"
SEED = BOX / "scripts" / "contained_light" / "seed_check.py"
PACKET = BOX / "fixtures" / "distinguishability" / "positive_distinguish.json"
NEGATIVE = BOX / "fixtures" / "distinguishability" / "collapsed_demand.json"
STATE = Path(
    os.environ.get(
        "CB_WAVE_SELF_LOOP_STATE_DIR",
        str(BOX / "receipts" / "wave_self_loop" / "state"),
    )
)
CONTEXT = STATE / "context.receipt.json"
GOODHART_WAVE = SKILLS / "cb-goodhart-wave" / "wave.json"
ACTIVE_WAVES = Path(
    os.environ.get("CB_ACTIVE_WAVE_MANIFEST", SKILLS / "ACTIVE_WAVES.json")
)


def _run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BOX / "src")
    env["PYTHONNOUSERSITE"] = "1"
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False, env=env)


def _json_out(proc: subprocess.CompletedProcess[str]) -> dict:
    text = (proc.stdout or "").strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _pytest_count(path: Path) -> tuple[int, bool]:
    proc = _run([str(PY), "-m", "pytest", "-q", "-p", "no:cacheprovider", str(path)])
    passed = 0
    for line in (proc.stdout or "").splitlines():
        if " passed" in line:
            try:
                passed = int(line.split()[0])
            except ValueError:
                passed = 0
    return passed, proc.returncode == 0


def _active_wave_paths() -> tuple[list[Path], Path, str]:
    body = json.loads(ACTIVE_WAVES.read_text(encoding="utf-8"))
    if body.get("schema") != "constraintbox.active-wave-set.v1":
        raise ValueError("active wave manifest schema")
    declared = body.get("wave_definitions")
    zip_declared = body.get("zip_wave_definition")
    if not isinstance(declared, list) or not declared or not isinstance(zip_declared, str):
        raise ValueError("active wave manifest fields")
    paths = [SKILLS / str(value) for value in declared]
    if any(not path.is_file() for path in [*paths, SKILLS / zip_declared]):
        raise ValueError("active wave definition missing")
    return paths, SKILLS / zip_declared, hashlib.sha256(ACTIVE_WAVES.read_bytes()).hexdigest()


def score() -> dict:
    manifest_error = None
    try:
        v1_paths, zip_path, active_manifest_sha256 = _active_wave_paths()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        v1_paths = []
        zip_path = SKILLS / "zip-failure-wave" / "wave.json"
        active_manifest_sha256 = None
        manifest_error = f"{type(exc).__name__}:{exc}"
    valid_v1 = 0
    invalid_v1 = (
        [{"path": str(ACTIVE_WAVES), "errors": [manifest_error]}]
        if manifest_error
        else []
    )
    for path in v1_paths:
        proc = _run([str(PY), str(V1), str(path)])
        body = _json_out(proc)
        if body.get("disposition") == "WAVE_DEFINITION_VALID":
            valid_v1 += 1
        else:
            invalid_v1.append({"path": str(path), "errors": body.get("errors", [proc.stderr[-200:]])})

    zip_proc = _run([str(PY), str(ZIP_VAL), str(zip_path)])
    zip_body = _json_out(zip_proc)
    zip_valid = zip_body.get("disposition") == "ZIP_WAVE_DEFINITION_VALID"

    test_paths = list(SKILLS.glob("cb-*-wave/tests/test_*.py"))
    test_paths.extend(SKILLS.glob("goodhart-proxy-guard/tests/test_*.py"))
    test_paths.extend(SKILLS.glob("paperclip-scope-guard/tests/test_*.py"))
    test_paths.extend(SKILLS.glob("mass-drift-guard/tests/test_*.py"))
    test_paths.extend(SKILLS.glob("cb-wave-self-loop/tests/test_*.py"))
    tests_passed = 0
    test_failures = []
    for tests in sorted(set(test_paths)):
        passed, ok = _pytest_count(tests)
        if ok:
            tests_passed += passed
        else:
            test_failures.append(str(tests))

    STATE.mkdir(parents=True, exist_ok=True)
    seed_proc = _run([str(PY), str(SEED), "--root", str(BOX), "--out", str(STATE / "SEED_CHECK.json")])
    seed_body = _json_out(seed_proc)
    seed_admit = seed_body.get("disposition") == "ADMIT"

    dist_proc = _run(
        [str(PY), "-m", "constraintbox.distinguishability", str(PACKET)],
        cwd=BOX,
    )
    dist_body = _json_out(dist_proc)
    light_decides_control = dist_body.get("status") == "BOUNDED_SAT"

    harvest_packet = STATE / "distinguish.packet.json"
    harvest_receipt = {}
    if harvest_packet.is_file():
        harvest_proc = _run(
            [str(PY), "-m", "constraintbox.distinguishability", str(harvest_packet)],
            cwd=BOX,
        )
        harvest_receipt = _json_out(harvest_proc)
    light_decided_harvest_packet = harvest_receipt.get("status") == "BOUNDED_SAT"

    neg_proc = _run(
        [str(PY), "-m", "constraintbox.distinguishability", str(NEGATIVE)],
        cwd=BOX,
    )
    neg_body = _json_out(neg_proc)
    light_negative_hold = neg_body.get("status") in {"HOLD", "BOUNDED_UNSAT", "UNSAT"}

    context = {}
    if CONTEXT.is_file():
        try:
            loaded = json.loads(CONTEXT.read_text(encoding="utf-8"))
            context = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            context = {}
    alignment_ready = context.get("status") == "CONTEXT_SNAPSHOT_READY"

    goodhart_proc = _run([str(PY), str(V1), str(GOODHART_WAVE)])
    goodhart_wave_valid = _json_out(goodhart_proc).get("disposition") == "WAVE_DEFINITION_VALID"

    light_gate = (
        seed_admit
        and light_decides_control
        and light_negative_hold
        and alignment_ready
        and not invalid_v1
        and zip_valid
    )
    raw = (
        1000 * valid_v1
        + 100 * int(zip_valid)
        + 50 * int(light_decided_harvest_packet)
        + 25 * int(goodhart_wave_valid)
        + tests_passed
    )
    total = raw if light_gate else 0
    return {
        "schema": "constraintbox.wave-estate-score.v2",
        "light_gate": light_gate,
        "seed_admit": seed_admit,
        "light_decides_control": light_decides_control,
        "light_negative_hold": light_negative_hold,
        "light_negative_status": neg_body.get("status"),
        "light_decided_harvest_packet": light_decided_harvest_packet,
        "alignment_ready": alignment_ready,
        "goodhart_wave_valid": goodhart_wave_valid,
        "valid_v1": valid_v1,
        "v1_total": len(v1_paths),
        "invalid_v1": invalid_v1,
        "zip_valid": zip_valid,
        "tests_passed": tests_passed,
        "test_failures": test_failures,
        "harvest_packet_status": harvest_receipt.get("status"),
        "score": total,
        "state_dir": str(STATE),
        "score_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "active_wave_manifest_sha256": active_manifest_sha256,
        "promotion_allowed": False,
    }


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    result = score()
    (STATE / "score.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["light_gate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
