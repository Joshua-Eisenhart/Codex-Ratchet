import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import json
import sys
from pathlib import Path

RATCHET = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RATCHET))

from b_kernel import BKernel
from evidence_store import input_hash_from_string, write_manifest
from state import KernelState

FIXTURES = Path(__file__).resolve().parent / "fixtures"
EXPECTED = Path(__file__).resolve().parent / "expected_outcomes.json"


def load_expected():
    data = json.loads(EXPECTED.read_text())
    return {d["fixture_name"]: d for d in data}


def detect_container(text: str) -> str:
    t = text.lstrip()
    if t.startswith("BEGIN EXPORT_BLOCK"):
        return "EXPORT_BLOCK"
    if t.startswith("BEGIN SIM_EVIDENCE v1"):
        return "SIM_EVIDENCE"
    if t.startswith("BEGIN THREAD_S_SAVE_SNAPSHOT v2"):
        return "THREAD_S_SAVE_SNAPSHOT"
    return "UNKNOWN"


def _prepare_sim_evidence_fixture(text: str, repo_root: Path) -> str:
    lines = text.splitlines()
    output = []
    current = None
    for line in lines:
        if line.strip() == "BEGIN SIM_EVIDENCE v1":
            current = [line]
            continue
        if current is not None:
            current.append(line)
            if line.strip() == "END SIM_EVIDENCE v1":
                block = _materialize_sim_block(current, repo_root)
                output.extend(block.splitlines())
                current = None
            continue
        output.append(line)
    return "\n".join(output) + ("\n" if text.endswith("\n") else "")


def _materialize_sim_block(lines, repo_root: Path) -> str:
    sim_id = None
    code_hash = None
    output_hash = None
    input_hash = None
    manifest_hash = None
    kept = []
    for line in lines:
        s = line.strip()
        if s.startswith("SIM_ID:"):
            sim_id = s.split(":", 1)[1].strip()
            kept.append(line)
            continue
        if s.startswith("CODE_HASH_SHA256:"):
            code_hash = s.split(":", 1)[1].strip()
            kept.append(line)
            continue
        if s.startswith("OUTPUT_HASH_SHA256:"):
            output_hash = s.split(":", 1)[1].strip()
            kept.append(line)
            continue
        if s.startswith("INPUT_HASH_SHA256:"):
            val = s.split(":", 1)[1].strip()
            if val == "AUTO":
                val = input_hash_from_string(f"input:{sim_id}")
                line = f"INPUT_HASH_SHA256: {val}"
            input_hash = val
            kept.append(line)
            continue
        if s.startswith("RUN_MANIFEST_SHA256:"):
            val = s.split(":", 1)[1].strip()
            if val == "AUTO":
                val = write_manifest(
                    repo_root,
                    {
                        "sim_id": sim_id,
                        "code_hash_sha256": code_hash,
                        "output_hash_sha256": output_hash,
                        "input_hash_sha256": input_hash,
                    },
                )
                line = f"RUN_MANIFEST_SHA256: {val}"
            manifest_hash = val
            kept.append(line)
            continue
        kept.append(line)
    return "\n".join(kept)


def run_fixture(kernel: BKernel, text: str, fixture_name: str, repo_root: Path) -> dict:
    events = []

    def log_fn(ev):
        events.append(ev)

    state = KernelState()
    if fixture_name.startswith("ruleset_gate_"):
        state.active_ruleset_sha256 = "a" * 64
    if fixture_name.startswith("megaboot_gate_"):
        state.active_megaboot_sha256 = "b" * 64
    if "SIM_EVIDENCE" in text:
        text = _prepare_sim_evidence_fixture(text, repo_root)
    kernel.evaluate_message(text, state, log_fn=log_fn)

    status = "PASS"
    tags = []
    for ev in events:
        if ev.get("event") == "reject":
            status = "REJECT"
            if ev.get("reason"):
                tags.append(ev["reason"])
        elif ev.get("event") == "park" and status != "REJECT":
            status = "PARK"
            if ev.get("reason"):
                tags.append(ev["reason"])
        elif ev.get("event") == "accept":
            pass

    if status == "PASS" and not any(e.get("event") == "accept" for e in events):
        status = "UNKNOWN"

    return {"status": status, "tags": sorted(set(tags)), "events": events}


def main():
    expected = load_expected()
    bootpack = REPO / "core_docs" / "BOOTPACK_THREAD_B_v3.9.13.md"
    kernel = BKernel(str(bootpack))

    failures = []
    for fixture_name in sorted(expected.keys()):
        fixture_path = FIXTURES / fixture_name
        if not fixture_path.exists():
            failures.append({"fixture": fixture_name, "error": "missing fixture"})
            continue
        text = fixture_path.read_text()
        actual = run_fixture(kernel, text, fixture_name, REPO)
        exp = expected[fixture_name]
        if exp["expected_status"] == "DEFERRED":
            continue
        if actual["status"] != exp["expected_status"] or actual["tags"] != sorted(exp["expected_tags"]):
            failures.append({
                "fixture": fixture_name,
                "expected": exp,
                "actual": {"status": actual["status"], "tags": actual["tags"]},
            })

    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, indent=2, sort_keys=True))
        sys.exit(1)

    print(json.dumps({"status": "PASS", "count": len(expected)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
