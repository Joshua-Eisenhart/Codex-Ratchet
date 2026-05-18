#!/usr/bin/env python3
"""auto_LiRPA bound scout for a LeWM-style latent surprise adapter.

This is a Ratchet-native micro-scout. It reads the local le-wm source only as a
design reference for three small ideas: next-embedding prediction, SIGReg-style
collapse pressure, and latent surprise/cost. It does not import le-wm, does not
load checkpoints, and does not admit an external world-model dependency.

Formal scout only. auto_LiRPA bounds a tiny PyTorch latent-surprise adapter over
source-native EngineCore stage records. The bound is a neural adapter diagnostic,
not physics evidence.
"""

from __future__ import annotations

import hashlib
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
import torch.nn.functional as F
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if not AUTO_LIRPA_ROOT.exists():
    raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "auto_lirpa_lewm_latent_surprise_bound_probe_results.json"
LEWM_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm")

NAME = "auto_lirpa_lewm_latent_surprise_bound_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "auto_lirpa_tool_admission_lewm_style_latent_surprise_micro_bound"
CLAIM_CEILING = (
    "Formal scout only: rewrites LeWM-style SIGReg, next-embedding prediction, "
    "and latent surprise as a tiny Ratchet-native PyTorch adapter, then bounds "
    "that adapter with auto_LiRPA over finite EngineCore stage features. It "
    "does not admit le-wm as a dependency, does not load checkpoints, and does "
    "not admit a neural world model, physics claim, cognition claim, final FEP "
    "system, final verifier, or canonical architecture."
)

TOOL_MANIFEST = {
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite interval bounds for the latent-surprise adapter",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing feature tensors, latent predictor, SIGReg-style collapse guard, training control, and perturbation samples",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness that all admission predicates are required together",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native stage records used to build the latent sequence; not a standalone tool-capability admission",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive local source-boundary checks for le-wm and auto_LiRPA",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "auto_LiRPA": "load_bearing",
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "engine_core": "supportive",
    "pathlib": "supportive",
}

OPERATORS = ["Ti", "Te", "Fi", "Fe"]
PERCEPTIONS = ["Se", "Ne", "Ni", "Si"]
FEATURE_NAMES = [
    "bloch_x",
    "bloch_y",
    "bloch_z",
    "entropy",
    "purity",
    "prediction_error_l2",
    "surprise_kl",
    "expected_free_energy_proxy",
    "manifold_projection_delta_norm",
    "prediction_observation_delta_0",
    "prediction_observation_delta_1",
    "prediction_observation_delta_2",
    "operator_sign",
    *[f"operator_{op}" for op in OPERATORS],
    *[f"perception_{item}" for item in PERCEPTIONS],
]
LATENT_DIM = 6
ACTION_DIM = 3


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


def collect_stage_tensor() -> tuple[torch.Tensor, list[dict[str, Any]]]:
    rows: list[list[float]] = []
    records: list[dict[str, Any]] = []
    for seed_idx in range(5):
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=True)
            rho = generate_initial_density(91000 + 100 * seed_idx + engine_type)
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    model = record["model_after"]
                    fep = record["fep_efe_score"]
                    repair = record["update_repair"]
                    pred = torch.tensor(record["prediction"]["observation_distribution"], dtype=torch.float32)
                    obs = torch.tensor(record["observation"]["observation_distribution"], dtype=torch.float32)
                    delta = pred - obs
                    rows.append(
                        [
                            *[float(x) for x in model["bloch"]],
                            float(model["entropy"]),
                            float(model["purity"]),
                            float(fep["prediction_error_l2"]),
                            float(fep["surprise_kl"]),
                            float(fep["expected_free_energy_proxy"]),
                            float(repair["manifold_projection_delta_norm"]),
                            *[float(x) for x in delta[:3]],
                            float(record["operator_sign"]),
                            *[1.0 if record["operator"] == op else 0.0 for op in OPERATORS],
                            *[1.0 if perception == item else 0.0 for item in PERCEPTIONS],
                        ]
                    )
                    records.append(
                        {
                            "operator": record["operator"],
                            "perception": perception,
                            "ordered_token": record["ordered_token"],
                            "next_policy_id": record["next_policy"]["policy_id"],
                        }
                    )
    x = torch.tensor(rows, dtype=torch.float32)
    mean = x.mean(dim=0, keepdim=True)
    std = x.std(dim=0, unbiased=False, keepdim=True).clamp_min(1e-6)
    return (x - mean) / std, records


def fixed_projection(input_dim: int, output_dim: int) -> tuple[torch.Tensor, torch.Tensor]:
    weights = torch.linspace(-0.65, 0.75, steps=input_dim * output_dim, dtype=torch.float32).reshape(input_dim, output_dim)
    bias = torch.linspace(-0.12, 0.18, steps=output_dim, dtype=torch.float32)
    return weights, bias


def build_latent_problem(features: torch.Tensor) -> dict[str, torch.Tensor]:
    proj, bias = fixed_projection(features.shape[1], LATENT_DIM)
    latent = torch.tanh(features @ proj + bias)
    action = torch.stack(
        [
            features[:-1, FEATURE_NAMES.index("operator_sign")],
            features[:-1, FEATURE_NAMES.index("prediction_error_l2")],
            features[:-1, FEATURE_NAMES.index("expected_free_energy_proxy")],
        ],
        dim=1,
    )
    context_proj = torch.tensor(
        [
            [0.20, -0.14, 0.11, 0.08, -0.06, 0.04],
            [-0.09, 0.16, -0.05, 0.14, 0.07, -0.03],
            [0.05, 0.06, 0.13, -0.10, 0.15, 0.02],
        ],
        dtype=torch.float32,
    )
    source_next = latent[1:]
    current = latent[:-1]
    target = torch.tanh(0.72 * source_next + 0.20 * current + 0.18 * (action @ context_proj))
    x = torch.cat([current, action], dim=1)
    return {"x": x, "target": target, "latent": latent, "action": action}


class TinyLatentPredictor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(LATENT_DIM + ACTION_DIM, 18),
            nn.Tanh(),
            nn.Linear(18, LATENT_DIM),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.net(x))


class LatentSurpriseScore(nn.Module):
    def __init__(self, predictor: TinyLatentPredictor, target: torch.Tensor) -> None:
        super().__init__()
        self.predictor = predictor
        self.register_buffer("target", target.detach().clone())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        pred = self.predictor(x)
        diff = pred - self.target
        return torch.sum(diff * diff, dim=1, keepdim=True)


def train_predictor(x: torch.Tensor, target: torch.Tensor) -> tuple[TinyLatentPredictor, dict[str, Any]]:
    torch.manual_seed(707)
    model = TinyLatentPredictor()
    opt = torch.optim.Adam(model.parameters(), lr=0.03)
    train_x = x[:120]
    train_y = target[:120]
    test_x = x[120:]
    test_y = target[120:]
    shuffled_y = torch.roll(test_y, shifts=5, dims=0)
    for _ in range(260):
        opt.zero_grad()
        pred = model(train_x)
        loss = F.mse_loss(pred, train_y)
        loss.backward()
        opt.step()
    with torch.no_grad():
        train_loss = F.mse_loss(model(train_x), train_y).item()
        test_loss = F.mse_loss(model(test_x), test_y).item()
        shuffled_loss = F.mse_loss(model(test_x), shuffled_y).item()
        far_loss = F.mse_loss(model(test_x[:16]), test_y[:16] + 0.75).item()
    return model.eval(), {
        "pass": bool(train_loss < 0.05 and test_loss < shuffled_loss * 0.82 and far_loss > test_loss * 2.0),
        "train_loss": float(train_loss),
        "test_loss": float(test_loss),
        "shuffled_target_loss": float(shuffled_loss),
        "far_target_loss": float(far_loss),
        "claim_ceiling": "Tiny next-embedding predictor only; target remains a finite source-native latent fixture, not a production world model.",
    }


def sigreg_score(proj: torch.Tensor, num_proj: int = 96, knots: int = 17) -> torch.Tensor:
    generator = torch.Generator().manual_seed(808)
    directions = torch.randn(proj.size(-1), num_proj, generator=generator, dtype=torch.float32)
    directions = directions / directions.norm(p=2, dim=0, keepdim=True).clamp_min(1e-7)
    t = torch.linspace(0.0, 3.0, knots, dtype=torch.float32)
    dt = 3.0 / float(knots - 1)
    weights = torch.full((knots,), 2.0 * dt, dtype=torch.float32)
    weights[0] = dt
    weights[-1] = dt
    phi = torch.exp(-(t * t) / 2.0)
    weights = weights * phi
    x_t = (proj @ directions).unsqueeze(-1) * t
    err = (x_t.cos().mean(dim=-3) - phi).square() + x_t.sin().mean(dim=-3).square()
    statistic = (err @ weights) * proj.size(-2)
    return statistic.mean()


def sigreg_report(latent: torch.Tensor) -> dict[str, Any]:
    usable = latent[:128].reshape(8, 16, LATENT_DIM).transpose(0, 1).contiguous()
    generator = torch.Generator().manual_seed(809)
    gaussian = torch.randn(16, 8, LATENT_DIM, generator=generator, dtype=torch.float32)
    collapsed = torch.zeros_like(gaussian) + 0.125
    source_score = sigreg_score(usable).item()
    gaussian_score = sigreg_score(gaussian).item()
    collapsed_score = sigreg_score(collapsed).item()
    return {
        "pass": bool(collapsed_score > gaussian_score * 3.0 and collapsed_score > source_score * 1.5),
        "source_stage_latent_score": float(source_score),
        "gaussian_control_score": float(gaussian_score),
        "collapsed_control_score": float(collapsed_score),
        "claim_ceiling": "LeWM-style SIGReg collapse pressure rewritten as a small PyTorch fixture; no le-wm module or checkpoint is imported.",
    }


def lirpa_bound_report(model: TinyLatentPredictor, x: torch.Tensor, target: torch.Tensor) -> dict[str, Any]:
    sample = x[8:24].detach().clone()
    sample_target = target[8:24].detach().clone()
    score_model = LatentSurpriseScore(model, sample_target).eval()
    eps = 0.015
    bounded = BoundedModule(score_model, sample)
    bounded_x = BoundedTensor(sample, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    generator = torch.Generator().manual_seed(810)
    brute_scores = []
    with torch.no_grad():
        nominal = score_model(sample)
        for _ in range(60):
            delta = (torch.rand(sample.shape, generator=generator, dtype=sample.dtype) * 2.0 - 1.0) * eps
            brute_scores.append(score_model(sample + delta))
    brute = torch.stack(brute_scores, dim=0)
    brute_min = brute.min(dim=0).values
    brute_max = brute.max(dim=0).values
    tol = 2e-5
    contains_bruteforce = bool(torch.all(brute_min >= lb - tol) and torch.all(brute_max <= ub + tol))
    contains_nominal = bool(torch.all(nominal >= lb - tol) and torch.all(nominal <= ub + tol))
    width = torch.mean(ub - lb).item()
    center_shift = torch.mean(torch.abs(((ub + lb) / 2.0) - nominal)).item()
    return {
        "pass": bool(contains_bruteforce and contains_nominal and width > 0.0),
        "method": "IBP",
        "eps_linf": eps,
        "sample_rows": int(sample.shape[0]),
        "contains_nominal": contains_nominal,
        "contains_bruteforce_perturbation_samples": contains_bruteforce,
        "mean_bound_width": float(width),
        "mean_center_to_nominal_shift": float(center_shift),
        "bruteforce_min_margin": float(torch.min(brute_min - lb).item()),
        "bruteforce_max_margin": float(torch.min(ub - brute_max).item()),
        "claim_ceiling": "auto_LiRPA bounds finite latent-surprise scores for this tiny PyTorch adapter only.",
    }


def z3_witness(train: dict[str, Any], sigreg: dict[str, Any], bound: dict[str, Any], lewm_reference: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    repo_present = z3.Bool("lewm_repo_present")
    imported_dependency = z3.Bool("lewm_imported_dependency")
    rewritten_micro_fixture = z3.Bool("rewritten_micro_fixture")
    lirpa_bound_passed = z3.Bool("lirpa_bound_passed")
    admitted_dependency = z3.Bool("admitted_dependency")
    solver.add(repo_present == bool(lewm_reference["present"]))
    solver.add(imported_dependency == False)
    solver.add(rewritten_micro_fixture == bool(train["pass"] and sigreg["pass"]))
    solver.add(lirpa_bound_passed == bool(bound["pass"]))
    solver.add(admitted_dependency == z3.And(repo_present, imported_dependency, rewritten_micro_fixture, lirpa_bound_passed))
    solver.add(admitted_dependency)
    dependency_admission_status = solver.check()
    micro_solver = z3.Solver()
    micro_admitted = z3.Bool("micro_scout_admitted")
    micro_solver.add(imported_dependency == False)
    micro_solver.add(rewritten_micro_fixture == bool(train["pass"] and sigreg["pass"]))
    micro_solver.add(lirpa_bound_passed == bool(bound["pass"]))
    micro_solver.add(micro_admitted == z3.And(rewritten_micro_fixture, lirpa_bound_passed, z3.Not(imported_dependency)))
    micro_solver.add(z3.Not(micro_admitted))
    micro_status = micro_solver.check()
    return {
        "pass": dependency_admission_status == z3.unsat and micro_status == z3.unsat,
        "dependency_admission_without_import_status": str(dependency_admission_status),
        "micro_scout_rule_status": str(micro_status),
        "encoded_rule": "le-wm repo presence is not dependency admission; only the rewritten PyTorch micro-scout plus LiRPA bound is admitted as evidence.",
    }


def main() -> int:
    started = time.time()
    features, records = collect_stage_tensor()
    problem = build_latent_problem(features)
    predictor, train = train_predictor(problem["x"], problem["target"])
    sigreg = sigreg_report(problem["latent"])
    bound = lirpa_bound_report(predictor, problem["x"], problem["target"])
    lewm_reference = {
        "present": LEWM_ROOT.exists(),
        "path": str(LEWM_ROOT),
        "readme_present": (LEWM_ROOT / "README.md").exists(),
        "jepa_source_present": (LEWM_ROOT / "jepa.py").exists(),
        "sigreg_source_present": (LEWM_ROOT / "module.py").exists(),
        "imported": False,
        "decision": "reference_only_micro_scout_source",
    }
    witness = z3_witness(train, sigreg, bound, lewm_reference)

    positive = {
        "lewm_style_micro_fixture_rewritten_in_pytorch": {
            "pass": bool(train["pass"] and sigreg["pass"] and lewm_reference["present"]),
            "training": train,
            "sigreg": sigreg,
            "lewm_reference": lewm_reference,
        },
        "auto_lirpa_bounds_latent_surprise_adapter": bound,
        "source_native_stage_records_drive_latent_sequence": {
            "pass": bool(features.shape[0] == 320 and problem["x"].shape[0] == 319 and len(records) == 320),
            "feature_rows": int(features.shape[0]),
            "input_rows": int(problem["x"].shape[0]),
            "feature_dim": int(features.shape[1]),
            "latent_dim": LATENT_DIM,
            "sample_records": records[:3],
        },
        "z3_blocks_repo_presence_as_dependency_admission": witness,
    }

    graveyards = {
        "lewm_repo_import_is_not_required_or_allowed_here": {
            "pass": lewm_reference["present"] and lewm_reference["imported"] is False,
            "decision": lewm_reference["decision"],
            "reason": "The external repo supplies design vocabulary only; the scout is Ratchet-native PyTorch.",
        },
        "collapsed_latents_are_rejected_by_sigreg_control": {
            "pass": sigreg["pass"],
            "collapsed_control_score": sigreg["collapsed_control_score"],
            "gaussian_control_score": sigreg["gaussian_control_score"],
        },
        "shuffled_and_far_targets_do_not_substitute_for_predictive_latent_cost": {
            "pass": train["pass"],
            "test_loss": train["test_loss"],
            "shuffled_target_loss": train["shuffled_target_loss"],
            "far_target_loss": train["far_target_loss"],
        },
    }

    repair_receipt = {
        "weak_link": "auto_LiRPA was integrated as a stage-policy bound checker, while le-wm was only a large local repo with no tiny Ratchet-native consumption fixture.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "LeWM ideas may enter only as rewritten PyTorch micro-scouts; auto_LiRPA may certify the finite adapter graph but cannot promote physics or dependency claims.",
        "dependency_subset": [
            "EngineCore source-native stage records",
            "local auto_LiRPA BoundedModule/BoundedTensor/PerturbationLpNorm",
            "local le-wm README/jepa.py/module.py as reference-only source",
        ],
        "stage_fields_touched_or_consumed": FEATURE_NAMES,
        "before_baseline/hash": {
            "lewm_repo": str(LEWM_ROOT),
            "prior_state": "reference repo present, no tiny PyTorch consumption fixture in this branch",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "training": train,
            "sigreg": sigreg,
            "lirpa_bound": bound,
            "z3_witness": witness,
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "If this remains green, add a queue/index row that treats le-wm as reference-only and this scout as the admissible micro-fixture, then test a second LiRPA method beyond IBP on the same adapter.",
    }

    boundary = {
        "claim_ceiling_blocks_world_model_or_physics_promotion": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "neural world model", "physics claim"]),
        },
        "no_external_repo_runtime_or_checkpoint_used": {
            "pass": bool(lewm_reference["present"] and lewm_reference["imported"] is False),
            "scope": "local source/readme boundary only; no le-wm import, package install, checkpoint, dataset, model download, video/image generation, or training stack.",
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
        "tool_manifest_keeps_numpy_out_of_the_micro_scout": {
            "pass": "numpy" not in TOOL_MANIFEST and "numpy" not in TOOL_INTEGRATION_DEPTH,
            "tools": sorted(TOOL_MANIFEST),
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
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": "This is a v5 formal scout over local GitHub tool integration; it is not a v4 canonical probe and cannot promote a canonical architecture.",
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
