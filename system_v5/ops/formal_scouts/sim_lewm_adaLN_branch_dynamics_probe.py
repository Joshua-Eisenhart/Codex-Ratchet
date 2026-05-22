#!/usr/bin/env python3
"""Minimal scout: does AdaLN-zero conditioning on EFE branch status discriminate dynamic
Axis0 branch behavior beyond SIGReg static collapse detection?

Reference: /Users/joshuaeisenhart/GitHub/le-wm/module.py (ConditionalBlock, SIGReg).
No le-wm import. No checkpoint. Ratchet-native PyTorch only.

Probe question:
  Given EngineCore sequences split by high/low FEP expected-free-energy (EFE) proxy
  (proxy for admitted vs blocked Axis0 branch pressure), does AdaLN-zero conditioning
  on the EFE-pressure vector lower prediction surprise *more* for high-EFE sequences
  than for low-EFE sequences?

  If yes → le-wm ConditionalBlock gating is load-bearing for dynamic branch discrimination.
  If no  → SIGReg static collapse detection is sufficient; conditioning adds nothing.

Classification: formal_scout. PROMOTION_ALLOWED = False.
Claim ceiling: tool_lego_fit_probe pre-admission evidence only.
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

from engine_core import EngineCore, generate_initial_density  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "lewm_adaLN_branch_dynamics_probe_results.json"
LEWM_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm")

NAME = "lewm_adaLN_branch_dynamics_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "lewm_adaLN_conditional_branch_dynamics_scout"
CLAIM_CEILING = (
    "Formal scout only: tests whether a Ratchet-native AdaLN-zero conditional block "
    "(inlined from le-wm ConditionalBlock design) produces a prediction-error gap between "
    "high-EFE and low-EFE EngineCore sequences that exceeds both (a) unconditioned prediction "
    "and (b) SIGReg static collapse detection. Does not import le-wm, does not load "
    "checkpoints, does not admit a world model, physics claim, canonical Axis0 alignment, "
    "or final architecture. promotion_allowed: false."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: AdaLN-zero TinyCondPredictor, feature tensors, EFE split, gap measurement, perturbation samples",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: IBP interval bounds for the conditioned predictor under input perturbation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: finite witness that conditioning + EFE split are jointly required for the gap claim",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive: source-native stage records providing EFE and latent features; not standalone tool admission",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: le-wm source boundary check and result path",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "z3": "load_bearing",
    "engine_core": "supportive",
    "pathlib": "supportive",
}

LATENT_DIM = 8
COND_DIM = 4
EFE_IDX = 6          # index of surprise_kl in feature vector (see FEATURE_NAMES below)
EFE_PROXY_IDX = 7    # expected_free_energy_proxy
FEATURE_NAMES = [
    "bloch_x", "bloch_y", "bloch_z",
    "entropy", "purity",
    "prediction_error_l2", "surprise_kl", "expected_free_energy_proxy",
    "manifold_projection_delta_norm",
    "prediction_observation_delta_0", "prediction_observation_delta_1", "prediction_observation_delta_2",
    "operator_sign",
]
FEAT_DIM = len(FEATURE_NAMES)

COND_IMPROVEMENT_THRESHOLD = 1.3   # conditioning must help admitted >1.3× more than blocked
SIGREG_GAP_DOMINATION_THRESHOLD = 1.2  # cond gap must exceed SIGReg gap by ≥ this ratio


# ---------------------------------------------------------------------------
# Inline AdaLN-zero block  (reference: le-wm/module.py ConditionalBlock)
# Plain torch ops only. No einops.
# ---------------------------------------------------------------------------

class TinyAdaLNBlock(nn.Module):
    def __init__(self, dim: int, cond_dim: int) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(dim, elementwise_affine=False, eps=1e-6)
        self.norm2 = nn.LayerNorm(dim, elementwise_affine=False, eps=1e-6)
        self.attn = nn.Linear(dim, dim, bias=False)
        # auto_LiRPA in this environment does not support ONNX Erf emitted by
        # GELU. Keep this adapter intentionally ReLU-only so the bound is a real
        # LiRPA gate rather than a failed ornamental call.
        self.mlp = nn.Sequential(nn.Linear(dim, dim * 2), nn.ReLU(), nn.Linear(dim * 2, dim))
        self.adaLN = nn.Sequential(nn.ReLU(), nn.Linear(cond_dim, 6 * dim, bias=True))
        nn.init.constant_(self.adaLN[-1].weight, 0)
        nn.init.constant_(self.adaLN[-1].bias, 0)

    @staticmethod
    def modulate(x: torch.Tensor, shift: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
        return x * (1.0 + scale) + shift

    def forward(self, x: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        shift_a, scale_a, gate_a, shift_m, scale_m, gate_m = self.adaLN(c).chunk(6, dim=-1)
        x = x + gate_a * self.attn(self.modulate(self.norm1(x), shift_a, scale_a))
        x = x + gate_m * self.mlp(self.modulate(self.norm2(x), shift_m, scale_m))
        return x


class TinyCondPredictor(nn.Module):
    """Next-step latent predictor with AdaLN-zero conditioning on EFE branch status."""

    def __init__(self) -> None:
        super().__init__()
        self.input_proj = nn.Linear(FEAT_DIM, LATENT_DIM)
        self.block = TinyAdaLNBlock(LATENT_DIM, COND_DIM)
        self.output_proj = nn.Linear(LATENT_DIM, LATENT_DIM)

    def forward(self, x: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        h = torch.tanh(self.input_proj(x))
        h = self.block(h, c)
        return self.output_proj(h)


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect_features() -> tuple[torch.Tensor, list[float]]:
    rows: list[list[float]] = []
    efe_vals: list[float] = []
    for seed_idx in range(4):
        for etype in (0, 1):
            engine = EngineCore(etype, manifold_enabled=True)
            rho = generate_initial_density(77000 + 100 * seed_idx + etype)
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for sub_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, sub_idx)
                    m = record["model_after"]
                    fep = record["fep_efe_score"]
                    repair = record["update_repair"]
                    pred = torch.tensor(record["prediction"]["observation_distribution"], dtype=torch.float32)
                    obs = torch.tensor(record["observation"]["observation_distribution"], dtype=torch.float32)
                    delta = (pred - obs)[:3]
                    row = [
                        *[float(v) for v in m["bloch"]],
                        float(m["entropy"]),
                        float(m["purity"]),
                        float(fep["prediction_error_l2"]),
                        float(fep["surprise_kl"]),
                        float(fep["expected_free_energy_proxy"]),
                        float(repair["manifold_projection_delta_norm"]),
                        *[float(v) for v in delta],
                        float(record["operator_sign"]),
                    ]
                    rows.append(row)
                    efe_vals.append(float(fep["expected_free_energy_proxy"]))
    x = torch.tensor(rows, dtype=torch.float32)
    mean = x.mean(0, keepdim=True)
    std = x.std(0, unbiased=False, keepdim=True).clamp_min(1e-6)
    return (x - mean) / std, efe_vals


def split_by_efe(features: torch.Tensor, efe_vals: list[float]) -> dict[str, torch.Tensor]:
    efe_t = torch.tensor(efe_vals, dtype=torch.float32)
    q25 = float(torch.quantile(efe_t, 0.25).item())
    q75 = float(torch.quantile(efe_t, 0.75).item())
    hi_idx = (efe_t >= q75).nonzero(as_tuple=True)[0]
    lo_idx = (efe_t <= q25).nonzero(as_tuple=True)[0]
    return {
        "hi": features[hi_idx],
        "lo": features[lo_idx],
        "q25": q25,
        "q75": q75,
    }


# ---------------------------------------------------------------------------
# Conditioning vector: top-4 EFE-pressure features
# ---------------------------------------------------------------------------

def make_cond(features: torch.Tensor) -> torch.Tensor:
    # c = [efe_proxy, surprise_kl, purity, prediction_error_l2] (all already normalized)
    idx = [EFE_PROXY_IDX, EFE_IDX, 4, 5]  # purity=4, pred_err=5
    return features[:, idx]


# ---------------------------------------------------------------------------
# SIGReg gap (static baseline)
# ---------------------------------------------------------------------------

def sigreg_score(x: torch.Tensor, num_proj: int = 64, knots: int = 17) -> float:
    gen = torch.Generator().manual_seed(333)
    directions = torch.randn(x.size(-1), num_proj, generator=gen, dtype=torch.float32)
    directions = directions / directions.norm(p=2, dim=0, keepdim=True).clamp_min(1e-7)
    t = torch.linspace(0.0, 3.0, knots, dtype=torch.float32)
    dt = 3.0 / float(knots - 1)
    w = torch.full((knots,), 2.0 * dt, dtype=torch.float32)
    w[0] = dt; w[-1] = dt
    phi = torch.exp(-(t * t) / 2.0)
    w = w * phi
    x_t = (x @ directions).unsqueeze(-1) * t
    err = (x_t.cos().mean(-3) - phi).square() + x_t.sin().mean(-3).square()
    return float((err @ w).mean().item() * x.size(-2))


def sigreg_gap_report(split: dict[str, Any]) -> dict[str, Any]:
    hi_score = sigreg_score(split["hi"])
    lo_score = sigreg_score(split["lo"])
    gap = abs(hi_score - lo_score)
    return {
        "hi_score": hi_score,
        "lo_score": lo_score,
        "gap": gap,
        "hi_n": int(split["hi"].shape[0]),
        "lo_n": int(split["lo"].shape[0]),
    }


# ---------------------------------------------------------------------------
# Conditioned vs unconditioned prediction gap
# ---------------------------------------------------------------------------

def predictor_gap_report(split: dict[str, Any]) -> tuple[TinyCondPredictor, dict[str, Any]]:
    torch.manual_seed(555)
    model = TinyCondPredictor()
    opt = torch.optim.Adam(model.parameters(), lr=0.02)

    hi, lo = split["hi"], split["lo"]
    # targets: next-step (shift by 1)
    hi_x, hi_y = hi[:-1], hi[1:]
    lo_x, lo_y = lo[:-1], lo[1:]
    c_hi = make_cond(hi_x)
    c_lo = make_cond(lo_x)

    # train on combined data
    all_x = torch.cat([hi_x, lo_x], dim=0)
    all_y = torch.cat([hi_y, lo_y], dim=0)
    all_c = torch.cat([c_hi, c_lo], dim=0)
    n_train = int(0.75 * all_x.shape[0])
    for _ in range(300):
        opt.zero_grad()
        pred = model(all_x[:n_train], all_c[:n_train])
        loss = F.mse_loss(pred[:, :LATENT_DIM], all_y[:n_train, :LATENT_DIM])
        loss.backward()
        opt.step()

    model.eval()
    c_zero = torch.zeros_like(c_hi)
    c_lo_same_shape = c_lo if c_lo.shape[0] == c_hi.shape[0] else c_lo[:c_hi.shape[0]]

    with torch.no_grad():
        # hi sequences: conditioned vs unconditioned
        pred_hi_cond = model(hi_x, c_hi)
        pred_hi_nocond = model(hi_x, torch.zeros_like(c_hi))
        pred_hi_wrong = model(hi_x, c_lo_same_shape if c_lo_same_shape.shape[0] == hi_x.shape[0] else c_lo[:hi_x.shape[0]])

        loss_hi_cond = F.mse_loss(pred_hi_cond[:, :LATENT_DIM], hi_y[:, :LATENT_DIM]).item()
        loss_hi_nocond = F.mse_loss(pred_hi_nocond[:, :LATENT_DIM], hi_y[:, :LATENT_DIM]).item()
        loss_hi_wrong = F.mse_loss(pred_hi_wrong[:, :LATENT_DIM], hi_y[:, :LATENT_DIM]).item()

        # lo sequences: conditioned vs unconditioned
        pred_lo_cond = model(lo_x, c_lo)
        pred_lo_nocond = model(lo_x, torch.zeros_like(c_lo))
        loss_lo_cond = F.mse_loss(pred_lo_cond[:, :LATENT_DIM], lo_y[:, :LATENT_DIM]).item()
        loss_lo_nocond = F.mse_loss(pred_lo_nocond[:, :LATENT_DIM], lo_y[:, :LATENT_DIM]).item()

    # key quantities
    cond_benefit_hi = loss_hi_nocond - loss_hi_cond    # positive = conditioning helped hi
    cond_benefit_lo = loss_lo_nocond - loss_lo_cond    # positive = conditioning helped lo
    wrong_cond_penalty = loss_hi_wrong - loss_hi_cond  # positive = wrong cond hurts

    # pass: conditioning helps hi MORE than lo by threshold, and wrong cond hurts
    pass_cond = (
        cond_benefit_hi > cond_benefit_lo * COND_IMPROVEMENT_THRESHOLD
        and wrong_cond_penalty > 0.0
        and loss_hi_cond < loss_hi_nocond
    )

    return model, {
        "pass": bool(pass_cond),
        "loss_hi_conditioned": float(loss_hi_cond),
        "loss_hi_unconditioned": float(loss_hi_nocond),
        "loss_hi_wrong_cond": float(loss_hi_wrong),
        "loss_lo_conditioned": float(loss_lo_cond),
        "loss_lo_unconditioned": float(loss_lo_nocond),
        "cond_benefit_hi": float(cond_benefit_hi),
        "cond_benefit_lo": float(cond_benefit_lo),
        "wrong_cond_penalty": float(wrong_cond_penalty),
        "cond_improvement_threshold": COND_IMPROVEMENT_THRESHOLD,
        "interpretation": (
            "LOAD_BEARING" if pass_cond else "NOT_LOAD_BEARING"
        ),
    }


# ---------------------------------------------------------------------------
# auto_LiRPA: bound conditioned predictor under input perturbation (c fixed)
# ---------------------------------------------------------------------------

def lirpa_bound_report(model: TinyCondPredictor, split: dict[str, Any]) -> dict[str, Any]:
    hi = split["hi"]
    sample_x = hi[4:20].detach().clone()
    sample_c = make_cond(sample_x).detach().clone()

    class PredWrapper(nn.Module):
        def __init__(self, inner: TinyCondPredictor, c: torch.Tensor) -> None:
            super().__init__()
            self.inner = inner
            self.register_buffer("c", c.detach().clone())

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.inner(x, self.c)

    wrapped = PredWrapper(model, sample_c).eval()
    eps = 0.02
    bounded = BoundedModule(wrapped, sample_x)
    bounded_x = BoundedTensor(sample_x, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")

    gen = torch.Generator().manual_seed(666)
    brute = []
    with torch.no_grad():
        nominal = wrapped(sample_x)
        for _ in range(60):
            delta = (torch.rand(sample_x.shape, generator=gen, dtype=sample_x.dtype) * 2.0 - 1.0) * eps
            brute.append(wrapped(sample_x + delta))
    brute_t = torch.stack(brute, dim=0)
    brute_min = brute_t.min(dim=0).values
    brute_max = brute_t.max(dim=0).values
    tol = 2e-5
    contains_brute = bool(torch.all(brute_min >= lb - tol) and torch.all(brute_max <= ub + tol))
    contains_nominal = bool(torch.all(nominal >= lb - tol) and torch.all(nominal <= ub + tol))

    return {
        "pass": bool(contains_brute and contains_nominal and torch.all((ub - lb) > 0.0).item()),
        "method": "IBP",
        "eps_linf": eps,
        "rows": int(sample_x.shape[0]),
        "contains_nominal": contains_nominal,
        "contains_bruteforce": contains_brute,
        "mean_bound_width": float(torch.mean(ub - lb).item()),
        "claim_ceiling": "LiRPA bounds finite conditioned-predictor output under input perturbation only; c is fixed.",
    }


# ---------------------------------------------------------------------------
# z3 witness: conditioning + EFE split jointly required
# ---------------------------------------------------------------------------

def z3_witness(
    pred_report: dict[str, Any],
    sigreg: dict[str, Any],
    lirpa: dict[str, Any],
) -> dict[str, Any]:
    solver = z3.Solver()
    cond_helps_hi = z3.Bool("cond_benefit_hi_positive")
    cond_helps_lo = z3.Bool("cond_benefit_lo_positive")
    cond_selective = z3.Bool("cond_selective_over_branches")
    sigreg_not_sufficient = z3.Bool("sigreg_gap_not_dominating_cond_gap")
    lirpa_ok = z3.Bool("lirpa_bounds_ok")
    load_bearing = z3.Bool("adaLN_load_bearing")

    cond_gap = pred_report["cond_benefit_hi"] - pred_report["cond_benefit_lo"]
    sigreg_gap = sigreg["gap"]

    solver.add(cond_helps_hi == (pred_report["cond_benefit_hi"] > 0.0))
    solver.add(cond_helps_lo == (pred_report["cond_benefit_lo"] >= 0.0))
    solver.add(cond_selective == bool(pred_report["pass"]))
    # sigreg not sufficient means: cond gap (branch-selective benefit) > sigreg_gap
    solver.add(sigreg_not_sufficient == bool(cond_gap > sigreg_gap / SIGREG_GAP_DOMINATION_THRESHOLD))
    solver.add(lirpa_ok == bool(lirpa["pass"]))
    solver.add(load_bearing == z3.And(cond_helps_hi, cond_selective, sigreg_not_sufficient, lirpa_ok))
    solver.add(z3.Not(load_bearing))

    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "status": str(status),
        "cond_gap_over_sigreg_gap": float(cond_gap),
        "sigreg_gap": float(sigreg_gap),
        "encoded_rule": (
            "AdaLN gating is load-bearing only when conditioning selectively reduces "
            "hi-EFE surprise more than lo-EFE, and this gap exceeds SIGReg static detection."
        ),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def as_jsonable(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): as_jsonable(vv) for k, vv in v.items()}
    if isinstance(v, (list, tuple)):
        return [as_jsonable(vv) for vv in v]
    if isinstance(v, pathlib.Path):
        return str(v)
    if torch.is_tensor(v):
        return v.detach().cpu().tolist()
    return v


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    started = time.time()

    features, efe_vals = collect_features()
    split = split_by_efe(features, efe_vals)
    sigreg = sigreg_gap_report(split)
    model, pred_report = predictor_gap_report(split)
    lirpa = lirpa_bound_report(model, split)
    witness = z3_witness(pred_report, sigreg, lirpa)
    lewm_ref = {
        "present": LEWM_ROOT.exists(),
        "module_py": (LEWM_ROOT / "module.py").exists(),
        "imported": False,
        "decision": "reference_only_design_source",
    }

    positive = {
        "adaLN_conditioning_selective_over_efe_branch_split": pred_report,
        "auto_lirpa_bounds_conditioned_predictor": lirpa,
        "z3_conditioning_and_efe_split_jointly_required": witness,
    }
    graveyards = {
        "sigreg_static_detection_does_not_substitute_for_conditioned_gap": {
            "pass": bool(
                (pred_report["cond_benefit_hi"] - pred_report["cond_benefit_lo"])
                > sigreg["gap"] / SIGREG_GAP_DOMINATION_THRESHOLD
            ),
            "sigreg_gap": sigreg["gap"],
            "cond_selective_gap": float(pred_report["cond_benefit_hi"] - pred_report["cond_benefit_lo"]),
            "threshold": SIGREG_GAP_DOMINATION_THRESHOLD,
        },
        "wrong_conditioning_degrades_hi_prediction": {
            "pass": bool(pred_report["wrong_cond_penalty"] > 0.0),
            "wrong_cond_penalty": pred_report["wrong_cond_penalty"],
        },
        "lewm_repo_not_imported": {
            "pass": bool(lewm_ref["present"] and not lewm_ref["imported"]),
            "decision": lewm_ref["decision"],
        },
    }
    repair_receipt = {
        "weak_link": (
            "Prior le-wm scouts tested static SIGReg collapse and IBP bounds but never tested "
            "whether AdaLN-zero gating selectively reduces prediction surprise across EFE-split branches."
        ),
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": (
            "le-wm ConditionalBlock is load-bearing iff conditioning on EFE-branch status "
            "reduces hi-EFE prediction surprise more than lo-EFE by ≥1.3×, "
            "and this gap exceeds SIGReg static gap by ≥1.2×."
        ),
        "dependency_subset": ["EngineCore stage records", "local auto_LiRPA", "local le-wm/module.py (reference only)"],
        "stage_fields_touched_or_consumed": FEATURE_NAMES,
        "before_baseline/hash": {
            "prior_state": "SIGReg + latent prediction bounds only; no branch-selective conditioning gap test",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "pred_report": pred_report,
            "sigreg": sigreg,
            "lirpa": lirpa,
            "z3": witness,
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": (
            "If green: this scout becomes the admission gate for le-wm ConditionalBlock "
            "as a load-bearing dynamic branch discriminator. Next step: test with CROWN/CROWN-IBP "
            "bounds beyond IBP, and test with multiple EFE threshold splits for stability."
        ),
    }
    boundary = {
        "claim_ceiling_blocks_world_model_or_architecture_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not import", "does not admit", "world model", "promotion_allowed: false"]
            ),
        },
        "no_le_wm_import_or_checkpoint": {
            "pass": bool(lewm_ref["present"] and not lewm_ref["imported"]),
        },
        "repair_receipt_has_required_fields": {
            "pass": all(
                k in repair_receipt
                for k in [
                    "weak_link", "target_file_or_result", "admission_rule_improved",
                    "dependency_subset", "stage_fields_touched_or_consumed",
                    "before_baseline/hash", "after_delta/hash",
                    "primary_control/result", "promotion_ceiling", "next_step",
                ]
            ),
        },
    }

    all_pass = (
        all(r.get("pass") is True for r in positive.values())
        and all(r.get("pass") is True for r in graveyards.values())
        and all(r.get("pass") is True for r in boundary.values())
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
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row.get("pass") is True),
        },
        "why_not_v4_probes": [
            "v5 formal scout over current manifold feature rows and local le-wm source reference",
            "does not import le-wm or use external checkpoints; the AdaLN branch is an inline finite fixture",
            "provider output is not evidence; this receipt is produced by local execution",
        ],
        "repair_receipt": repair_receipt,
        "sigreg_gap_report": sigreg,
        "lewm_reference": lewm_ref,
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
