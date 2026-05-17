#!/usr/bin/env python3
"""Sana diffusers system integration smoke.

This is a tool integration smoke, not a Codex Ratchet science sim. It verifies
that the repo interpreter can import Hugging Face diffusers' SanaPipeline and
records the local device boundary without downloading model weights by default.

Set RUN_SANA_MODEL_LOAD=1 to try an explicit model load. That path is
local-cache-only unless SANA_ALLOW_DOWNLOAD=1 is also set.
"""

from __future__ import annotations

import importlib
import importlib.metadata as metadata
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "sana_diffusers_system_smoke_results.json"
DEFAULT_MODEL_ID = "Efficient-Large-Model/Sana_600M_512px_diffusers"

CLASSIFICATION = "tool_lego_fit_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Sana/diffusers import and system-tool reachability smoke only. No image "
    "quality, QIT, FEP, Holodeck, engine, or canonical system claim."
)

TOOL_MANIFEST = {
    "diffusers": {
        "tried": True,
        "used": True,
        "reason": "load-bearing import surface for SanaPipeline",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local device capability boundary for Sana inference",
    },
    "transformers": {
        "tried": True,
        "used": True,
        "reason": "supporting SanaPipeline text-encoder dependency",
    },
    "accelerate": {
        "tried": True,
        "used": True,
        "reason": "supporting diffusers pipeline loading dependency",
    },
    "huggingface_hub": {
        "tried": True,
        "used": True,
        "reason": "supporting model repository client dependency; no download attempted by default",
    },
    "safetensors": {
        "tried": True,
        "used": True,
        "reason": "supporting weight-format dependency; no weights loaded by default",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "diffusers": "load_bearing",
    "torch": "supportive",
    "transformers": "supportive",
    "accelerate": "supportive",
    "huggingface_hub": "supportive",
    "safetensors": "supportive",
}


def version_for(module_name: str) -> str:
    dist_names = {"huggingface_hub": "huggingface-hub", "PIL": "pillow"}
    try:
        return metadata.version(dist_names.get(module_name, module_name))
    except metadata.PackageNotFoundError:
        return "missing"


def import_module(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {
            "pass": True,
            "version": version_for(module_name),
            "file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "pass": False,
            "version": version_for(module_name),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def load_sana_model(SanaPipeline: Any) -> tuple[dict[str, Any], Any | None]:
    model_id = os.environ.get("SANA_MODEL_ID", DEFAULT_MODEL_ID)
    cache_dir = os.environ.get("SANA_CACHE_DIR")
    allow_download = bool_env("SANA_ALLOW_DOWNLOAD")
    started = time.time()
    kwargs: dict[str, Any] = {"local_files_only": not allow_download}
    if cache_dir:
        kwargs["cache_dir"] = cache_dir

    check: dict[str, Any] = {
        "model_id": model_id,
        "cache_dir": cache_dir,
        "allow_download": allow_download,
        "local_files_only": not allow_download,
    }
    try:
        pipe = SanaPipeline.from_pretrained(model_id, **kwargs)
        check.update(
            {
                "pass": True,
                "class": f"{pipe.__class__.__module__}.{pipe.__class__.__name__}",
                "elapsed_seconds": time.time() - started,
            }
        )
        return check, pipe
    except Exception as exc:  # noqa: BLE001
        check.update(
            {
                "pass": False,
                "blocked": not allow_download,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "elapsed_seconds": time.time() - started,
            }
        )
        return check, None


def generate_sana_image(pipe: Any) -> dict[str, Any]:
    output_path = os.environ.get("SANA_OUTPUT_PATH")
    if not output_path:
        return {
            "pass": False,
            "blocked": True,
            "reason": "RUN_SANA_GENERATE=1 requires SANA_OUTPUT_PATH.",
        }

    import torch

    requested_device = os.environ.get("SANA_DEVICE")
    if requested_device:
        device = requested_device
    elif torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    prompt = os.environ.get("SANA_PROMPT", "a small geometric test image")
    steps = int(os.environ.get("SANA_STEPS", "2"))
    height = int(os.environ.get("SANA_HEIGHT", "512"))
    width = int(os.environ.get("SANA_WIDTH", "512"))
    started = time.time()
    try:
        pipe = pipe.to(device)
        image = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            height=height,
            width=width,
            guidance_scale=float(os.environ.get("SANA_GUIDANCE_SCALE", "4.5")),
        ).images[0]
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out)
        return {
            "pass": True,
            "device": device,
            "requested_device": requested_device,
            "output_path": str(out),
            "prompt": prompt,
            "height": height,
            "width": width,
            "steps": steps,
            "elapsed_seconds": time.time() - started,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "pass": False,
            "device": device,
            "requested_device": requested_device,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "elapsed_seconds": time.time() - started,
        }


def main() -> dict[str, Any]:
    started = time.time()
    out_path = Path(os.environ.get("SANA_RESULT_PATH", str(OUT_PATH)))
    imports = {
        name: import_module(name)
        for name in [
            "torch",
            "diffusers",
            "transformers",
            "accelerate",
            "huggingface_hub",
            "safetensors",
            "sentencepiece",
            "PIL",
        ]
    }

    checks: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []

    try:
        import torch

        device = {
            "cuda_available": bool(torch.cuda.is_available()),
            "mps_available": bool(
                hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
            ),
            "mps_built": bool(
                hasattr(torch.backends, "mps") and torch.backends.mps.is_built()
            ),
            "torch_version": torch.__version__,
        }
    except Exception as exc:  # noqa: BLE001
        device = {"error_type": type(exc).__name__, "error": str(exc)}
        blockers.append("torch_device_check_failed")

    SanaPipeline = None
    try:
        from diffusers import SanaPipeline

        checks["sana_pipeline_import"] = {
            "pass": True,
            "class": f"{SanaPipeline.__module__}.{SanaPipeline.__name__}",
            "has_from_pretrained": hasattr(SanaPipeline, "from_pretrained"),
        }
    except Exception as exc:  # noqa: BLE001
        checks["sana_pipeline_import"] = {
            "pass": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        blockers.append("sana_pipeline_import_failed")

    run_model_load = bool_env("RUN_SANA_MODEL_LOAD") or bool_env("RUN_SANA_GENERATE")
    model_download_attempted = run_model_load and bool_env("SANA_ALLOW_DOWNLOAD")
    loaded_pipe = None
    if run_model_load and SanaPipeline is not None:
        checks["sana_model_load"], loaded_pipe = load_sana_model(SanaPipeline)
        if not checks["sana_model_load"].get("pass", False):
            if checks["sana_model_load"].get("blocked"):
                blockers.append("sana_model_load_blocked_no_local_cache_or_download")
            else:
                blockers.append("sana_model_load_failed")
    elif run_model_load:
        checks["sana_model_load"] = {
            "pass": False,
            "blocked": True,
            "reason": "SanaPipeline import failed, so model load was not attempted.",
        }
        blockers.append("sana_model_load_blocked_import_failed")
    else:
        checks["default_no_model_download"] = {
            "pass": True,
            "reason": "Default smoke imports SanaPipeline only and never calls from_pretrained.",
        }

    if bool_env("RUN_SANA_GENERATE"):
        if checks.get("sana_model_load", {}).get("pass", False) and loaded_pipe is not None:
            checks["sana_generation"] = generate_sana_image(loaded_pipe)
        else:
            checks["sana_generation"] = {
                "pass": False,
                "blocked": True,
                "reason": "Generation requires a successful Sana model load.",
            }
        if not checks["sana_generation"].get("pass", False):
            blockers.append("sana_generation_failed_or_blocked")

    result = {
        "schema": "SANA_DIFFUSERS_SYSTEM_SMOKE_v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "python": sys.version,
        "executable": sys.executable,
        "result_path": str(out_path),
        "imports": imports,
        "device": device,
        "checks": checks,
        "model_download_attempted": model_download_attempted,
        "blockers": blockers,
        "all_pass": (
            all(row.get("pass", False) for row in imports.values())
            and all(row.get("pass", False) for row in checks.values())
            and not blockers
        ),
        "elapsed_seconds": time.time() - started,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    payload = main()
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0 if payload["all_pass"] else 1)
