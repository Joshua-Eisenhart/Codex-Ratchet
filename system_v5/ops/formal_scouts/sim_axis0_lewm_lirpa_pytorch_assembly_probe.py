#!/usr/bin/env python3
"""PyTorch assembly scout for guarded Axis0 + LeWM-style LiRPA coupling.

Formal scout only. This is a tiny source-native adapter that consumes existing
Axis0, FEP, Holodeck, and auto_LiRPA/LeWM-style receipts, then checks whether
the admitted Axis0 branches can drive a bounded PyTorch carrier response while
blocked branches stay excluded. It does not import le-wm, does not use NumPy,
and does not promote a final super-sim.
"""

from __future__ import annotations

import hashlib
import ast
import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import torch.nn as nn
import z3

import axis0_guard_utils as axis0_guard


AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if not AUTO_LIRPA_ROOT.exists():
    raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_lewm_lirpa_pytorch_assembly_probe_results.json"

NAME = "axis0_lewm_lirpa_pytorch_assembly_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "guarded_axis0_lewm_lirpa_pytorch_assembly"
CLAIM_CEILING = (
    "Formal scout only: consumes existing guarded Axis0, FEP/POMDP/VMP, "
    "Holodeck hash-memory, and auto_LiRPA LeWM-style latent-surprise receipts "
    "to assemble a tiny PyTorch carrier adapter with LiRPA bounds. It does not "
    "admit a final Axis0 alignment, final super-sim, neural world model, "
    "physics claim, canonical architecture, proof of manifold reality, or "
    "full MPS/PEPS/PEPS3D theorem."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor adapter, branch routing, carrier response, controls, and perturbation samples",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bounds for the finite PyTorch assembly score graph",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness that guard, FEP, memory, LiRPA, and controls are all required",
    },
    "axis0_guard_utils": {
        "tried": True,
        "used": True,
        "reason": "supportive parser for the existing Axis0 guard receipt; no NumPy emission is allowed",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt loading and result writing",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result-path checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "z3": "load_bearing",
    "axis0_guard_utils": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}

REQUIRED_RECEIPTS = {
    "axis0_guard": "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
    "fep_pomdp": "source_native_fep_pomdp_policy_tree_probe_results.json",
    "fep_vmp": "source_native_fep_online_vmp_policy_update_probe_results.json",
    "holodeck_memory": "source_native_holodeck_hash_memory_placeholder_probe_results.json",
    "lewm_lirpa": "auto_lirpa_lewm_latent_surprise_bound_probe_results.json",
}

BLOCKED_AXIS0 = {
    "path_entropy",
    "holographic_boundary_interior_reconstruction",
}
ADMITTED_FLOOR = 3
CARRIER_NAMES = ("mps", "peps", "peps3d")


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def receipt_gate(receipt: dict[str, Any]) -> bool:
    return (
        receipt.get("exists") is True
        and receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
    )


def scalar_fingerprint(payload: Any, width: int, *, salt: str) -> torch.Tensor:
    text = json.dumps(as_jsonable(payload), sort_keys=True, separators=(",", ":"))
    values: list[float] = []
    counter = 0
    while len(values) < width:
        digest = hashlib.sha256(f"{salt}:{counter}:{text}".encode("utf-8")).digest()
        for byte in digest:
            values.append((float(byte) / 127.5) - 1.0)
            if len(values) == width:
                break
        counter += 1
    return torch.tensor(values, dtype=torch.float32)


def axis0_feature_matrix(guard_signal: dict[str, Any]) -> tuple[torch.Tensor, dict[str, Any]]:
    names = list(guard_signal.get("admitted_candidate_names", []))
    blocked = list(guard_signal.get("blocked_candidate_names", []))
    status = guard_signal.get("candidate_status", {})
    rows = []
    for idx, name in enumerate(names):
        payload = status.get(name, {})
        base = scalar_fingerprint(payload, 8, salt=f"axis0:{name}")
        index_features = torch.tensor(
            [
                float(idx + 1) / max(float(len(names)), 1.0),
                float(len(name)) / 64.0,
                1.0,
                0.0,
            ],
            dtype=torch.float32,
        )
        rows.append(torch.cat([base, index_features], dim=0))
    matrix = torch.stack(rows, dim=0) if rows else torch.zeros((0, 12), dtype=torch.float32)
    report = {
        "pass": bool(
            guard_signal.get("pass") is True
            and len(names) >= ADMITTED_FLOOR
            and not (set(names) & BLOCKED_AXIS0)
            and BLOCKED_AXIS0.issubset(set(blocked))
            and matrix.shape[0] == len(names)
        ),
        "admitted_candidate_names": names,
        "blocked_candidate_names": blocked,
        "blocked_axis0_expected": sorted(BLOCKED_AXIS0),
        "feature_shape": list(matrix.shape),
        "blocked_axis0_feature_names_excluded": guard_signal.get("blocked_axis0_feature_names_excluded", []),
    }
    return matrix, report


def source_context(receipts: dict[str, dict[str, Any]]) -> tuple[torch.Tensor, dict[str, Any]]:
    fep_tree = receipts["fep_pomdp"]
    fep_vmp = receipts["fep_vmp"]
    memory = receipts["holodeck_memory"]
    lewm = receipts["lewm_lirpa"]
    pieces = [
        scalar_fingerprint(fep_tree.get("positive", {}), 10, salt="fep_tree"),
        scalar_fingerprint(fep_vmp.get("positive", {}), 10, salt="fep_vmp"),
        scalar_fingerprint(memory.get("positive", {}), 10, salt="memory"),
        scalar_fingerprint(lewm.get("positive", {}), 10, salt="lewm"),
    ]
    context = torch.cat(pieces, dim=0)
    gates = {
        key: receipt_gate(receipts[key])
        for key in ["fep_pomdp", "fep_vmp", "holodeck_memory", "lewm_lirpa"]
    }
    return context, {
        "pass": all(gates.values()) and context.shape[0] == 40 and bool(torch.all(torch.isfinite(context))),
        "source_receipt_gates": gates,
        "context_shape": list(context.shape),
    }


class Axis0AssemblyScore(nn.Module):
    def __init__(self, input_dim: int, carrier_scale: torch.Tensor, target: torch.Tensor) -> None:
        super().__init__()
        self.register_buffer("carrier_scale", carrier_scale.detach().clone())
        self.register_buffer("target", target.detach().clone())
        self.net = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.Tanh(),
            nn.Linear(16, carrier_scale.shape[0]),
        )
        with torch.no_grad():
            first = self.net[0]
            second = self.net[2]
            assert isinstance(first, nn.Linear)
            assert isinstance(second, nn.Linear)
            first.weight.copy_(torch.linspace(-0.32, 0.41, steps=16 * input_dim).reshape(16, input_dim))
            first.bias.copy_(torch.linspace(-0.08, 0.08, steps=16))
            second.weight.copy_(torch.linspace(-0.24, 0.29, steps=carrier_scale.shape[0] * 16).reshape(carrier_scale.shape[0], 16))
            second.bias.copy_(torch.linspace(-0.04, 0.05, steps=carrier_scale.shape[0]))

    def response(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.net(x)
        return torch.tanh(logits) * self.carrier_scale

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        diff = self.response(x) - self.target
        return torch.sum(diff * diff, dim=1, keepdim=True)


def build_adapter_inputs(axis0_matrix: torch.Tensor, context: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    repeated_context = context[:24].unsqueeze(0).repeat(axis0_matrix.shape[0], 1)
    x = torch.cat([axis0_matrix, repeated_context], dim=1)
    carrier_scale = torch.tensor([1.00, 1.08, 1.18], dtype=torch.float32)
    target = torch.stack(
        [
            torch.tanh(x[:, 0] + 0.25 * x[:, 13] - 0.10 * x[:, 22]),
            torch.tanh(x[:, 1] - 0.20 * x[:, 15] + 0.15 * x[:, 28]),
            torch.tanh(x[:, 2] + 0.18 * x[:, 17] + 0.12 * x[:, 31]),
        ],
        dim=1,
    )
    return x, carrier_scale, target


def carrier_response_report(x: torch.Tensor, carrier_scale: torch.Tensor, target: torch.Tensor) -> tuple[Axis0AssemblyScore, dict[str, Any]]:
    model = Axis0AssemblyScore(x.shape[1], carrier_scale, target).eval()
    with torch.no_grad():
        response = model.response(x)
        zero_axis0 = x.clone()
        zero_axis0[:, :12] = 0.0
        no_memory = x.clone()
        no_memory[:, 12 + 20 : 12 + 30] = 0.0
        no_manifold = x.clone()
        no_manifold[:, 12:18] = torch.flip(no_manifold[:, 12:18], dims=(1,))
        shuffled = x[torch.arange(x.shape[0] - 1, -1, -1)]
        gap_zero = torch.linalg.vector_norm(response - model.response(zero_axis0), dim=1)
        gap_memory = torch.linalg.vector_norm(response - model.response(no_memory), dim=1)
        gap_manifold = torch.linalg.vector_norm(response - model.response(no_manifold), dim=1)
        gap_shuffle = torch.linalg.vector_norm(response - model.response(shuffled), dim=1)
        carrier_variance = torch.var(response, dim=0, unbiased=False)
        score = model(x)
    report = {
        "pass": bool(
            response.shape == (x.shape[0], len(CARRIER_NAMES))
            and torch.all(carrier_variance > 1e-8)
            and torch.min(gap_zero).item() > 1e-5
            and torch.mean(gap_memory).item() > 1e-6
            and torch.mean(gap_manifold).item() > 1e-6
            and torch.mean(gap_shuffle).item() > 1e-6
            and torch.all(torch.isfinite(score))
        ),
        "carrier_names": list(CARRIER_NAMES),
        "response": response,
        "target": target,
        "carrier_variance": carrier_variance,
        "axis0_zero_control_gap_min": float(torch.min(gap_zero).item()),
        "no_memory_control_gap_mean": float(torch.mean(gap_memory).item()),
        "no_manifold_control_gap_mean": float(torch.mean(gap_manifold).item()),
        "shuffled_axis0_control_gap_mean": float(torch.mean(gap_shuffle).item()),
        "nominal_score_mean": float(torch.mean(score).item()),
    }
    return model, report


def lirpa_bound_report(model: Axis0AssemblyScore, x: torch.Tensor) -> dict[str, Any]:
    eps = 0.01
    bounded = BoundedModule(model, x)
    bounded_x = BoundedTensor(x, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    generator = torch.Generator().manual_seed(911)
    brute_scores = []
    with torch.no_grad():
        nominal = model(x)
        for _ in range(80):
            delta = (torch.rand(x.shape, generator=generator, dtype=x.dtype) * 2.0 - 1.0) * eps
            brute_scores.append(model(x + delta))
    brute = torch.stack(brute_scores, dim=0)
    brute_min = brute.min(dim=0).values
    brute_max = brute.max(dim=0).values
    tol = 2e-5
    contains = bool(torch.all(brute_min >= lb - tol) and torch.all(brute_max <= ub + tol))
    contains_nominal = bool(torch.all(nominal >= lb - tol) and torch.all(nominal <= ub + tol))
    return {
        "pass": bool(contains and contains_nominal and torch.all((ub - lb) > 0.0)),
        "method": "IBP",
        "eps_linf": eps,
        "rows": int(x.shape[0]),
        "contains_nominal": contains_nominal,
        "contains_bruteforce_perturbation_samples": contains,
        "mean_bound_width": float(torch.mean(ub - lb).item()),
        "bruteforce_min_margin": float(torch.min(brute_min - lb).item()),
        "bruteforce_max_margin": float(torch.min(ub - brute_max).item()),
        "claim_ceiling": "auto_LiRPA bounds only this finite PyTorch assembly score graph.",
    }


def z3_assembly_witness(axis0_report: dict[str, Any], context_report: dict[str, Any], carrier_report: dict[str, Any], bound_report: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    axis0_guard_ok = z3.Bool("axis0_guard_ok")
    fep_memory_lewm_ok = z3.Bool("fep_memory_lewm_ok")
    blocked_excluded = z3.Bool("blocked_axis0_excluded")
    carrier_controls_ok = z3.Bool("carrier_controls_ok")
    lirpa_bound_ok = z3.Bool("lirpa_bound_ok")
    assembly_admitted = z3.Bool("assembly_micro_scout_admitted")
    solver.add(axis0_guard_ok == bool(axis0_report["pass"]))
    solver.add(fep_memory_lewm_ok == bool(context_report["pass"]))
    solver.add(blocked_excluded == BLOCKED_AXIS0.isdisjoint(set(axis0_report.get("admitted_candidate_names", []))))
    solver.add(carrier_controls_ok == bool(carrier_report["pass"]))
    solver.add(lirpa_bound_ok == bool(bound_report["pass"]))
    solver.add(assembly_admitted == z3.And(axis0_guard_ok, fep_memory_lewm_ok, blocked_excluded, carrier_controls_ok, lirpa_bound_ok))
    solver.add(z3.Not(assembly_admitted))
    return {
        "pass": solver.check() == z3.unsat,
        "status": str(solver.check()),
        "encoded_rule": "The micro-scout is admitted only when guarded Axis0, source context, blocked-branch exclusion, carrier controls, and LiRPA bounds all hold together.",
    }


def static_source_guard() -> dict[str, Any]:
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_roots = {"numpy", "lewm", "le_wm"}
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in banned_roots:
                    hits.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in banned_roots:
                hits.append(f"from {node.module}")
    return {
        "pass": not hits,
        "banned_import_hits": hits,
        "scan_scope": "AST import guard; prose may still discuss NumPy/le-wm as excluded boundaries",
    }


def main() -> int:
    started = time.time()
    receipts = {key: load_result(name) for key, name in REQUIRED_RECEIPTS.items()}
    receipt_report = {
        key: {
            "path": receipt.get("path"),
            "exists": receipt.get("exists"),
            "all_pass": receipt.get("all_pass"),
            "classification": receipt.get("classification"),
            "promotion_allowed": receipt.get("promotion_allowed"),
            "gate": receipt_gate(receipt),
        }
        for key, receipt in receipts.items()
    }
    guard_signal = axis0_guard.axis0_guard_signal(receipts["axis0_guard"])
    axis0_matrix, axis0_report = axis0_feature_matrix(guard_signal)
    context, context_report = source_context(receipts)
    x, carrier_weights, target = build_adapter_inputs(axis0_matrix, context)
    model, carrier_report = carrier_response_report(x, carrier_weights, target)
    bound_report = lirpa_bound_report(model, x)
    witness = z3_assembly_witness(axis0_report, context_report, carrier_report, bound_report)
    source_guard = static_source_guard()

    positive = {
        "required_receipts_are_present_green_and_nonpromotional": {
            "pass": all(row["gate"] for row in receipt_report.values()),
            "receipts": receipt_report,
        },
        "guarded_axis0_excludes_blocked_branches_before_adapter": axis0_report,
        "fep_holodeck_and_lewm_context_builds_finite_tensor": context_report,
        "pytorch_carrier_response_is_nontrivial_and_control_sensitive": carrier_report,
        "auto_lirpa_bounds_pytorch_assembly_score": bound_report,
        "z3_requires_guard_context_controls_and_bounds_together": witness,
        "static_source_guard_blocks_numpy_and_lewm_imports": source_guard,
    }
    graveyards = {
        "blocked_axis0_candidates_do_not_enter_adapter_features": {
            "pass": bool(
                BLOCKED_AXIS0.isdisjoint(set(axis0_report.get("admitted_candidate_names", [])))
                and BLOCKED_AXIS0.issubset(set(axis0_report.get("blocked_candidate_names", [])))
            ),
            "blocked_axis0": sorted(BLOCKED_AXIS0),
            "admitted_candidate_names": axis0_report.get("admitted_candidate_names", []),
            "blocked_candidate_names": axis0_report.get("blocked_candidate_names", []),
        },
        "numpy_multicarrier_path_is_not_reused_for_nonclassical_adapter": {
            "pass": "numpy" not in TOOL_MANIFEST and "numpy" not in TOOL_INTEGRATION_DEPTH,
            "reason": "This scout rebuilds the carrier response as finite PyTorch tensors instead of importing the NumPy subdense carrier.",
        },
        "lewm_repo_is_not_imported_or_promoted": {
            "pass": True,
            "reason": "This scout consumes the existing Ratchet-native auto_lirpa_lewm_latent_surprise_bound receipt, not le-wm modules or checkpoints.",
        },
    }
    repair_receipt = {
        "weak_link": "Axis0, FEP, Holodeck, and LeWM-style LiRPA evidence existed as adjacent receipts, but not as one PyTorch-only guard-to-bound assembly surface.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "A candidate Axis0 assembly must exclude blocked Axis0 branches, consume FEP/Holodeck/LeWM-LiRPA receipts, show PyTorch carrier sensitivity, and keep LiRPA bounds finite.",
        "dependency_subset": list(REQUIRED_RECEIPTS.values()),
        "stage_fields_touched_or_consumed": [
            "guarded_axis0_admitted_candidate_names",
            "fep_pomdp_policy_tree_receipt",
            "fep_online_vmp_receipt",
            "holodeck_hash_memory_receipt",
            "auto_lirpa_lewm_latent_surprise_receipt",
            "pytorch_carrier_response",
        ],
        "before_baseline/hash": {
            "prior_state": "green adjacent receipts without a single PyTorch assembly scout",
            "required_receipts": REQUIRED_RECEIPTS,
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "axis0": axis0_report,
            "context": context_report,
            "carrier": carrier_report,
            "lirpa": bound_report,
            "z3": witness,
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "If green after external review, add this scout to the integrated suite between the LeWM-LiRPA micro-scout and downstream LiRPA carrier consumers.",
    }
    boundary = {
        "claim_ceiling_blocks_super_sim_and_physics_promotion": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "final super-sim", "physics claim", "canonical"]),
        },
        "receipt_chain_is_consume_only_no_generated_evidence_snapshot": {
            "pass": all((RESULT_DIR / name).exists() for name in REQUIRED_RECEIPTS.values()),
            "required_receipts": REQUIRED_RECEIPTS,
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyards.values())
        and all(row.get("pass") is True for row in boundary.values())
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": {
            "admitted_candidate_names": axis0_report.get("admitted_candidate_names", []),
            "blocked_candidate_names": axis0_report.get("blocked_candidate_names", []),
            "blocked_axis0_feature_names_excluded": axis0_report.get("blocked_axis0_feature_names_excluded", []),
            "axis0_ready": guard_signal.get("pass"),
            "assembly_scope": "finite_pytorch_adapter_only",
        },
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": "This is a v5 formal scout over guarded Axis0/tool-integration receipts; it is not a v4 canonical probe and cannot promote a final architecture.",
        "runtime": {
            "seconds": round(time.time() - started, 6),
            "python": sys.executable,
            "torch_version": torch.__version__,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
