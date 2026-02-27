#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
RUNNER = BOOTPACK / "a1_a0_b_sim_runner.py"

LAWYER_PACK = SYSTEM_V3 / "tools" / "a1_lawyer_pack.py"
LAWYER_SINK = SYSTEM_V3 / "tools" / "a1_lawyer_sink.py"
COLD_CORE_STRIP = SYSTEM_V3 / "tools" / "a1_cold_core_strip.py"
PACK_SELECTOR = SYSTEM_V3 / "tools" / "a1_pack_selector.py"
PACKETIZE = SYSTEM_V3 / "tools" / "codex_json_to_a1_strategy_packet_zip.py"
MEMO_QUALITY_GATE = SYSTEM_V3 / "tools" / "a1_memo_quality_gate.py"


def _run_cmd(cmd: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _count_rescue_from_fields(strategy_path: Path) -> int:
    try:
        strategy = _read_json(strategy_path)
    except Exception:
        return 0
    count = 0
    for item in strategy.get("alternatives", []) if isinstance(strategy, dict) else []:
        if not isinstance(item, dict):
            continue
        for row in item.get("def_fields", []) or []:
            if isinstance(row, dict) and str(row.get("name", "")).strip() == "RESCUE_FROM":
                count += 1
    return int(count)


def _strategy_target_probe_terms(strategy_path: Path) -> list[str]:
    try:
        strategy = _read_json(strategy_path)
    except Exception:
        return []
    out: list[str] = []
    for item in strategy.get("targets", []) if isinstance(strategy, dict) else []:
        if not isinstance(item, dict):
            continue
        if str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        for row in item.get("def_fields", []) or []:
            if isinstance(row, dict) and str(row.get("name", "")).strip() == "PROBE_TERM":
                term = str(row.get("value", "")).strip()
                if term:
                    out.append(term)
    return out


def _dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if not p.is_file():
            continue
        try:
            total += p.stat().st_size
        except OSError:
            continue
    return int(total)


def _prune_dir_keep_last(path: Path, *, keep_last: int) -> dict:
    """
    Keep the newest `keep_last` files (by name sort) and delete older ones.

    This is a *run-hygiene* measure: A1 sandbox artifacts are high-entropy and can
    explode in volume during unattended campaigns. We keep a small tail for
    debugging, but prefer a lean run surface.
    """
    if keep_last <= 0 or not path.exists() or not path.is_dir():
        return {"path": str(path), "kept": 0, "deleted": 0}
    files = sorted([p for p in path.iterdir() if p.is_file() and not p.name.startswith(".")], key=lambda p: p.name)
    if len(files) <= keep_last:
        return {"path": str(path), "kept": len(files), "deleted": 0}
    to_delete = files[: max(0, len(files) - int(keep_last))]
    deleted = 0
    for p in to_delete:
        try:
            p.unlink()
            deleted += 1
        except OSError:
            continue
    return {"path": str(path), "kept": len(files) - deleted, "deleted": deleted}


def _init_run(*, run_id: str, runs_root: Path, clean: bool) -> None:
    cmd = ["python3", str(RUNNER), "--a1-source", "packet", "--run-id", run_id, "--steps", "1", "--runs-root", str(runs_root)]
    if clean:
        cmd.append("--clean")
    _run_cmd(cmd, cwd=BOOTPACK)


def _required_roles_for_preset(preset: str) -> set[str]:
    # Must match presets in a1_lawyer_pack.py.
    if preset == "entropy_lenses7":
        return {
            "LENS_VN",
            "LENS_MUTUAL_INFO",
            "LENS_CONDITIONAL",
            "LENS_THERMO_ANALOGY",
            "DEVIL_CLASSICAL_SMUGGLER",
            "RESCUER",
        }
    if preset == "graveyard13":
        return {
            "STEELMAN_CORE",
            "STEELMAN_ALT_FORMALISM",
            "DEVIL_CLASSICAL_TIME",
            "DEVIL_COMMUTATIVE",
            "DEVIL_CONTINUUM",
            "DEVIL_EQUALS_SMUGGLE",
            "BOUNDARY_REPAIR",
            "RESCUER_MINIMAL_EDIT",
            "RESCUER_OPERATOR_REFACTOR",
            "ENTROPY_LENS_VN",
            "ENTROPY_LENS_MUTUAL",
            "ENGINE_LENS_SZILARD_CARNOT",
        }
    # lawyer4
    return {"STEELMAN", "DEVIL", "BOUNDARY"}


def _discover_sequence_from_pack(pack_result: dict) -> int:
    try:
        return int(pack_result.get("sequence", 0))
    except Exception:
        return 0


def _recent_rescue_targets(run_dir: Path, *, limit: int = 16) -> list[str]:
    state = _read_json(run_dir / "state.json")
    out: list[str] = []
    for row in reversed(state.get("kill_log", []) if isinstance(state, dict) else []):
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        sid = str(row.get("id", "")).strip()
        if not sid:
            continue
        out.append(sid)
        if len(out) >= int(limit):
            break
    out.reverse()
    return out


@dataclass(frozen=True)
class _StopCaps:
    max_run_mb: float


def _autofill_entropy_lenses7_memos(
    *, run_id: str, sequence: int, run_dir: Path, memo_drop_dir: Path, focus_terms: list[str]
) -> list[Path]:
    """
    Deterministic “no-LLM” memo autofill for entropy_lenses7.

    This is intentionally conservative: it uses short, low-entropy claims and
    prioritizes terms that already have real SIM probes. It exists to keep the
    ratchet moving when an interactive LLM step isn't available.
    """
    import time

    memo_drop_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    # Keep a stable base substrate so the pack selector has enough overlap.
    base = [
        "density_matrix",
        "probe_operator",
        "unitary_operator",
        "cptp_channel",
        "partial_trace",
        "correlation_polarity",
        "entropy_production_rate",
        "qit_master_conjunction",
        "engine_cycle",
    ]
    terms = sorted({t for t in (base + list(focus_terms or [])) if isinstance(t, str) and t.strip()})

    # Default adversarial classes: only the ones the downstream mapping understands today.
    # (The SIM engine itself can recognize additional semantic-field markers, but negative
    # classes are how we wire KILL_IF deterministically.)
    neg = ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME", "CONTINUOUS_BATH", "INFINITE_SET", "INFINITE_RESOLUTION"]

    role_templates: dict[str, dict[str, list[str] | str]] = {
        "LENS_VN": {
            "claims": [
                "Prefer density_matrix + probe_operator substrate; avoid identity/equals primitives.",
                "Admit finite probes first: measurement/operator/geometry terms only when SIM probes pass.",
            ],
            "risks": ["No time/bath primitives unless adversarial."],
        },
        "LENS_MUTUAL_INFO": {
            "claims": [
                "Use partial_trace cuts + trajectory_correlation style witnesses; correlation_polarity is a probe-classification, not a story.",
            ],
            "risks": ["Avoid classical probability collapse."],
        },
        "LENS_CONDITIONAL": {
            "claims": [
                "Conditional regimes may go negative; represent via probe evidence, not narrative entropy.",
            ],
            "risks": ["Do not introduce continuous-time generators."],
        },
        "LENS_THERMO_ANALOGY": {
            "claims": [
                "Carnot/Szilard are quarantined analogies: accept only the stroke graph pattern, not baths/time.",
                "Engine_cycle uses unitary_operator vs cptp_channel strokes; entropy_production_rate is the witness.",
            ],
            "risks": ["No temperature/bath primitives."],
        },
        "DEVIL_CLASSICAL_SMUGGLER": {
            "claims": [
                "Attempt classical smuggling: commutative collapse + global time parameter + continuous bath framing.",
            ],
            "risks": ["Adversarial only; should be killed via NEGATIVE_CLASS wiring."],
        },
        "RESCUER": {
            "claims": [
                "Rescue killed items by removing time/bath primitives and re-expressing as finite probe sequences.",
                "Keep classical boundary explicit; no narrative smoothing.",
            ],
            "risks": ["Do not collapse distinct candidates into a single story."],
        },
    }

    written: list[Path] = []
    rescue_targets = _recent_rescue_targets(run_dir, limit=16)
    for role, tpl in role_templates.items():
        obj = {
            "schema": "A1_LAWYER_MEMO_v1",
            "run_id": str(run_id),
            "sequence": int(sequence),
            "role": str(role),
            "claims": list(tpl.get("claims", [])),  # type: ignore[arg-type]
            "risks": list(tpl.get("risks", [])),  # type: ignore[arg-type]
            "proposed_terms": terms,
            "proposed_negative_classes": neg,
            "graveyard_rescue_targets": list(rescue_targets),
        }
        path = memo_drop_dir / f"{sequence:06d}_MEMO_{role}__{stamp}__AUTOFILL.json"
        path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _autofill_graveyard13_memos(
    *, run_id: str, sequence: int, run_dir: Path, memo_drop_dir: Path, focus_terms: list[str]
) -> list[Path]:
    import time

    memo_drop_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    rescue_targets = _recent_rescue_targets(run_dir, limit=24)

    base_terms = sorted(
        {
            "finite_dimensional_hilbert_space",
            "density_matrix",
            "probe_operator",
            "cptp_channel",
            "partial_trace",
            "unitary_operator",
            "noncommutative_composition_order",
            "commutator_operator",
            "measurement_operator",
            "observable_operator",
            "projector_operator",
            "pauli_operator",
            "bloch_sphere",
            "hopf_fibration",
            "hopf_torus",
            "berry_flux",
            "spinor_double_cover",
            "left_weyl_spinor",
            "right_weyl_spinor",
            "left_action_superoperator",
            "right_action_superoperator",
            "von_neumann_entropy",
            "trajectory_correlation",
            "correlation_polarity",
            "entropy_production_rate",
            "engine_cycle",
            "qit_master_conjunction",
            "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
            "information_work_extraction_bound",
            "erasure_channel_entropy_cost_lower_bound",
            *list(focus_terms or []),
        }
    )

    neg_role_map: dict[str, list[str]] = {
        "STEELMAN_CORE": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
        "STEELMAN_ALT_FORMALISM": ["COMMUTATIVE_ASSUMPTION", "INFINITE_SET"],
        "DEVIL_CLASSICAL_TIME": ["CLASSICAL_TIME"],
        "DEVIL_COMMUTATIVE": ["COMMUTATIVE_ASSUMPTION"],
        "DEVIL_CONTINUUM": ["INFINITE_SET", "INFINITE_RESOLUTION", "CONTINUOUS_BATH"],
        "DEVIL_EQUALS_SMUGGLE": ["COMMUTATIVE_ASSUMPTION", "INFINITE_SET"],
        "BOUNDARY_REPAIR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
        "RESCUER_MINIMAL_EDIT": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
        "RESCUER_OPERATOR_REFACTOR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
        "ENTROPY_LENS_VN": ["CLASSICAL_TIME", "CONTINUOUS_BATH"],
        "ENTROPY_LENS_MUTUAL": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
        "ENGINE_LENS_SZILARD_CARNOT": ["CONTINUOUS_BATH", "CLASSICAL_TIME", "INFINITE_SET"],
    }

    role_templates: dict[str, dict[str, list[str] | str]] = {
        "STEELMAN_CORE": {
            "claims": [
                "Build strongest finite noncommutative substrate first: density_matrix + probe_operator + cptp_channel + partial_trace.",
                "Keep terms explicit and compositional; avoid narrative labels in math surfaces.",
            ],
            "risks": ["Do not smuggle equals/identity primitives."],
        },
        "STEELMAN_ALT_FORMALISM": {
            "claims": [
                "Construct an admissible alternate formal path using superoperators and operator-sidedness without changing constraints.",
            ],
            "risks": ["Avoid implicit classical geometry assumptions."],
        },
        "DEVIL_CLASSICAL_TIME": {
            "claims": ["Generate plausible candidates that rely on primitive global time and should fail under constraints."],
            "risks": ["Adversarial lane; expected to die."],
        },
        "DEVIL_COMMUTATIVE": {
            "claims": ["Generate plausible candidates that assume effective commutativity and should fail under noncommutation."],
            "risks": ["Adversarial lane; expected to die."],
        },
        "DEVIL_CONTINUUM": {
            "claims": ["Generate plausible candidates that assume infinite/continuous sets or infinite resolution and should fail."],
            "risks": ["Adversarial lane; expected to die."],
        },
        "DEVIL_EQUALS_SMUGGLE": {
            "claims": ["Generate identity/equality smuggling variants that look neat but hide classical assumptions."],
            "risks": ["Adversarial lane; expected to die."],
        },
        "BOUNDARY_REPAIR": {
            "claims": ["Generate near-boundary perturbation and stress variants around known failures."],
            "risks": ["Do not converge all variants into one narrative."],
        },
        "RESCUER_MINIMAL_EDIT": {
            "claims": ["Select recent graveyard items and propose minimal-edit rescue candidates with explicit ancestry."],
            "risks": ["Rescue can fail; failure is informative."],
        },
        "RESCUER_OPERATOR_REFACTOR": {
            "claims": ["Select recent graveyard items and attempt operator-level rewrites preserving finite noncommutative structure."],
            "risks": ["Rescue can fail; avoid narrative smoothing."],
        },
        "ENTROPY_LENS_VN": {
            "claims": ["Drive entropy claims through spectrum/operator witnesses and density-matrix probes."],
            "risks": ["No primitive thermal-bath assumptions."],
        },
        "ENTROPY_LENS_MUTUAL": {
            "claims": ["Drive entropy/correlation through cuts, partial traces, and trajectory terms."],
            "risks": ["No classical probability collapse."],
        },
        "ENGINE_LENS_SZILARD_CARNOT": {
            "claims": [
                "Treat engine narratives as overlays only; ratchet QIT witnesses and probeable terms only.",
                "Convert likely classical assumptions into explicit adversarial negatives.",
            ],
            "risks": ["No temperature/time primitive inside positive lanes."],
        },
    }

    written: list[Path] = []
    for role, tpl in role_templates.items():
        obj = {
            "schema": "A1_LAWYER_MEMO_v1",
            "run_id": str(run_id),
            "sequence": int(sequence),
            "role": str(role),
            "claims": list(tpl.get("claims", [])),  # type: ignore[arg-type]
            "risks": list(tpl.get("risks", [])),  # type: ignore[arg-type]
            "proposed_terms": list(base_terms),
            "proposed_negative_classes": list(neg_role_map.get(role, ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"])),
            "graveyard_rescue_targets": list(rescue_targets),
        }
        path = memo_drop_dir / f"{sequence:06d}_MEMO_{role}__{stamp}__AUTOFILL.json"
        path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _cycle_once(
    *,
    run_id: str,
    runs_root: Path,
    a2_state_dir: Path,
    preset: str,
    fuel_max_bytes: int,
    debate_mode: str,
    strategy_track: str,
    goal_selection: str,
    memo_drop_dir: Path,
    memo_consumed_dir: Path,
    stop_caps: _StopCaps | None,
) -> dict:
    run_dir = runs_root / run_id
    if stop_caps and stop_caps.max_run_mb > 0:
        size_mb = _dir_size_bytes(run_dir) / (1024.0 * 1024.0)
        if size_mb > float(stop_caps.max_run_mb):
            return {
                "schema": "A1_ENTROPY_ENGINE_CYCLE_RESULT_v1",
                "run_id": run_id,
                "sequence": 0,
                "status": "STOPPED__RUN_SIZE_CAP",
                "run_size_mb": size_mb,
                "max_run_mb": float(stop_caps.max_run_mb),
            }
    sandbox = run_dir / "a1_sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)

    pending_path = sandbox / "pending_cycle.json"
    pack_result: dict
    sequence: int
    if pending_path.exists():
        pending = _read_json(pending_path)
        if isinstance(pending, dict) and str(pending.get("preset", "")) == str(preset):
            pack_result = dict(pending.get("pack_result", {}) or {})
            sequence = int(pending.get("sequence", 0) or 0)
        else:
            pack_result = {}
            sequence = 0
    else:
        pack_result = {}
        sequence = 0

    if sequence <= 0 or not pack_result:
        pack_raw = _run_cmd(
            [
                "python3",
                str(LAWYER_PACK),
                "--run-id",
                run_id,
                "--preset",
                preset,
                "--fuel-max-bytes",
                str(int(fuel_max_bytes)),
                "--runs-root",
                str(runs_root),
                "--a2-state-dir",
                str(a2_state_dir),
            ],
            cwd=REPO,
        )
        pack_result = json.loads(pack_raw)
        sequence = _discover_sequence_from_pack(pack_result)
        if sequence <= 0:
            raise SystemExit("failed to discover sequence from lawyer pack")
        pending_path.write_text(
            json.dumps(
                {
                    "schema": "A1_PENDING_CYCLE_v1",
                    "run_id": run_id,
                    "preset": str(preset),
                    "sequence": int(sequence),
                    "pack_result": pack_result,
                    "required_roles": sorted(_required_roles_for_preset(preset)),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

    memo_drop_dir.mkdir(parents=True, exist_ok=True)
    memo_consumed_dir.mkdir(parents=True, exist_ok=True)

    # Ingest all available memo files for this cycle.
    required = _required_roles_for_preset(preset)
    ingested_roles: set[str] = set()
    ingested_paths: list[str] = []
    rejected_paths: list[str] = []
    rejected_gate_reports: list[dict] = []

    candidates = sorted(
        [p for p in memo_drop_dir.glob("*.json") if p.is_file() and not p.name.startswith(".")],
        key=lambda p: p.name,
    )
    for path in candidates:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(obj, dict) or str(obj.get("schema", "")).strip() != "A1_LAWYER_MEMO_v1":
            continue
        try:
            if int(obj.get("sequence", 0)) != int(sequence):
                continue
        except Exception:
            continue
        role = str(obj.get("role", "")).strip().upper()
        if not role:
            continue
        if bool(getattr(_cycle_once, "_memo_quality_gate", True)):
            gate_cmd = [
                "python3",
                str(MEMO_QUALITY_GATE),
                "--input-json",
                str(path),
                "--min-overall",
                str(float(getattr(_cycle_once, "_memo_quality_min_overall", 0.70))),
                "--min-role-compliance",
                str(float(getattr(_cycle_once, "_memo_quality_min_role_compliance", 0.60))),
                "--min-term-specificity",
                str(float(getattr(_cycle_once, "_memo_quality_min_term_specificity", 0.50))),
                "--min-negative-class-specificity",
                str(float(getattr(_cycle_once, "_memo_quality_min_negative_class_specificity", 0.60))),
                "--min-rescue-specificity",
                str(float(getattr(_cycle_once, "_memo_quality_min_rescue_specificity", 0.40))),
                "--min-classical-boundary-explicitness",
                str(float(getattr(_cycle_once, "_memo_quality_min_classical_boundary_explicitness", 0.60))),
            ]
            try:
                proc = subprocess.run(gate_cmd, cwd=str(REPO), check=False, capture_output=True, text=True)
                gate_payload = (proc.stdout or "").strip() or (proc.stderr or "").strip()
                gate_obj = json.loads(gate_payload) if gate_payload else {}
                if not isinstance(gate_obj, dict):
                    gate_obj = {}
                if int(proc.returncode) != 0 and "status" not in gate_obj:
                    gate_obj = {
                        "schema": "A1_MEMO_QUALITY_GATE_RESULT_v1",
                        "status": "FAIL",
                        "failures": [f"gate_returncode_{int(proc.returncode)}"],
                    }
            except Exception:
                gate_obj = {
                    "schema": "A1_MEMO_QUALITY_GATE_RESULT_v1",
                    "status": "FAIL",
                    "failures": ["gate_execution_failed"],
                }
            if str(gate_obj.get("status", "")).upper() != "PASS":
                rejected_paths.append(str(path))
                rejected_gate_reports.append({"path": str(path), "report": gate_obj})
                continue
        _run_cmd(
            ["python3", str(LAWYER_SINK), "--run-id", run_id, "--runs-root", str(runs_root), "--input-json", str(path)],
            cwd=REPO,
        )
        ingested_roles.add(role)
        ingested_paths.append(str(path))
        shutil.move(str(path), str(memo_consumed_dir / path.name))

    missing = sorted(required - ingested_roles)
    if missing:
        if preset in {"entropy_lenses7", "graveyard13"} and str(goal_selection) and str(debate_mode) and str(strategy_track):
            # Optional deterministic autofill (no-LLM) to keep campaigns moving.
            # Focus on terms that have real SIM probes and are likely next needed in QIT substrate closure.
            focus = [
                "measurement_operator",
                "observable_operator",
                "projector_operator",
                "pauli_operator",
                "bloch_sphere",
                "hopf_fibration",
                "hopf_torus",
                "berry_flux",
                "spinor_double_cover",
                "left_weyl_spinor",
                "right_weyl_spinor",
                "left_action_superoperator",
                "right_action_superoperator",
                "noncommutative_composition_order",
                "lindblad_generator",
                "liouvillian_superoperator",
                "kraus_representation",
                "density_purity",
                "density_entropy",
                "von_neumann_entropy",
                "coherence_decoherence",
                "left_right_action_entropy_production_rate_orthogonality",
                "variance_order_trajectory_correlation_orthogonality",
                "channel_realization_correlation_polarity_orthogonality",
                "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
                "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
                "channel_realization",
                "information_work_extraction_bound",
                "erasure_channel_entropy_cost_lower_bound",
            ]
            # Only autofill if enabled via env flag; CLI sets this below.
            if bool(getattr(_cycle_once, "_autofill", False)):
                if preset == "graveyard13":
                    _autofill_graveyard13_memos(
                        run_id=run_id,
                        sequence=sequence,
                        run_dir=run_dir,
                        memo_drop_dir=memo_drop_dir,
                        focus_terms=focus,
                    )
                else:
                    _autofill_entropy_lenses7_memos(
                        run_id=run_id,
                        sequence=sequence,
                        run_dir=run_dir,
                        memo_drop_dir=memo_drop_dir,
                        focus_terms=focus,
                    )
                # Re-run once, now that memos exist.
                return _cycle_once(
                    run_id=run_id,
                    runs_root=runs_root,
                    a2_state_dir=a2_state_dir,
                    preset=preset,
                    fuel_max_bytes=fuel_max_bytes,
                    debate_mode=debate_mode,
                    strategy_track=strategy_track,
                    goal_selection=goal_selection,
                    memo_drop_dir=memo_drop_dir,
                    memo_consumed_dir=memo_consumed_dir,
                    stop_caps=stop_caps,
                )
        return {
            "schema": "A1_ENTROPY_ENGINE_CYCLE_RESULT_v1",
            "run_id": run_id,
            "sequence": sequence,
            "status": "WAITING_FOR_MEMOS",
            "missing_roles": missing,
            "prompt_paths": list(pack_result.get("prompt_paths", [])),
            "memo_drop_dir": str(memo_drop_dir),
            "memo_consumed_dir": str(memo_consumed_dir),
            "ingested_roles": sorted(ingested_roles),
            "ingested_paths": ingested_paths,
            "rejected_paths": rejected_paths,
            "rejected_gate_reports": rejected_gate_reports,
        }

    min_corroboration = int(getattr(_cycle_once, "_min_corroboration", 2))
    strip_raw = _run_cmd(
        [
            "python3",
            str(COLD_CORE_STRIP),
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--sequence",
            str(sequence),
            "--min-corroboration",
            str(max(1, min_corroboration)),
        ],
        cwd=REPO,
    )
    strip_result = json.loads(strip_raw)
    cold_core_path = Path(str(strip_result.get("out", "")).strip())
    if not cold_core_path.exists():
        raise SystemExit("cold core strip did not produce output")

    try:
        select_cmd = [
            "python3",
            str(PACK_SELECTOR),
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--cold-core",
            str(cold_core_path),
            "--sequence",
            str(sequence),
            "--track",
            str(strategy_track),
            "--debate-mode",
            str(debate_mode),
            "--goal-selection",
            str(goal_selection),
            "--graveyard-fill-policy",
            str(getattr(_cycle_once, "_graveyard_fill_policy", "anchor_replay")),
            "--graveyard-library-terms",
            str(getattr(_cycle_once, "_graveyard_library_terms_csv", "")),
        ]
        pack_selector_max_terms = int(getattr(_cycle_once, "_pack_selector_max_terms", 0))
        if pack_selector_max_terms > 0:
            select_cmd.extend(["--max-terms", str(pack_selector_max_terms)])
        if bool(getattr(_cycle_once, "_forbid_rescue_in_graveyard_first", False)) and str(debate_mode) == "graveyard_first":
            select_cmd.append("--forbid-rescue-in-graveyard-first")
        select_raw = _run_cmd(select_cmd, cwd=REPO)
    except subprocess.CalledProcessError as exc:
        # Fail closed but do not crash the whole campaign. This can happen when
        # all proposed terms are already canonical and debate_mode isn't recovery.
        return {
            "schema": "A1_ENTROPY_ENGINE_CYCLE_RESULT_v1",
            "run_id": run_id,
            "sequence": sequence,
            "status": "STOPPED__PACK_SELECTOR_FAILED",
            "cold_core_path": str(cold_core_path),
            "cmd": exc.cmd,
            "stdout": (exc.output or "").strip(),
        }
    select_result = json.loads(select_raw)
    strategy_path = Path(str(select_result.get("out", "")).strip())
    if not strategy_path.exists():
        raise SystemExit("pack selector did not produce strategy output")

    # Do NOT force packet sequence to match sandbox sequence. Packet sequence must follow
    # ZIP_PROTOCOL_v2 monotone sequence for (run_id, source_layer), which is tracked
    # in a1_inbox/sequence_state.json and starts at 1.
    packet_raw = _run_cmd(
        ["python3", str(PACKETIZE), "--run-id", run_id, "--runs-root", str(runs_root), "--strategy-json", str(strategy_path)],
        cwd=REPO,
    )
    packet_result = json.loads(packet_raw)

    runner_raw = _run_cmd(
        ["python3", str(RUNNER), "--a1-source", "packet", "--run-id", run_id, "--steps", "1", "--runs-root", str(runs_root)],
        cwd=BOOTPACK,
    )
    summary = _read_json(run_dir / "summary.json")
    state = _read_json(run_dir / "state.json")
    # Fail closed if the runner did not actually consume a strategy packet.
    # This typically indicates ZIP sequence mismatch or packet validation failure.
    unique_strat = int(summary.get("unique_strategy_digest_count", 0) or 0)
    if unique_strat <= 0:
        return {
            "schema": "A1_ENTROPY_ENGINE_CYCLE_RESULT_v1",
            "run_id": run_id,
            "sequence": sequence,
            "status": "A1_PACKET_NOT_CONSUMED",
            "prompt_paths": list(pack_result.get("prompt_paths", [])),
            "cold_core_path": str(cold_core_path),
            "strategy_path": str(strategy_path),
            "packet_path": str(packet_result.get("out", "")),
            "runner_last_line": runner_raw.splitlines()[-1] if runner_raw else "",
            "summary": summary,
        }
    pending_path.unlink(missing_ok=True)

    # Prune high-entropy sandbox surfaces to prevent run bloat.
    # ZIP packets remain the canonical journal; these sandbox artifacts are only
    # for debugging / optional LLM interaction.
    keep_prompt_queue = int(getattr(_cycle_once, "_prune_keep_prompt_queue", 6))
    keep_lawyer_memos = int(getattr(_cycle_once, "_prune_keep_lawyer_memos", 48))
    keep_incoming_drop = int(getattr(_cycle_once, "_prune_keep_incoming_drop", 24))
    keep_incoming_consumed = int(getattr(_cycle_once, "_prune_keep_incoming_consumed", 48))
    keep_cold_core = int(getattr(_cycle_once, "_prune_keep_cold_core", 48))
    keep_outgoing = int(getattr(_cycle_once, "_prune_keep_outgoing", 24))
    keep_failed_packets = int(getattr(_cycle_once, "_prune_keep_failed_packets", 40))
    keep_external_exchange = int(getattr(_cycle_once, "_prune_keep_external_exchange", 72))

    prune_report = {
        # Prompts are reproducible from state + fuel; keep only a small tail.
        "prompt_queue": _prune_dir_keep_last(sandbox / "prompt_queue", keep_last=max(1, keep_prompt_queue)),
        "lawyer_memos": _prune_dir_keep_last(sandbox / "lawyer_memos", keep_last=max(1, keep_lawyer_memos)),
        "incoming_drop": _prune_dir_keep_last(sandbox / "incoming_drop", keep_last=max(1, keep_incoming_drop)),
        "incoming_consumed": _prune_dir_keep_last(
            sandbox / "incoming_consumed", keep_last=max(1, keep_incoming_consumed)
        ),
        "cold_core": _prune_dir_keep_last(sandbox / "cold_core", keep_last=max(1, keep_cold_core)),
        "outgoing": _prune_dir_keep_last(sandbox / "outgoing", keep_last=max(1, keep_outgoing)),
        "failed_packets": _prune_dir_keep_last(sandbox / "failed_packets", keep_last=max(1, keep_failed_packets)),
        "external_memo_exchange_requests": _prune_dir_keep_last(
            sandbox / "external_memo_exchange" / "requests",
            keep_last=max(1, keep_external_exchange),
        ),
    }

    return {
        "schema": "A1_ENTROPY_ENGINE_CYCLE_RESULT_v1",
        "run_id": run_id,
        "sequence": sequence,
        "status": "STEP_EXECUTED",
        "prompt_paths": list(pack_result.get("prompt_paths", [])),
        "cold_core_path": str(cold_core_path),
        "strategy_path": str(strategy_path),
        "packet_path": str(packet_result.get("out", "")),
        "runner_last_line": runner_raw.splitlines()[-1] if runner_raw else "",
        "summary": summary,
        "strategy_rescue_from_fields": _count_rescue_from_fields(strategy_path),
        "strategy_target_probe_terms": _strategy_target_probe_terms(strategy_path),
        "rejected_paths": rejected_paths,
        "rejected_gate_reports": rejected_gate_reports,
        "sandbox_prune": prune_report,
        "state_counts": {
            "canonical_term_count": sum(
                1
                for row in (state.get("term_registry", {}) or {}).values()
                if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED"
            ),
            "graveyard_count": len(state.get("graveyard", {}) or {}),
            "kill_log_count": len(state.get("kill_log", []) or []),
            "park_set_count": len(state.get("park_set", {}) or {}),
            "sim_registry_count": len(state.get("sim_registry", {}) or {}),
        },
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Automate the mechanical A1 sandbox -> strategy -> packet -> step loop.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT), help="Override A2 state dir used for A1 prompt fuel.")
    ap.add_argument("--preset", choices=["lawyer4", "entropy_lenses7", "graveyard13"], default="graveyard13")
    ap.add_argument("--fuel-max-bytes", type=int, default=60_000)
    ap.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="graveyard_first")
    ap.add_argument(
        "--debate-strategy",
        choices=["fixed", "graveyard_then_recovery"],
        default="graveyard_then_recovery",
        help="fixed uses --debate-mode for all cycles; graveyard_then_recovery fills graveyard first then rescue.",
    )
    ap.add_argument("--graveyard-fill-cycles", type=int, default=10)
    ap.add_argument(
        "--graveyard-fill-max-stall-cycles",
        type=int,
        default=2,
        help=(
            "When debate-strategy=graveyard_then_recovery, automatically transition to "
            "graveyard_recovery after this many weak graveyard-fill cycles."
        ),
    )
    ap.add_argument("--track", default="ENGINE_ENTROPY_EXPLORATION")
    ap.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="closure_first")
    ap.add_argument("--max-cycles", type=int, default=200)
    ap.add_argument("--memo-drop-dir", default="", help="Directory to watch for memo JSON drops for the current sequence.")
    ap.add_argument(
        "--autofill-memos",
        action="store_true",
        help="If set, auto-generate deterministic role memos when missing, so the campaign can run unattended (no external LLM).",
    )
    ap.add_argument(
        "--graveyard-fill-min-delta",
        type=int,
        default=1,
        help="During graveyard-fill cycles, fail if graveyard growth in a cycle is below this delta.",
    )
    ap.add_argument(
        "--graveyard-fill-max-canonical-delta",
        type=int,
        default=2,
        help="During graveyard-fill cycles, fail if canonical growth in a cycle exceeds this delta.",
    )
    ap.add_argument(
        "--recovery-min-rescue-from-fields",
        type=int,
        default=1,
        help="During recovery cycles, fail if emitted strategy has fewer RESCUE_FROM fields than this threshold.",
    )
    ap.add_argument(
        "--graveyard-fill-policy",
        choices=["anchor_replay", "fuel_full_load"],
        default="anchor_replay",
        help="How graveyard_first mode selects terms: anchor replay (legacy) or full fuel loading first.",
    )
    ap.add_argument(
        "--forbid-rescue-during-graveyard-fill",
        action="store_true",
        help="If set, strip RESCUE_FROM fields while debate_mode=graveyard_first.",
    )
    ap.add_argument(
        "--pack-selector-max-terms",
        type=int,
        default=0,
        help="Optional override for max term goals selected per strategy.",
    )
    ap.add_argument(
        "--graveyard-library-terms",
        default="",
        help="Comma-separated terms treated as graveyard-library only (never rescued in recovery mode).",
    )
    ap.add_argument(
        "--max-run-mb",
        type=float,
        default=50.0,
        help="Stop the campaign if the run directory exceeds this size in MB. Set <=0 to disable.",
    )
    ap.add_argument("--memo-quality-gate", dest="memo_quality_gate", action="store_true", default=True)
    ap.add_argument("--no-memo-quality-gate", dest="memo_quality_gate", action="store_false")
    ap.add_argument("--memo-quality-min-overall", type=float, default=0.70)
    ap.add_argument("--memo-quality-min-role-compliance", type=float, default=0.60)
    ap.add_argument("--memo-quality-min-term-specificity", type=float, default=0.50)
    ap.add_argument("--memo-quality-min-negative-class-specificity", type=float, default=0.60)
    ap.add_argument("--memo-quality-min-rescue-specificity", type=float, default=0.40)
    ap.add_argument("--memo-quality-min-classical-boundary-explicitness", type=float, default=0.60)
    ap.add_argument(
        "--prune-keep-prompt-queue",
        type=int,
        default=6,
        help="Keep this many prompt_queue files per run (high-entropy debug surface).",
    )
    ap.add_argument(
        "--prune-keep-lawyer-memos",
        type=int,
        default=48,
        help="Keep this many lawyer_memos files per run.",
    )
    ap.add_argument(
        "--prune-keep-incoming-drop",
        type=int,
        default=24,
        help="Keep this many incoming_drop memo files per run.",
    )
    ap.add_argument(
        "--prune-keep-incoming-consumed",
        type=int,
        default=48,
        help="Keep this many incoming_consumed memo files per run.",
    )
    ap.add_argument(
        "--prune-keep-cold-core",
        type=int,
        default=48,
        help="Keep this many cold_core proposal files per run.",
    )
    ap.add_argument(
        "--prune-keep-outgoing",
        type=int,
        default=24,
        help="Keep this many outgoing packet candidate files per run.",
    )
    ap.add_argument(
        "--prune-keep-failed-packets",
        type=int,
        default=40,
        help="Keep this many failed_packets files per run.",
    )
    ap.add_argument(
        "--prune-keep-external-exchange",
        type=int,
        default=72,
        help="Keep this many external memo exchange request/response files per run.",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("missing run-id")

    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    _init_run(run_id=run_id, runs_root=runs_root, clean=bool(args.clean))
    run_dir = runs_root / run_id
    sandbox_root = run_dir / "a1_sandbox"
    memo_drop_dir = Path(args.memo_drop_dir).expanduser().resolve() if str(args.memo_drop_dir).strip() else (sandbox_root / "incoming_drop")
    memo_consumed_dir = sandbox_root / "incoming_consumed"

    cycles: list[dict] = []
    stop_reason = "MAX_CYCLES_REACHED"
    stop_caps = _StopCaps(max_run_mb=float(args.max_run_mb))
    prev_state = _read_json(run_dir / "state.json")
    prev_graveyard = int(len(prev_state.get("graveyard", {}) or {})) if isinstance(prev_state, dict) else 0
    prev_canonical = (
        sum(
            1
            for row in (prev_state.get("term_registry", {}) or {}).values()
            if isinstance(row, dict) and str(row.get("state", "")) == "CANONICAL_ALLOWED"
        )
        if isinstance(prev_state, dict)
        else 0
    )
    graveyard_fill_stall_count = 0
    force_recovery = False
    for idx in range(1, int(args.max_cycles) + 1):
        if str(args.debate_strategy) == "graveyard_then_recovery":
            cycle_debate_mode = (
                "graveyard_recovery"
                if force_recovery or idx > int(args.graveyard_fill_cycles)
                else "graveyard_first"
            )
        else:
            cycle_debate_mode = str(args.debate_mode)
        cycle_min_corroboration = 1 if cycle_debate_mode == "graveyard_first" else 2
        # Thread a runtime flag through the function object to avoid widening the argument surface.
        setattr(_cycle_once, "_autofill", bool(args.autofill_memos))
        setattr(_cycle_once, "_min_corroboration", int(cycle_min_corroboration))
        setattr(_cycle_once, "_memo_quality_gate", bool(args.memo_quality_gate))
        setattr(_cycle_once, "_memo_quality_min_overall", float(args.memo_quality_min_overall))
        setattr(_cycle_once, "_memo_quality_min_role_compliance", float(args.memo_quality_min_role_compliance))
        setattr(_cycle_once, "_memo_quality_min_term_specificity", float(args.memo_quality_min_term_specificity))
        setattr(
            _cycle_once,
            "_memo_quality_min_negative_class_specificity",
            float(args.memo_quality_min_negative_class_specificity),
        )
        setattr(_cycle_once, "_memo_quality_min_rescue_specificity", float(args.memo_quality_min_rescue_specificity))
        setattr(
            _cycle_once,
            "_memo_quality_min_classical_boundary_explicitness",
            float(args.memo_quality_min_classical_boundary_explicitness),
        )
        setattr(_cycle_once, "_prune_keep_prompt_queue", int(args.prune_keep_prompt_queue))
        setattr(_cycle_once, "_prune_keep_lawyer_memos", int(args.prune_keep_lawyer_memos))
        setattr(_cycle_once, "_prune_keep_incoming_drop", int(args.prune_keep_incoming_drop))
        setattr(_cycle_once, "_prune_keep_incoming_consumed", int(args.prune_keep_incoming_consumed))
        setattr(_cycle_once, "_prune_keep_cold_core", int(args.prune_keep_cold_core))
        setattr(_cycle_once, "_prune_keep_outgoing", int(args.prune_keep_outgoing))
        setattr(_cycle_once, "_prune_keep_failed_packets", int(args.prune_keep_failed_packets))
        setattr(_cycle_once, "_prune_keep_external_exchange", int(args.prune_keep_external_exchange))
        setattr(_cycle_once, "_graveyard_fill_policy", str(args.graveyard_fill_policy))
        setattr(_cycle_once, "_forbid_rescue_in_graveyard_first", bool(args.forbid_rescue_during_graveyard_fill))
        setattr(_cycle_once, "_pack_selector_max_terms", int(args.pack_selector_max_terms))
        setattr(_cycle_once, "_graveyard_library_terms_csv", str(args.graveyard_library_terms))
        result = _cycle_once(
            run_id=run_id,
            runs_root=runs_root,
            a2_state_dir=a2_state_dir,
            preset=str(args.preset),
            fuel_max_bytes=int(args.fuel_max_bytes),
            debate_mode=str(cycle_debate_mode),
            strategy_track=str(args.track),
            goal_selection=str(args.goal_selection),
            memo_drop_dir=memo_drop_dir,
            memo_consumed_dir=memo_consumed_dir,
            stop_caps=stop_caps,
        )
        result["cycle_index"] = int(idx)
        result["cycle_debate_mode"] = str(cycle_debate_mode)
        result["cycle_min_corroboration"] = int(cycle_min_corroboration)
        current_graveyard = int((result.get("state_counts", {}) or {}).get("graveyard_count", prev_graveyard))
        graveyard_delta = current_graveyard - prev_graveyard
        result["cycle_graveyard_delta"] = int(graveyard_delta)
        prev_graveyard = current_graveyard
        current_canonical = int((result.get("state_counts", {}) or {}).get("canonical_term_count", prev_canonical))
        canonical_delta = current_canonical - prev_canonical
        result["cycle_canonical_delta"] = int(canonical_delta)
        prev_canonical = current_canonical
        if (
            str(result.get("status")) == "STEP_EXECUTED"
            and cycle_debate_mode == "graveyard_first"
            and int(args.graveyard_fill_min_delta) > 0
            and graveyard_delta < int(args.graveyard_fill_min_delta)
        ):
            graveyard_fill_stall_count += 1
            result["graveyard_fill_stall_count"] = int(graveyard_fill_stall_count)
            result["expected_min_graveyard_delta"] = int(args.graveyard_fill_min_delta)
            if str(args.debate_strategy) == "graveyard_then_recovery":
                if (
                    int(args.graveyard_fill_max_stall_cycles) >= 0
                    and graveyard_fill_stall_count > int(args.graveyard_fill_max_stall_cycles)
                ):
                    # Transition instead of hard-stop: once fill plateau is reached,
                    # keep the campaign moving into recovery/rescue behavior.
                    force_recovery = True
                    result["graveyard_fill_transition_to_recovery"] = True
            else:
                result["status"] = "STOPPED__GRAVEYARD_FILL_TOO_WEAK"
        elif cycle_debate_mode == "graveyard_first":
            graveyard_fill_stall_count = 0
        if (
            str(result.get("status")) == "STEP_EXECUTED"
            and cycle_debate_mode == "graveyard_first"
            and int(args.graveyard_fill_max_canonical_delta) >= 0
            and canonical_delta > int(args.graveyard_fill_max_canonical_delta)
        ):
            result["status"] = "STOPPED__GRAVEYARD_FILL_CANONICALIZING_TOO_FAST"
            result["expected_max_canonical_delta"] = int(args.graveyard_fill_max_canonical_delta)
        if (
            str(result.get("status")) == "STEP_EXECUTED"
            and cycle_debate_mode == "graveyard_recovery"
            and int(args.recovery_min_rescue_from_fields) > 0
            and current_graveyard >= 10
            and int(result.get("strategy_rescue_from_fields", 0)) < int(args.recovery_min_rescue_from_fields)
            and "qit_master_conjunction" not in set(result.get("strategy_target_probe_terms", []) or [])
        ):
            result["status"] = "STOPPED__RECOVERY_NOT_USING_RESCUE"
            result["expected_min_rescue_from_fields"] = int(args.recovery_min_rescue_from_fields)
        cycles.append(result)
        if str(result.get("status")) != "STEP_EXECUTED":
            stop_reason = str(result.get("status"))
            break

    report = {
        "schema": "A1_ENTROPY_ENGINE_CAMPAIGN_REPORT_v1",
        "run_id": run_id,
        "preset": str(args.preset),
        "track": str(args.track),
        "debate_mode": str(args.debate_mode),
        "debate_strategy": str(args.debate_strategy),
        "graveyard_fill_cycles": int(args.graveyard_fill_cycles),
        "graveyard_fill_min_delta": int(args.graveyard_fill_min_delta),
        "graveyard_fill_max_canonical_delta": int(args.graveyard_fill_max_canonical_delta),
        "recovery_min_rescue_from_fields": int(args.recovery_min_rescue_from_fields),
        "memo_quality_gate": bool(args.memo_quality_gate),
        "memo_quality_min_overall": float(args.memo_quality_min_overall),
        "fuel_max_bytes": int(args.fuel_max_bytes),
        "max_cycles": int(args.max_cycles),
        "cycles_executed": sum(1 for c in cycles if c.get("status") == "STEP_EXECUTED"),
        "stop_reason": stop_reason,
        "memo_drop_dir": str(memo_drop_dir),
        "cycles": cycles,
    }
    out = run_dir / "reports" / "a1_entropy_engine_campaign_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": report["schema"], "out": str(out), "stop_reason": stop_reason}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
