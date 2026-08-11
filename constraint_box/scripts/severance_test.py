"""Severance harness: dependency admission earned by removal, per dependency.

For one named dependency this harness:
  1. runs a REAL run-path CB operation in a fresh subprocess with the
     dependency importable (present);
  2. runs the SAME operation in a second fresh subprocess where a meta-path
     import blocker makes ``import <name>`` raise ModuleNotFoundError (with
     ``name`` set, exactly as a genuine absence would) BEFORE any constraintbox
     module is imported (severed);
  3. records disposition and reason codes for both runs;
  4. verdicts LOAD_BEARING only if the DECISION moved: a different enumerated
     disposition/verdict/signal/status, a new reason code, or a refusal where
     there was an admission.  Hashes and prose are excluded from the decision
     comparison by construction, so a receipt merely holding a different
     string can never count as a change;
  5. emits one receipt per dependency following gate_operations.py's
     execution-receipt shape (gate_id, input_sha256, output_sha256, verdict,
     reason), never a second receipt grammar.

Real operations exercised (no fixtures):
  z3-solver / cvc5  agentrun._smt_gate on the released run's observed gate
                    values (all nine boolean gates True, requested_claim ==
                    ALLOWED_CLAIM, as in the RELEASED run at
                    receipts/first_released_run_20260809): three dual_solve
                    calls on the run path's own FiniteConstraintProblem specs.
  rustworkx         proposal_minilev_flow._TOPOLOGY.evaluate on the real
                    reference_flow_policy() — the run path's own
                    FixedMiniLevTopology preflight.
  sympy             gate_operations.gate_sympy_flow_budgets on the real
                    reference_flow_policy() (cb:sympy-exact-gate, run-path
                    wiring).
  maude             gate_operations.gate_maude_flow_transitions on the real
                    reference_flow_policy() (cb:maude-transition-gate,
                    run-path wiring).

Known instrument limit (recorded in the maude receipt): the maude rewrite
itself executes in a ``sys.executable -I`` isolated worker subprocess that
re-imports maude independently.  The in-process blocker severs the
parent-process runtime-identity binding (maude_rewrite line ~230), which fails
closed to PARKED before any worker is spawned.  Exercising the worker's own
import-failure path would need a site-packages-level severance (environment
mutation), which this harness deliberately does not perform.

This harness ADDS a surface; it does not modify any existing gate, check,
bound, test, or CLI surface.

promotion_allowed: false.  Claim ceiling: severance of one import name on one
real run-path operation under this interpreter and environment.  LOAD_BEARING
means removal changed this operation's decision here; DECORATIVE means removal
changed nothing observable in this operation's decision here.  No platform,
resolver, or whole-suite claim.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

PINNED_PYTHON = (
    "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
)
CONSTRAINT_BOX_ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet/constraint_box")
SRC_ROOT = CONSTRAINT_BOX_ROOT / "src"
RECEIPT_DIR = CONSTRAINT_BOX_ROOT / "receipts" / "severance_v1"
RESULT_MARKER = "SEVERANCE_PROBE_RESULT_JSON="
SCHEMA = "constraintbox.severance-test.v1"
CLAIM_CEILING = (
    "severance of one import name on one real run-path operation under this "
    "interpreter and environment; LOAD_BEARING means removal changed this "
    "operation's decision here; no platform, resolver, or whole-suite claim"
)

# dependency (pyproject/distribution name) -> probe wiring
DEPENDENCIES: dict[str, dict[str, str]] = {
    "z3-solver": {
        "import_name": "z3",
        "probe": "smt",
        "operation": (
            "constraintbox.agentrun._smt_gate(observed) with the RELEASED "
            "run's gate values (all boolean gates True, requested_claim == "
            "ALLOWED_CLAIM): three dual_solve calls (proposal / "
            "hostile_overclaim / claim_constraint_erased_control) on the run "
            "path's own FiniteConstraintProblem specs"
        ),
    },
    "cvc5": {
        "import_name": "cvc5",
        "probe": "smt",
        "operation": (
            "constraintbox.agentrun._smt_gate(observed) with the RELEASED "
            "run's gate values (all boolean gates True, requested_claim == "
            "ALLOWED_CLAIM): three dual_solve calls (proposal / "
            "hostile_overclaim / claim_constraint_erased_control) on the run "
            "path's own FiniteConstraintProblem specs"
        ),
    },
    "sympy": {
        "import_name": "sympy",
        "probe": "sympy",
        "operation": (
            "constraintbox.gate_operations.gate_sympy_flow_budgets("
            "proposal_minilev_flow.reference_flow_policy()) — "
            "cb:sympy-exact-gate run-path wiring on the real FlowPolicy"
        ),
    },
    "rustworkx": {
        "import_name": "rustworkx",
        "probe": "topology",
        "operation": (
            "constraintbox.proposal_minilev_flow._TOPOLOGY.evaluate("
            "reference_flow_policy(), run_dir) — the run path's own "
            "FixedMiniLevTopology rustworkx preflight"
        ),
    },
    "maude": {
        "import_name": "maude",
        "probe": "maude",
        "operation": (
            "constraintbox.gate_operations.gate_maude_flow_transitions("
            "proposal_minilev_flow.reference_flow_policy()) — "
            "cb:maude-transition-gate run-path wiring on the real FlowPolicy"
        ),
    },
}

PROBE_TIMEOUT_SECONDS = 900


# ---------------------------------------------------------------------------
# Child-side: the severance instrument and the real operations.
# ---------------------------------------------------------------------------


class _SeveranceFinder:
    """Meta-path finder that refuses exactly one top-level module name.

    Raises ModuleNotFoundError with ``name`` set, exactly as a genuine
    absence from the environment would, so every existing
    ``except ModuleNotFoundError ... exc.name == <name>`` fail-closed branch
    in the package fires on its real path.
    """

    def __init__(self, blocked: str) -> None:
        self.blocked = blocked

    def find_spec(self, fullname: str, path=None, target=None):  # noqa: ANN001
        if fullname == self.blocked or fullname.startswith(self.blocked + "."):
            raise ModuleNotFoundError(
                f"No module named {fullname!r} (severed by severance_test)",
                name=fullname,
            )
        return None


def _install_severance(import_name: str) -> None:
    for key in list(sys.modules):
        if key == import_name or key.startswith(import_name + "."):
            del sys.modules[key]
    sys.meta_path.insert(0, _SeveranceFinder(import_name))


def _severance_control(import_name: str, mode: str) -> dict[str, Any]:
    """Negative/positive control on the instrument itself, not the operation."""

    try:
        spec = importlib.util.find_spec(import_name)
        importable = spec is not None
        error = None
    except ModuleNotFoundError as exc:
        importable = False
        error = f"{type(exc).__name__}: {exc}"
    if mode == "severed":
        return {"severance_confirmed": not importable, "control_error": error}
    return {"dependency_present_confirmed": importable, "control_error": error}


def _smt_decision(smt: dict[str, Any]) -> dict[str, Any]:
    decision: dict[str, Any] = {
        "settled": smt.get("settled"),
        "proposal_admitted": smt.get("proposal_admitted"),
    }
    for key in (
        "proposal",
        "hostile_overclaim",
        "claim_constraint_erased_control",
    ):
        row = smt.get(key)
        if not isinstance(row, dict):
            decision[f"{key}.missing"] = True
            continue
        decision[f"{key}.agrees"] = row.get("agrees")
        for backend in ("z3", "cvc5", "enumeration"):
            backend_row = row.get(backend)
            if isinstance(backend_row, dict):
                decision[f"{key}.{backend}.status"] = backend_row.get("status")
                decision[f"{key}.{backend}.reason"] = backend_row.get("reason")
        disagreement = row.get("disagreement")
        decision[f"{key}.disagreement_reason"] = (
            disagreement.get("reason") if isinstance(disagreement, dict) else None
        )
    return decision


def _probe_smt() -> tuple[dict[str, Any], dict[str, Any], str, str]:
    from constraintbox.agentrun import ALLOWED_CLAIM, _BOOLEAN_GATES, _smt_gate

    observed: dict[str, Any] = {name: True for name in _BOOLEAN_GATES}
    observed["requested_claim"] = ALLOWED_CLAIM
    smt = _smt_gate(observed)
    decision = _smt_decision(smt)
    if smt.get("settled") and smt.get("proposal_admitted"):
        verdict = "SETTLED"
        reason = "three_way_agreement_on_all_three_specs"
    else:
        verdict = "NOT_SETTLED"
        reasons = sorted(
            {
                value
                for key, value in decision.items()
                if key.endswith("disagreement_reason") and value
            }
        )
        reason = (
            "disagreement:" + ",".join(reasons)
            if reasons
            else "not_settled_without_disagreement_reason"
        )
    return decision, smt, verdict, reason


def _probe_topology() -> tuple[dict[str, Any], dict[str, Any], str, str]:
    from constraintbox.proposal_minilev_flow import (
        _TOPOLOGY,
        reference_flow_policy,
    )

    run_dir = Path(tempfile.mkdtemp(prefix="severance_topology_"))
    preflight = _TOPOLOGY.evaluate(reference_flow_policy(), run_dir)
    outcome = preflight.profile_outcome
    decision = {
        "signal": preflight.signal.value,
        "disposition": outcome.get("disposition"),
        "reason": outcome.get("reason"),
        "evaluation_executed": preflight.evaluation_executed,
    }
    raw = {
        "projection": preflight.projection,
        "projection_sha256": preflight.projection_sha256,
        "profile_outcome": outcome,
        "evaluation_executed": preflight.evaluation_executed,
        "signal": preflight.signal.value,
    }
    return decision, raw, preflight.signal.value, str(outcome.get("reason"))


def _probe_formal_gate(
    gate_name: str,
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    from constraintbox import gate_operations
    from constraintbox.proposal_minilev_flow import reference_flow_policy

    gate = getattr(gate_operations, gate_name)
    execution = gate(reference_flow_policy())
    decision = {"verdict": execution.verdict, "reason": execution.reason}
    raw = {
        "gate_id": execution.gate_id,
        "input_sha256": execution.input_sha256,
        "output_sha256": execution.output_sha256,
        "verdict": execution.verdict,
        "reason": execution.reason,
    }
    return decision, raw, execution.verdict, execution.reason


def _run_probe(dependency: str, mode: str) -> dict[str, Any]:
    wiring = DEPENDENCIES[dependency]
    import_name = wiring["import_name"]
    result: dict[str, Any] = {
        "dependency": dependency,
        "import_name": import_name,
        "mode": mode,
        "probe": wiring["probe"],
        "operation": wiring["operation"],
    }
    if mode == "severed":
        _install_severance(import_name)
    result["instrument_control"] = _severance_control(import_name, mode)

    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

    started = time.monotonic()
    try:
        if wiring["probe"] == "smt":
            decision, raw, verdict, reason = _probe_smt()
        elif wiring["probe"] == "topology":
            decision, raw, verdict, reason = _probe_topology()
        elif wiring["probe"] == "sympy":
            decision, raw, verdict, reason = _probe_formal_gate(
                "gate_sympy_flow_budgets"
            )
        elif wiring["probe"] == "maude":
            decision, raw, verdict, reason = _probe_formal_gate(
                "gate_maude_flow_transitions"
            )
        else:
            raise ValueError(f"unknown probe {wiring['probe']!r}")
        result["decision"] = decision
        result["raw"] = raw
        result["operation_verdict"] = verdict
        result["operation_reason"] = reason
        result["refusal"] = None
    except BaseException as exc:  # noqa: BLE001 - a refusal is data, not a crash
        result["decision"] = {"refusal": type(exc).__name__}
        result["raw"] = {
            "refusal_type": type(exc).__name__,
            "refusal_message": str(exc)[:2048],
        }
        result["operation_verdict"] = "REFUSED"
        result["operation_reason"] = f"operation_refused:{type(exc).__name__}"
        result["refusal"] = type(exc).__name__
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


# ---------------------------------------------------------------------------
# Parent-side: subprocess orchestration, comparison, receipts.
# ---------------------------------------------------------------------------


def _sha256_canonical(material: Any) -> str:
    """Prefer the package's strict canonical JSON; fall back with a flag."""

    try:
        sys.path.insert(0, str(SRC_ROOT))
        from constraintbox.intake import canonical_json

        return hashlib.sha256(canonical_json(material)).hexdigest()
    except Exception:
        rendered = json.dumps(
            material, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
        return hashlib.sha256(rendered).hexdigest()


def _spawn_probe(dependency: str, mode: str) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_ROOT)
    command = [
        PINNED_PYTHON,
        str(Path(__file__).resolve()),
        "--probe",
        dependency,
        "--mode",
        mode,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=env,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "probe_transport": "TIMEOUT",
            "returncode": None,
            "stderr_tail": "",
        }
    payload: dict[str, Any] | None = None
    for line in completed.stdout.splitlines():
        if line.startswith(RESULT_MARKER):
            try:
                payload = json.loads(line[len(RESULT_MARKER):])
            except json.JSONDecodeError:
                payload = None
    record: dict[str, Any] = {
        "probe_transport": "OK" if payload is not None else "NO_RESULT",
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-2000:],
    }
    if payload is not None:
        record.update(payload)
    # A nonzero exit code is never a quiet negative: surface it explicitly.
    if completed.returncode != 0:
        record["probe_transport"] = "NONZERO_EXIT"
    return record


def _execution_record(
    gate_id: str,
    input_material: Any,
    output_material: Any,
    verdict: str,
    reason: str,
) -> dict[str, Any]:
    """gate_operations.GateExecution shape, verbatim field set."""

    return {
        "gate_id": gate_id,
        "input_sha256": _sha256_canonical(input_material),
        "output_sha256": _sha256_canonical(output_material),
        "verdict": verdict,
        "reason": reason,
    }


def _compare(dependency: str) -> dict[str, Any]:
    wiring = DEPENDENCIES[dependency]
    present = _spawn_probe(dependency, "present")
    severed = _spawn_probe(dependency, "severed")

    input_material = {
        "dependency": dependency,
        "import_name": wiring["import_name"],
        "operation": wiring["operation"],
        "severance_mechanism": (
            "meta_path_module_not_found_installed_before_constraintbox_import"
        ),
    }

    decision_present = present.get("decision")
    decision_severed = severed.get("decision")
    instrument_present = present.get("instrument_control", {})
    instrument_severed = severed.get("instrument_control", {})

    inconclusive_reasons: list[str] = []
    if present.get("probe_transport") != "OK":
        inconclusive_reasons.append(
            f"present_probe_{present.get('probe_transport')}"
            f"_rc={present.get('returncode')}"
        )
    if severed.get("probe_transport") != "OK":
        inconclusive_reasons.append(
            f"severed_probe_{severed.get('probe_transport')}"
            f"_rc={severed.get('returncode')}"
        )
    if instrument_present.get("dependency_present_confirmed") is not True:
        inconclusive_reasons.append("dependency_not_importable_at_baseline")
    if instrument_severed.get("severance_confirmed") is not True:
        inconclusive_reasons.append("severance_not_confirmed_by_control")

    decision_moved: bool | None = None
    delta: list[str] = []
    if not inconclusive_reasons and isinstance(decision_present, dict) and isinstance(
        decision_severed, dict
    ):
        keys = sorted(set(decision_present) | set(decision_severed))
        delta = [
            key
            for key in keys
            if decision_present.get(key) != decision_severed.get(key)
        ]
        decision_moved = bool(delta)

    if inconclusive_reasons:
        verdict = "INCONCLUSIVE"
        reason = ";".join(inconclusive_reasons)
    elif decision_moved:
        verdict = "LOAD_BEARING"
        reason = f"decision_moved:{len(delta)}_fields"
    else:
        verdict = "DECORATIVE"
        reason = "decision_unchanged_under_severance"

    executions = [
        _execution_record(
            f"cb:severance-test:{dependency}:present",
            input_material,
            present,
            str(present.get("operation_verdict", "UNAVAILABLE")),
            str(present.get("operation_reason", "probe_result_unavailable")),
        ),
        _execution_record(
            f"cb:severance-test:{dependency}:severed",
            input_material,
            severed,
            str(severed.get("operation_verdict", "UNAVAILABLE")),
            str(severed.get("operation_reason", "probe_result_unavailable")),
        ),
        _execution_record(
            "cb:severance-test-gate",
            input_material,
            {"present": decision_present, "severed": decision_severed},
            verdict,
            reason,
        ),
    ]

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "dependency": dependency,
        "import_name": wiring["import_name"],
        "operation": wiring["operation"],
        "severance_mechanism": input_material["severance_mechanism"],
        "python_executable": PINNED_PYTHON,
        "executions": executions,
        "present": present,
        "severed": severed,
        "decision_present": decision_present,
        "decision_severed": decision_severed,
        "decision_moved": decision_moved,
        "decision_delta": delta,
        "verdict": verdict,
        "reason": reason,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    if dependency == "maude":
        receipt["instrument_limit"] = (
            "the maude rewrite executes in a sys.executable -I isolated "
            "worker that re-imports maude independently; this severance "
            "reaches the parent-process runtime-identity binding "
            "(maude_rewrite._controller_runtime_identity), which fails "
            "closed to PARKED before any worker is spawned; the worker's own "
            "import-failure path was NOT exercised (it would require "
            "site-packages mutation, deliberately not performed)"
        )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=sorted(DEPENDENCIES))
    parser.add_argument("--mode", choices=["present", "severed"])
    parser.add_argument(
        "--deps",
        nargs="*",
        default=sorted(DEPENDENCIES),
        help="dependencies to test (default: all five core tools)",
    )
    args = parser.parse_args()

    if args.probe:
        if not args.mode:
            raise SystemExit("--probe requires --mode")
        result = _run_probe(args.probe, args.mode)
        print(RESULT_MARKER + json.dumps(result, sort_keys=True, default=str))
        return 0

    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, Any]] = []
    for dependency in args.deps:
        started = time.monotonic()
        receipt = _compare(dependency)
        elapsed = round(time.monotonic() - started, 1)
        receipt_path = RECEIPT_DIR / f"severance_{dependency}.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n"
        )
        summary_rows.append(
            {
                "dependency": dependency,
                "verdict": receipt["verdict"],
                "reason": receipt["reason"],
                "operation_verdict_present": receipt["present"].get(
                    "operation_verdict"
                ),
                "operation_verdict_severed": receipt["severed"].get(
                    "operation_verdict"
                ),
                "decision_delta_count": len(receipt["decision_delta"]),
                "receipt": str(receipt_path),
                "elapsed_seconds": elapsed,
            }
        )
        print(
            f"{dependency:<10} {receipt['verdict']:<13} "
            f"present={receipt['present'].get('operation_verdict')}"
            f"/{receipt['present'].get('operation_reason')}  "
            f"severed={receipt['severed'].get('operation_verdict')}"
            f"/{receipt['severed'].get('operation_reason')}  "
            f"delta_fields={len(receipt['decision_delta'])}  "
            f"[{elapsed}s]"
        )

    summary = {
        "schema": SCHEMA + ".summary",
        "python_executable": PINNED_PYTHON,
        "rows": summary_rows,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    summary_path = RECEIPT_DIR / "severance_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(f"SUMMARY_RECEIPT={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
