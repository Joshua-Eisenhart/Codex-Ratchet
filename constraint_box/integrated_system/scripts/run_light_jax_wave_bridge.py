#!/usr/bin/env python3
"""Run one bounded Light -> JAX observation -> wave -> Light settlement route."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


SCHEMA = "constraintbox.light-jax-wave-bridge.v1"

# Children produced by run_json().  Each must retain its subprocess return
# code so a nonzero exit cannot be masked by a PASS-like JSON body.
RUN_JSON_CHILD_NAMES = (
    "seed",
    "etf_exact",
    "etf_dual",
    "maintenance",
    "context",
    "exploration",
    "dualsolve",
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def declared_interpreter(path: Path) -> Path:
    """Validate without resolving a venv/symlink into its base interpreter."""
    declared = path.expanduser().absolute()
    if not declared.is_file() or not os.access(declared, os.X_OK):
        raise ValueError(f"interpreter is not executable: {declared}")
    return declared


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_json(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 180.0,
) -> tuple[int, dict[str, Any], str]:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    text = (completed.stdout or "").strip()
    try:
        value = json.loads(text)
        body = value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        body = {}
    return completed.returncode, body, (completed.stderr or "")[-1000:]


def runtime_probe(python: Path, modules: list[str]) -> dict[str, Any]:
    code = (
        "import importlib,json,pathlib,sys; rows={}; "
        "[(lambda n: rows.update({n:{'imported':True,'version':str(getattr(importlib.import_module(n),'__version__',None)),'origin':getattr(importlib.import_module(n),'__file__',None)}}))(n) for n in json.loads(sys.argv[1])]; "
        "print(json.dumps({'executable':sys.executable,'realpath':str(pathlib.Path(sys.executable).resolve()),'prefix':sys.prefix,'modules':rows},sort_keys=True))"
    )
    completed = subprocess.run(
        [str(python), "-I", "-c", code, json.dumps(modules)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return {
            "status": "HOLD_RUNTIME_PROBE",
            "returncode": completed.returncode,
            "stderr": (completed.stderr or "")[-1000:],
        }
    return {"status": "PROBED", **json.loads(completed.stdout)}


def light_jax_negative(light_python: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [str(light_python), "-I", "-c", "import jax"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return {
        "status": "PASS" if completed.returncode != 0 else "REFUSE_JAX_IN_LIGHT",
        "returncode": completed.returncode,
        "stderr_sha256": sha256_bytes((completed.stderr or "").encode("utf-8")),
    }


def settle(children: dict[str, dict[str, Any]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if children["light_jax_negative"].get("status") != "PASS":
        reasons.append("REFUSE_JAX_IN_LIGHT")
    if children["jax_runtime"].get("status") != "PROBED":
        reasons.append("HOLD_JAX_RUNTIME")
    if children["seed"].get("disposition") != "ADMIT":
        reasons.append("HOLD_LIGHT_SEED")
    for name in ("etf_exact", "etf_dual"):
        if children[name].get("status") != "PASS":
            reasons.append(f"HOLD_{name.upper()}")
    if children["maintenance"].get("status") != "READY":
        reasons.append("HOLD_MAINTENANCE")
    if children["context"].get("status") != "CONTEXT_SNAPSHOT_READY":
        reasons.append("HOLD_CONTEXT_WAVE")
    if children["exploration"].get("status") != "ANTICHAIN_OPEN":
        reasons.append("HOLD_EXPLORATION_WAVE")
    if children["dualsolve"].get("status") != "BOUNDED_SAT":
        reasons.append("HOLD_LIGHT_SETTLEMENT")
    for name in RUN_JSON_CHILD_NAMES:
        if children[name].get("returncode") != 0:
            reasons.append(f"HOLD_{name.upper()}_RETURNCODE")
    return ("PASS" if not reasons else "HOLD"), reasons


def replay_projection(
    children: dict[str, dict[str, Any]],
    *,
    target_sha256: str,
    source_bindings: dict[str, str],
) -> dict[str, Any]:
    seed = children["seed"]
    exact = children["etf_exact"]
    dual = children["etf_dual"]
    maintenance = children["maintenance"]
    context = children["context"]
    exploration = children["exploration"]
    settlement = children["dualsolve"]
    return {
        "light_jax_negative": children["light_jax_negative"].get("status"),
        "jax_runtime": {
            "status": children["jax_runtime"].get("status"),
            "prefix": children["jax_runtime"].get("prefix"),
            "modules": {
                name: {
                    "imported": row.get("imported"),
                    "version": row.get("version"),
                }
                for name, row in sorted(
                    (children["jax_runtime"].get("modules") or {}).items()
                )
            },
        },
        "seed": {
            "disposition": seed.get("disposition"),
            "source_sha256": seed.get("source_sha256"),
            "support_counts": seed.get("support_counts"),
            "delta_K": seed.get("delta_K"),
        },
        "etf_exact": {
            "status": exact.get("status"),
            "result_sha256": exact.get("result_sha256"),
        },
        "etf_dual": {
            "status": dual.get("status"),
            "result_sha256": dual.get("result_sha256"),
            "jax_output_sha256": (dual.get("jax") or {}).get("output_sha256"),
        },
        "maintenance": {
            "status": maintenance.get("status"),
            "source_digest": maintenance.get("source_digest"),
            "context_digest": maintenance.get("context_digest"),
            "candidate_decisions": [
                {
                    "relative_path": row.get("relative_path"),
                    "classification": row.get("classification"),
                    "reason_code": row.get("reason_code"),
                }
                for row in maintenance.get("candidate_decisions") or []
            ],
        },
        "context": {
            "status": context.get("status"),
            "prompt_corpus_digest": context.get("prompt_corpus_digest"),
            "user_mmm_draft_digest": context.get("user_mmm_draft_digest"),
            "project_mmm_draft_digest": context.get("project_mmm_draft_digest"),
        },
        "exploration": {
            "status": exploration.get("status"),
            "seed_digest": exploration.get("seed_digest"),
            "reading_count": exploration.get("reading_count"),
            "family_count": exploration.get("family_count"),
            "antichain_digest": exploration.get("antichain_digest"),
            "distinguish_packet_digest": exploration.get(
                "distinguish_packet_digest"
            ),
        },
        "dualsolve": {
            "status": settlement.get("status"),
            "packet_sha256": settlement.get("packet_sha256"),
            "receipt_sha256": settlement.get("receipt_sha256"),
            "agree": (settlement.get("dual_solve") or {}).get("agree"),
        },
        "target_sha256": target_sha256,
        "source_bindings": source_bindings,
    }


def run_bridge(
    *,
    box_root: Path,
    light_python: Path,
    jax_python: Path,
    skills_root: Path,
    mmm_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    box_root = box_root.resolve(strict=True)
    light_python = declared_interpreter(light_python)
    jax_python = declared_interpreter(jax_python)
    skills_root = skills_root.resolve(strict=True)
    mmm_root = mmm_root.resolve(strict=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    observations_dir = output_dir / "observations"
    observations_dir.mkdir(parents=True, exist_ok=True)
    fixture = box_root / "scripts/contained_light/fixtures/entropic_time_field_v1.json"
    field_source = box_root / "scripts/contained_light/entropic_time_field.py"
    seed_source = box_root / "scripts/contained_light/seed_check.py"
    campaign_source = box_root / "experiments/manifold_capability/v1/campaign.py"
    campaign_custody = box_root / "experiments/manifold_capability/v1/REPLAY_CUSTODY.json"

    controller_src = box_root / "integrated_system/runtime/controller_src"
    if controller_src.is_dir():
        python_roots = [str(controller_src)]
    else:
        # Source-checkout compatibility.  The release bundle always carries
        # the single merged controller tree above.
        python_roots = [
            str(box_root / "src"),
            str(box_root / "light_runtime/src"),
        ]
    common_env = os.environ.copy()
    common_env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "CB_SKILLS_ROOT": str(skills_root),
            "CB_BOX_ROOT": str(box_root),
            "CB_LIGHT_PYTHON": str(light_python),
            "CB_MMM_ROOT": str(mmm_root),
            "PYTHONPATH": os.pathsep.join(python_roots),
        }
    )

    children: dict[str, dict[str, Any]] = {}
    children["light_jax_negative"] = light_jax_negative(light_python)
    children["jax_runtime"] = runtime_probe(
        jax_python, ["jax", "jaxlib", "sympy", "rustworkx", "z3", "cvc5"]
    )

    seed_path = output_dir / "seed_check.json"
    seed_rc, seed, seed_stderr = run_json(
        [str(light_python), str(seed_source), "--root", str(box_root), "--out", str(seed_path)],
        cwd=box_root,
        env=common_env,
    )
    children["seed"] = {**seed, "stderr": seed_stderr, "returncode": seed_rc}

    exact_path = observations_dir / "etf_exact.json"
    exact_rc, exact, exact_stderr = run_json(
        [
            str(light_python),
            str(field_source),
            "--input",
            str(fixture),
            "--output",
            str(exact_path),
            "--engine",
            "exact",
        ],
        cwd=box_root,
        env=common_env,
    )
    children["etf_exact"] = {**exact, "stderr": exact_stderr, "returncode": exact_rc}

    dual_path = observations_dir / "etf_dual.json"
    dual_rc, dual, dual_stderr = run_json(
        [
            str(jax_python),
            str(field_source),
            "--input",
            str(fixture),
            "--output",
            str(dual_path),
            "--engine",
            "dual",
        ],
        cwd=box_root,
        env=common_env,
        timeout=240,
    )
    children["etf_dual"] = {**dual, "stderr": dual_stderr, "returncode": dual_rc}

    target = {
        "schema": "constraintbox.light-jax-wave-target.v1",
        "operation": "finite_entropic_time_dual_engine_observation.v1",
        "light_seed_source_sha256": seed.get("source_sha256"),
        "light_seed_support_counts": seed.get("support_counts"),
        "light_seed_delta_K": seed.get("delta_K"),
        "etf_exact_sha256": sha256_path(exact_path) if exact_path.is_file() else None,
        "etf_dual_sha256": sha256_path(dual_path) if dual_path.is_file() else None,
        "campaign_source_sha256": sha256_path(campaign_source),
        "campaign_custody_sha256": sha256_path(campaign_custody),
        "questions": [
            "Does structured support-extension/probe-restriction preserve a non-generic order scar?",
            "Which probe family changes Q without inventing observations?",
            "Which two-hand controls should falsify the current fixture?",
        ],
        "claim_ceiling": (
            "bounded Light seed plus exact/JAX agreement and campaign custody inputs; "
            "not chirality, not manifold admission, not provider execution"
        ),
        "promotion_allowed": False,
    }
    target_path = observations_dir / "bridge_target.json"
    write_json(target_path, target)

    zip_source_path = "zip_agent/src"
    zip_package_path = "zip_agent"
    if not (box_root / zip_source_path).is_dir():
        zip_source_path = "integrated_system/runtime/zip_agent_src"
        zip_package_path = zip_source_path
    maintenance_path = output_dir / "maintenance.json"
    maintenance_rc, maintenance, _ = run_json(
        [
            str(light_python),
            "-I",
            str(skills_root / "cb-maintenance-wave/scripts/run_maintenance_wave.py"),
            "--root",
            str(box_root),
            "--package",
            zip_package_path,
            "--source-path",
            "integrated_system/scripts",
            "--source-path",
            "integrated_system/skills",
            "--source-path",
            "integrated_system/mmms/primary/mini",
            "--source-path",
            "light_runtime/src",
            "--source-path",
            zip_source_path,
            "--context-path",
            "integrated_system/context/current",
            "--candidate",
            "integrated_system",
            "--requested-action",
            "classify",
            "--run-id",
            "light-jax-wave-bridge",
            "--output",
            str(maintenance_path),
        ],
        cwd=box_root,
        env=common_env,
    )
    if maintenance_path.is_file():
        maintenance = json.loads(maintenance_path.read_text(encoding="utf-8"))
    children["maintenance"] = {**maintenance, "returncode": maintenance_rc}

    context_path = output_dir / "context_strategy.json"
    context_rc, context, _ = run_json(
        [
            str(light_python),
            "-I",
            str(skills_root / "cb-context-strategy-wave/scripts/run_context_strategy.py"),
            "--root",
            str(box_root),
            "--prompt-path",
            "integrated_system/context/current",
            "--output-path",
            str(observations_dir),
            "--out",
            str(context_path),
        ],
        cwd=box_root,
        env=common_env,
    )
    if context_path.is_file():
        context = json.loads(context_path.read_text(encoding="utf-8"))
    children["context"] = {**context, "returncode": context_rc}

    readings = {
        "readings": [
            {
                "id": "structured-map-family",
                "family": "structured_open_bind",
                "text": "Open extends support and bind restricts by named probes and constraints.",
            },
            {
                "id": "generic-order-scar",
                "family": "generic_noncommutation_control",
                "text": "The observed order gap may be generic endomap noncommutation.",
            },
            {
                "id": "two-functional-hands",
                "family": "two_hand_field_hypothesis",
                "text": "One gradient may admit two ordered functional readings without two clocks.",
            },
            {
                "id": "measurement-artifact",
                "family": "probe_artifact_control",
                "text": "A different finite probe family may erase the apparent scar.",
            },
        ]
    }
    readings_path = output_dir / "readings.json"
    write_json(readings_path, readings)
    exploration_path = output_dir / "exploration.json"
    exploration_rc, exploration, _ = run_json(
        [
            str(light_python),
            "-I",
            str(skills_root / "cb-exploration-wave/scripts/run_exploration.py"),
            "--root",
            str(box_root),
            "--seed",
            str(target_path),
            "--readings",
            str(readings_path),
            "--out",
            str(exploration_path),
        ],
        cwd=box_root,
        env=common_env,
    )
    if exploration_path.is_file():
        exploration = json.loads(exploration_path.read_text(encoding="utf-8"))
    children["exploration"] = {**exploration, "returncode": exploration_rc}

    packet_path = output_dir / "distinguish.packet.json"
    dualsolve_rc, dualsolve, dualsolve_stderr = run_json(
        [str(light_python), "-m", "constraintbox.distinguishability", str(packet_path)],
        cwd=box_root,
        env=common_env,
    )
    children["dualsolve"] = {**dualsolve, "stderr": dualsolve_stderr, "returncode": dualsolve_rc}

    status, reasons = settle(children)
    child_files = [
        path
        for path in (
            seed_path,
            exact_path,
            dual_path,
            target_path,
            maintenance_path,
            context_path,
            exploration_path,
            packet_path,
        )
        if path.is_file()
    ]
    source_bindings = {
        "bridge_source_sha256": sha256_path(Path(__file__)),
        "field_source_sha256": sha256_path(field_source),
        "seed_source_sha256": sha256_path(seed_source),
        "fixture_sha256": sha256_path(fixture),
        "campaign_source_sha256": sha256_path(campaign_source),
        "campaign_custody_sha256": sha256_path(campaign_custody),
    }
    projection = replay_projection(
        children,
        target_sha256=sha256_path(target_path),
        source_bindings=source_bindings,
    )
    receipt = {
        "schema": SCHEMA,
        "status": status,
        "reason_codes": reasons,
        "operation": "light_jax_wave_bridge.v1",
        "children": children,
        "bindings": {
            **source_bindings,
            "child_file_sha256": {
                str(path.relative_to(output_dir)): sha256_path(path)
                for path in child_files
            },
        },
        "boundaries": {
            "one_system": True,
            "interpreter_count": 2,
            "light_contains_jax": False,
            "jax_output_is_observation_only": True,
            "wave_can_promote": False,
            "dualsolve_invents_probes": False,
        },
        "next_operation": "structured_open_bind_family_probe.v1",
        "replay_projection": projection,
        "replay_projection_sha256": sha256_bytes(canonical_json_bytes(projection)),
        "claim_ceiling": (
            "local Light/JAX boundary and two model-free wave children with Light "
            "finite settlement; not provider execution, structured-map success, "
            "chirality, manifold admission, or promotion"
        ),
        "promotion_allowed": False,
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    write_json(output_dir / "bridge_receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--box-root", required=True, type=Path)
    parser.add_argument("--light-python", required=True, type=Path)
    parser.add_argument("--jax-python", required=True, type=Path)
    parser.add_argument("--skills-root", required=True, type=Path)
    parser.add_argument("--mmm-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = run_bridge(
            box_root=args.box_root,
            light_python=args.light_python,
            jax_python=args.jax_python,
            skills_root=args.skills_root,
            mmm_root=args.mmm_root,
            output_dir=args.output_dir,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "status": "REFUSE",
                    "reason_codes": ["REFUSE_BRIDGE_EXECUTION"],
                    "detail": f"{type(exc).__name__}:{exc}",
                    "promotion_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "status": receipt["status"],
                "reason_codes": receipt["reason_codes"],
                "receipt_sha256": receipt["receipt_sha256"],
                "promotion_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
