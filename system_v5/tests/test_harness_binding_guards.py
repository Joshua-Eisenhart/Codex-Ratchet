from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE_CLAIM = REPO_ROOT / "scripts" / "queue_claim.py"
STAGE_GATE = REPO_ROOT / "scripts" / "stage_gate.py"
WIZARD_ADMISSION = REPO_ROOT / "scripts" / "wizard_sim_admission.py"
REGISTRY = (
    REPO_ROOT
    / "system_v4"
    / "probes"
    / "a2_state"
    / "sim_results"
    / "actual_lego_registry.json"
)


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    module_parent = str(path.parent)
    inserted_parent = False
    if module_parent not in sys.path:
        sys.path.insert(0, module_parent)
        inserted_parent = True
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)
        if inserted_parent:
            sys.path.remove(module_parent)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_queue_claim_blocks_off_program_toy_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module("queue_claim_off_program_under_test", QUEUE_CLAIM)
    queue_root = tmp_path / "queue"
    monkeypatch.setattr(module, "QUEUE_ROOT", queue_root)
    monkeypatch.setattr(module, "STRICT_WIZARD_QUEUE_ADMISSION", False)
    monkeypatch.setattr(module, "CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION", False)

    terminal = module.enqueue("lane_A", "system_v4/probes/sim_totally_made_up_toy.py")

    assert terminal.parent.name == "blocked"
    payload = json.loads(terminal.read_text(encoding="utf-8"))
    assert payload["blocked_reason"] == "stage_gate_blocked"
    assert payload["blocked_stage_claim"] == "off_program"


def test_stage_gate_has_default_closed_off_program_claim() -> None:
    proc = subprocess.run(
        [sys.executable, str(STAGE_GATE), "--claim", "off_program"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["requested_claim"] == {
        "allowed": False,
        "claim": "off_program",
        "reason": "off_program is blocked because allow_off_program=false",
    }


def test_order_sensitivity_override_admission_binds_registry_and_load_bearing_tool() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(WIZARD_ADMISSION),
            "--repo-root",
            str(REPO_ROOT),
            "--basename",
            "order_sensitivity_scratch_diagnostic",
            "--sim-path",
            "system_v7/sims/order_sensitivity_noncommutation_floor_v0/order_sensitivity_scratch_diagnostic.py",
            "--expected-result-path",
            "system_v7/sims/order_sensitivity_noncommutation_floor_v0/order_sensitivity_scratch_diagnostic_results.json",
        ],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert {
        "basename_not_in_canonical_registry",
        "no_load_bearing_tool",
    } <= set(payload["findings"])


def test_wizard_admission_accepts_registry_member_with_load_bearing_tool(tmp_path: Path) -> None:
    module = _load_module("wizard_sim_admission_registry_member_under_test", WIZARD_ADMISSION)
    repo = tmp_path / "repo"
    stage_gate = repo / "scripts" / "stage_gate.py"
    stage_gate.parent.mkdir(parents=True)
    stage_gate.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
    stage_gate.chmod(0o755)
    registry_copy = (
        repo
        / "system_v4"
        / "probes"
        / "a2_state"
        / "sim_results"
        / "actual_lego_registry.json"
    )
    registry_copy.parent.mkdir(parents=True)
    shutil.copyfile(REGISTRY, registry_copy)
    result_path = registry_copy.parent / "probe_object_results.json"
    result_path.write_text(
        json.dumps(
            {
                "name": "probe_object",
                "classification": "canonical",
                "tool_manifest": {
                    "z3": {"tried": True, "used": True, "reason": "load-bearing finite fixture"}
                },
                "tool_integration_depth": {"z3": "load_bearing"},
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"result_path": str(result_path), "result_sha256": _sha256(result_path)}),
        encoding="utf-8",
    )
    payload = {
        "schema": "wizard_sim_admission_v4_2",
        "basename": "probe_object",
        "sim_path": "system_v4/probes/sim_probe_object.py",
        "status": "queue_ready",
        "admitted_by": "guard.receipt_audit",
        "admission_artifact": str(artifact),
        "controller_read_artifacts": [str(artifact), str(result_path)],
        "formal_sim_profile": {
            "stage": "micro",
            "claim": "one bounded registry-member claim",
            "exact_tool_or_function": "z3.Solver.check",
            "expected_result_path": str(result_path),
        },
        "packet_contract": {
            "type": "MICRO",
            "tool_target": "z3",
            "function_surface": "z3.Solver.check",
            "micro_claim": "one bounded registry-member claim",
            "prior_function_receipts": [],
            "promotion_boundary": "no promotion without a later admitted packet",
        },
    }

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert findings == []


class _FakeBuilder:
    def __init__(self, nodes: dict[str, object] | None = None) -> None:
        self.pydantic_model = SimpleNamespace(nodes=nodes or {})
        self.added_nodes: list[object] = []
        self.added_edges: list[object] = []

    def add_node(self, node: object) -> None:
        self.added_nodes.append(node)
        self.pydantic_model.nodes[getattr(node, "id")] = node

    def add_edge(self, edge: object) -> None:
        self.added_edges.append(edge)


class _FakeRefinery:
    def __init__(self, nodes: dict[str, object] | None = None) -> None:
        self.builder = _FakeBuilder(nodes)
        self.saved = False
        self.findings: list[str] = []

    def log_finding(self, message: str) -> None:
        self.findings.append(message)

    def _save(self) -> None:
        self.saved = True


def _candidate_node(node_id: str, name: str = "Candidate") -> SimpleNamespace:
    return SimpleNamespace(id=node_id, layer="B_KERNEL", name=name, properties={})


def test_graveyard_rejects_missing_candidate_ids() -> None:
    module = _load_module("graveyard_router_binding_under_test", REPO_ROOT / "system_v4/skills/graveyard_router.py")
    router = module.GraveyardRouter(_FakeRefinery())

    with pytest.raises(ValueError, match="candidate_id not found"):
        router.route_to_graveyard(
            candidate_id="totally_made_up_toy",
            reason_tag="TEST",
            failure_class="SIM_KILL",
            raw_lines=[],
            sim_evidence={},
        )

    with pytest.raises(ValueError, match="candidate_id not found"):
        router.route_parked(
            candidate_id="totally_made_up_toy",
            reason_tag="TEST",
            raw_lines=[],
        )


def test_graveyard_parks_existing_candidate_id() -> None:
    module = _load_module("graveyard_router_existing_under_test", REPO_ROOT / "system_v4/skills/graveyard_router.py")
    refinery = _FakeRefinery({"candidate_1": _candidate_node("candidate_1")})
    router = module.GraveyardRouter(refinery)

    node_id = router.route_parked(
        candidate_id="candidate_1",
        reason_tag="TEST",
        raw_lines=["park existing only"],
    )

    assert node_id == "PARKED::candidate_1"
    assert refinery.saved is True
    assert refinery.builder.added_edges
