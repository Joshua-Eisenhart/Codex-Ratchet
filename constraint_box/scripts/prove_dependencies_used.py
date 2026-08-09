#!/usr/bin/env python3
"""Prove by EXECUTION which declared dependencies ConstraintBox actually reaches.

Question answered: for every dependency declared in constraint_box/pyproject.toml
(hard dependencies plus the [test] extra), does a line of code INSIDE that
package execute while a REAL ConstraintBox operation runs?  Grep finds an
import statement; an import statement does not show the code ran; and an
import alone does not show the code was USED.  This harness therefore:

  1. pre-imports every declared dependency (and the ConstraintBox modules the
     operation needs) BEFORE measurement starts, so import-time module-body
     execution is excluded from the evidence window;
  2. then starts line coverage plus a native c_call profiler and drives the
     real operation;
  3. counts a dependency REACHED only on operation-phase evidence:
       - a line inside a FUNCTION BODY of the package executed (coverage +
         AST classification; module-body lines are reported separately and
         never suffice), or
       - a native (compiled) callable belonging to the package was invoked
         (sys.setprofile c_call), or
       - for the hermetic Maude worker (spawned with a scrubbed environment
         under `python -I`, so no tracer can reach it from outside), a
         settrace prelude is prepended to the byte-identical worker bootstrap
         at spawn time; maude-package call events with a real function name
         (not '<module>') count.

Driven operations (all real ConstraintBox surfaces, none synthetic):
  box_pipeline          run_first_box on fixtures/live_run_request_v1.json,
                        then the full agent run (_run_agent_for_test with a
                        deterministic offline provider at the documented
                        offline seam; every other component is production,
                        including the real ClaimGate chain).
  formal_flow_gates     gate_operations.run_formal_flow_gates on the
                        reference FlowPolicy (cb:sympy-exact-gate and
                        cb:maude-transition-gate, run-path wiring).
  dual_solve_smt_gate   agentrun._smt_gate on the run path's own observed
                        gate vector: three dual_solve executions (z3 + cvc5 +
                        exhaustive enumeration) on real FiniteConstraintProblems.
  mini_lev_topology     proposal_minilev_flow._TOPOLOGY.evaluate on the
                        reference FlowPolicy (the rustworkx preflight).
  gate_receipt          the pinned `gate <receipt>` CLI surface
                        (constraintbox.cli.main) against the real released
                        receipt receipts/first_released_run_20260809/run/
                        release_receipt.json.
  hypothesis_test_lane  (test-extra lane, reported separately) one real
                        adversarial suite, tests/test_hypothesis_adversarial.py.

This answers REACHABILITY only.  Whether removing a dependency CHANGES a
result is a different question answered by scripts/severance_test.py.

Claim ceiling: execution-reachability evidence about this checkout on this
host; no correctness, semantic, or promotion claim.  promotion_allowed: false.

Usage:
    python3 scripts/prove_dependencies_used.py            # full run
    python3 scripts/prove_dependencies_used.py --ops dual_solve_smt_gate
    python3 scripts/prove_dependencies_used.py --workdir /tmp/prove --keep
"""

from __future__ import annotations

import argparse
import ast
import datetime as _dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

CB_ROOT = Path(__file__).resolve().parents[1]
CB_SRC = CB_ROOT / "src"
FIXTURE_REQUEST = CB_ROOT / "fixtures" / "live_run_request_v1.json"
RELEASED_RECEIPT = (
    CB_ROOT
    / "receipts"
    / "first_released_run_20260809"
    / "run"
    / "release_receipt.json"
)
REGISTRY_PATH = CB_ROOT / "config" / "core_tool_registry_v9.json"
RECEIPT_OUT = CB_ROOT / "receipts" / "dependency_reachability_v1.json"
SCHEMA = "constraintbox.dependency-reachability-proof.v1"

# Fixed fallback for distribution -> import-name mapping; the live mapping is
# taken from importlib.metadata.packages_distributions() and the v9 registry,
# and this table is only consulted when both are silent.
_STATIC_IMPORT_NAMES = {
    "z3-solver": ["z3"],
    "cvc5": ["cvc5"],
    "sympy": ["sympy"],
    "rustworkx": ["rustworkx"],
    "maude": ["maude"],
    "hypothesis": ["hypothesis"],
}

_CB_PREIMPORTS = [
    "constraintbox",
    "constraintbox.boxrun",
    "constraintbox.agentrun",
    "constraintbox.constraints",
    "constraintbox.dualsolve",
    "constraintbox.gate_operations",
    "constraintbox.proposal_minilev_flow",
    "constraintbox.mini_lev_topology",
    "constraintbox.mini_levos",
    "constraintbox.workflow_graph",
    "constraintbox.maude_rewrite",
    "constraintbox.symbolic",
    "constraintbox.flow_termination",
    "constraintbox.gate",
    "constraintbox.cli",
    "constraintbox._provider_harness.providers",
]

OPS = {
    "box_pipeline": {
        "lane": "production",
        "timeout": 1800,
        "native_profile": False,
        "maude_prelude": True,
        "description": (
            "run_first_box(fixtures/live_run_request_v1.json) then the full "
            "agent run with the deterministic offline provider seam; real "
            "formal gates, real tool worker, real ClaimGate chain"
        ),
    },
    "formal_flow_gates": {
        "lane": "production",
        "timeout": 900,
        "native_profile": False,
        "maude_prelude": True,
        "description": (
            "gate_operations.run_formal_flow_gates on "
            "proposal_minilev_flow.reference_flow_policy()"
        ),
    },
    "dual_solve_smt_gate": {
        "lane": "production",
        "timeout": 600,
        "native_profile": True,
        "maude_prelude": False,
        "description": (
            "agentrun._smt_gate on the run path's own observed gate vector "
            "(three dual_solve calls: z3 + cvc5 + enumeration on real "
            "FiniteConstraintProblems)"
        ),
    },
    "mini_lev_topology": {
        "lane": "production",
        "timeout": 300,
        "native_profile": True,
        "maude_prelude": False,
        "description": (
            "proposal_minilev_flow._TOPOLOGY.evaluate(reference_flow_policy())"
            " — the run-path rustworkx topology preflight"
        ),
    },
    "gate_receipt": {
        "lane": "production",
        "timeout": 1200,
        "native_profile": False,
        "maude_prelude": False,
        "description": (
            "constraintbox.cli.main(['gate', receipts/first_released_run_"
            "20260809/run/release_receipt.json]) — the pinned gate surface "
            "against a real released receipt"
        ),
    },
    "hypothesis_test_lane": {
        "lane": "test_extra",
        "timeout": 900,
        "native_profile": False,
        "maude_prelude": False,
        "description": (
            "tests/test_hypothesis_adversarial.py under unittest — the "
            "[test] extra doing its declared job (adversarial input "
            "generation against assess_user_request and solver-result "
            "shapes); reported as the test lane, never as production reach"
        ),
    },
}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_dist(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def declared_dependencies() -> list[dict]:
    """Parse pyproject.toml: hard dependencies + every extra, deduplicated.

    One row per distribution; ``declared_in`` lists every declaration site so
    a dependency repeated across extras is proven once, not thrice.
    """
    import tomllib

    body = tomllib.loads((CB_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    merged: dict[str, dict] = {}

    def add(requirement: str, declared_in: str) -> None:
        match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
        if match is None:
            return
        key = _canonical_dist(match.group(1))
        row = merged.setdefault(
            key,
            {
                "distribution": match.group(1),
                "requirement": requirement.strip(),
                "declared_in": [],
            },
        )
        if declared_in not in row["declared_in"]:
            row["declared_in"].append(declared_in)

    for requirement in body["project"]["dependencies"]:
        add(requirement, "project.dependencies")
    for extra_name, requirements in body["project"].get(
        "optional-dependencies", {}
    ).items():
        for requirement in requirements:
            add(requirement, f"project.optional-dependencies.{extra_name}")
    return list(merged.values())


def import_names_for(distribution: str) -> list[str]:
    """distribution -> top-level import names, from live metadata first."""
    import importlib.metadata as md

    wanted = _canonical_dist(distribution)
    names = sorted(
        package
        for package, dists in md.packages_distributions().items()
        if wanted in {_canonical_dist(d) for d in dists}
        and not package.startswith("_")
    )
    if names:
        return names
    if REGISTRY_PATH.is_file():
        try:
            for tool in _read_json(REGISTRY_PATH).get("tools", []):
                if _canonical_dist(tool.get("distribution", "")) == wanted:
                    return [tool["import"]]
        except (ValueError, KeyError):
            pass
    return _STATIC_IMPORT_NAMES.get(distribution, [])


def package_paths(import_name: str) -> list[str]:
    """Package directories (or the module FILE for single-file modules).

    A single-file module (for example the ``isympy`` console module shipped by
    the sympy distribution) must contribute its own file path, never its
    parent directory: the parent is the whole site-packages root and would
    make every measurement match everything.
    """
    import importlib.util

    try:
        spec = importlib.util.find_spec(import_name)
    except (ImportError, ValueError):
        return []
    if spec is None:
        return []
    paths: list[str] = []
    if spec.submodule_search_locations:
        paths.extend(str(Path(p).resolve()) for p in spec.submodule_search_locations)
    elif spec.origin and spec.origin not in ("built-in", "frozen"):
        paths.append(str(Path(spec.origin).resolve()))
    return paths


def _path_matches(measured: str, package_path: str) -> bool:
    return measured == package_path or measured.startswith(package_path + os.sep)


def registry_roles() -> dict[str, dict]:
    roles: dict[str, dict] = {}
    if REGISTRY_PATH.is_file():
        try:
            for tool in _read_json(REGISTRY_PATH).get("tools", []):
                roles[_canonical_dist(tool.get("distribution", ""))] = {
                    "registry_id": tool.get("id"),
                    "cb_roles": tool.get("cb_roles"),
                    "integration_level": tool.get("integration_level"),
                }
        except (ValueError, KeyError):
            pass
    return roles


# ---------------------------------------------------------------------------
# Child-side: run one operation under measurement.
# ---------------------------------------------------------------------------

_MAUDE_PRELUDE_TEMPLATE = """try:
    import sys as _prove_sys, os as _prove_os
    _prove_fd = _prove_os.open({trace_path!r}, _prove_os.O_WRONLY | _prove_os.O_CREAT | _prove_os.O_APPEND, 0o644)
    _prove_seen = set()
    _prove_dirs = {package_dirs!r}
    def _prove_trace(frame, event, arg):
        if event == "call":
            code = frame.f_code
            filename = code.co_filename
            for prefix in _prove_dirs:
                if filename.startswith(prefix):
                    key = (filename, code.co_name, code.co_firstlineno)
                    if key not in _prove_seen:
                        _prove_seen.add(key)
                        try:
                            _prove_os.write(_prove_fd, ("%s\\t%d\\t%s\\n" % (filename, code.co_firstlineno, code.co_name)).encode("utf-8", "replace"))
                        except OSError:
                            pass
                    break
        return None
    _prove_sys.settrace(_prove_trace)
except BaseException:
    pass
"""


def _install_maude_worker_tracer(trace_path: Path, maude_dirs: list[str]) -> dict:
    """Wrap subprocess.Popen so the hermetic `-I` Maude worker gets a tracer.

    The worker is spawned with a scrubbed environment and `python -I`, so no
    environment-based tracer (coverage .pth, PYTHONPATH sitecustomize) can
    reach it.  The wrapper prepends a settrace prelude to the byte-identical
    bootstrap source; the pinned worker source and every internal check are
    untouched.  Nothing is weakened: this only OBSERVES.
    """
    prelude = _MAUDE_PRELUDE_TEMPLATE.format(
        trace_path=str(trace_path), package_dirs=tuple(maude_dirs)
    )
    original_popen = subprocess.Popen
    state = {"injections": 0}

    def wrapped_popen(args, *pargs, **kwargs):
        try:
            if isinstance(args, (list, tuple)) and any(
                isinstance(item, str) and "<pinned-maude-worker>" in item
                for item in args
            ):
                args = list(args)
                flag_index = args.index("-c")
                args[flag_index + 1] = prelude + args[flag_index + 1]
                state["injections"] += 1
        except (ValueError, IndexError, TypeError):
            pass
        return original_popen(args, *pargs, **kwargs)

    subprocess.Popen = wrapped_popen  # type: ignore[misc]
    return state


class _NativeCallRecorder:
    """sys.setprofile c_call recorder for compiled dependency callables."""

    def __init__(self, top_levels: set[str]):
        self.top_levels = top_levels
        self.first: dict[str, dict] = {}
        self.counts: dict[str, int] = {}

    def _module_of(self, callable_obj):
        module = getattr(callable_obj, "__module__", None)
        if isinstance(module, str):
            return module
        objclass = getattr(callable_obj, "__objclass__", None)
        if objclass is not None:
            module = getattr(objclass, "__module__", None)
            if isinstance(module, str):
                return module
        bound_self = getattr(callable_obj, "__self__", None)
        if bound_self is not None:
            module = type(bound_self).__module__
            if isinstance(module, str):
                return module
        return None

    def __call__(self, frame, event, arg):
        if event != "c_call":
            return
        try:
            module = self._module_of(arg)
            if module is None:
                return
            top = module.split(".", 1)[0]
            if top not in self.top_levels:
                return
            self.counts[top] = self.counts.get(top, 0) + 1
            if top not in self.first:
                caller = frame.f_code
                self.first[top] = {
                    "native_module": module,
                    "native_callable": getattr(
                        arg, "__qualname__", getattr(arg, "__name__", repr(arg))
                    ),
                    "caller_file": caller.co_filename,
                    "caller_line": frame.f_lineno,
                    "caller_function": caller.co_name,
                }
        except Exception:
            return


class _CompliantOfflineProvider:
    """Deterministic offline provider for the documented injectable seam.

    Emits the controller's only releasable claim with the controller's own
    evidence reference, and echoes the requested model the way a compliant
    backend would (FakeSuccessProvider sets model_resolved = job.model).
    It decides nothing: every gate that judges it is production code.
    """

    name = "prove-dependencies-offline"

    def __init__(self, agentrun_module, fake_success_cls):
        self._agentrun = agentrun_module
        self._fake_success_cls = fake_success_cls
        self.calls = 0

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        del timeout
        self.calls += 1
        match = re.search(r"evidence_ref=([0-9a-f]{64})", job.task.prompt)
        if match is None:
            raise RuntimeError("controller evidence reference absent from prompt")
        body = json.dumps(
            {
                "proposal_id": f"prove-deps-proposal-{self.calls}",
                "candidate": {
                    "requested_claim": self._agentrun.ALLOWED_CLAIM,
                    "evidence_ref": match.group(1),
                },
                "falsifiers": [
                    "the operation-severance control stops flipping the verdict"
                ],
            },
            sort_keys=True,
        )
        return self._fake_success_cls(body).run(
            job, started_at=started_at, completed_at=completed_at
        )


def _op_box_pipeline(opdir: Path) -> dict:
    from constraintbox.boxrun import run_first_box
    from constraintbox import agentrun
    from constraintbox._provider_harness.providers import FakeSuccessProvider

    request_raw = FIXTURE_REQUEST.read_bytes()
    box_dir = opdir / "box"
    run_dir = opdir / "run"
    box_result, box_code = run_first_box(request_raw, box_dir)
    summary = {
        "box_disposition": box_result.get("disposition"),
        "box_reason": box_result.get("reason"),
        "box_exit_code": box_code,
    }
    if not (box_dir / "box_receipt.json").is_file():
        summary["agent_run"] = "skipped: box receipt absent"
        return summary
    provider = _CompliantOfflineProvider(agentrun, FakeSuccessProvider)
    result, code = agentrun._run_agent_for_test(box_dir, run_dir, provider=provider)
    formal = result.get("formal_gates") or {}
    summary.update(
        {
            "run_disposition": result.get("disposition"),
            "run_reason": result.get("reason"),
            "run_exit_code": code,
            "provider_calls": provider.calls,
            "formal_gates_any_mismatch": formal.get("any_mismatch"),
            "formal_gate_verdicts": {
                execution.get("gate_id"): execution.get("verdict")
                for execution in formal.get("executions", [])
            },
        }
    )
    return summary


def _op_formal_flow_gates(opdir: Path) -> dict:
    del opdir
    from constraintbox.gate_operations import run_formal_flow_gates
    from constraintbox.proposal_minilev_flow import reference_flow_policy

    receipt = run_formal_flow_gates(reference_flow_policy())
    return {
        "any_mismatch": receipt["any_mismatch"],
        "executions": [
            {
                "gate_id": execution["gate_id"],
                "verdict": execution["verdict"],
                "reason": execution["reason"],
                "input_sha256": execution["input_sha256"],
                "output_sha256": execution["output_sha256"],
            }
            for execution in receipt["executions"]
        ],
    }


def _op_dual_solve_smt_gate(opdir: Path) -> dict:
    del opdir
    from constraintbox import agentrun

    observed = {name: True for name in agentrun._BOOLEAN_GATES}
    observed["requested_claim"] = agentrun.ALLOWED_CLAIM
    gate = agentrun._smt_gate(observed)

    def statuses(row):
        return {
            backend: row[backend]["status"]
            for backend in ("z3", "cvc5", "enumeration")
        }

    return {
        "settled": gate["settled"],
        "proposal_admitted": gate["proposal_admitted"],
        "z3_version": gate["z3_version"],
        "cvc5_version": gate["cvc5_version"],
        "proposal_statuses": statuses(gate["proposal"]),
        "hostile_overclaim_statuses": statuses(gate["hostile_overclaim"]),
        "claim_constraint_erased_statuses": statuses(
            gate["claim_constraint_erased_control"]
        ),
        "state_count": gate["proposal"]["state_count"],
    }


def _op_mini_lev_topology(opdir: Path) -> dict:
    from constraintbox.proposal_minilev_flow import _TOPOLOGY, reference_flow_policy

    flow_root = opdir / "flow"
    flow_root.mkdir(parents=True, exist_ok=True)
    preflight = _TOPOLOGY.evaluate(reference_flow_policy(), flow_root)
    return {
        "signal": preflight.signal.value,
        "evaluation_executed": preflight.evaluation_executed,
        "profile_disposition": preflight.profile_outcome.get("disposition"),
        "profile_reason": preflight.profile_outcome.get("reason"),
        "projection_sha256": preflight.projection_sha256,
    }


def _op_gate_receipt(opdir: Path) -> dict:
    from constraintbox import cli

    stdout_path = opdir / "gate_stdout.json"
    captured = io.StringIO()
    old_argv = sys.argv
    old_stdout = sys.stdout
    exit_code = 0
    try:
        sys.argv = ["constraintbox", "gate", str(RELEASED_RECEIPT)]
        sys.stdout = captured
        try:
            cli.main()
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
    text = captured.getvalue()
    stdout_path.write_text(text, encoding="utf-8")
    summary = {"exit_code": exit_code, "receipt_path": str(RELEASED_RECEIPT)}
    try:
        body = json.loads(text)
        summary["disposition"] = body.get("disposition")
        summary["chain_verdict"] = body.get("chain_verdict")
        summary["reason"] = body.get("reason")
    except ValueError:
        summary["stdout_head"] = text[:400]
    return summary


def _op_hypothesis_test_lane(opdir: Path) -> dict:
    import unittest

    tests_dir = CB_ROOT / "tests"
    sys.path.insert(0, str(tests_dir))
    stream = io.StringIO()
    loader = unittest.TestLoader()
    suite = loader.discover(
        str(tests_dir),
        pattern="test_hypothesis_adversarial.py",
        top_level_dir=str(tests_dir),
    )
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    (opdir / "unittest_output.txt").write_text(stream.getvalue(), encoding="utf-8")
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }


_OP_FUNCTIONS = {
    "box_pipeline": _op_box_pipeline,
    "formal_flow_gates": _op_formal_flow_gates,
    "dual_solve_smt_gate": _op_dual_solve_smt_gate,
    "mini_lev_topology": _op_mini_lev_topology,
    "gate_receipt": _op_gate_receipt,
    "hypothesis_test_lane": _op_hypothesis_test_lane,
}


def run_child(op_name: str, opdir: Path) -> int:
    """Execute one operation under measurement.  Never raises: records."""
    spec = OPS[op_name]
    opdir.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "schema": "constraintbox.dependency-reachability-op.v1",
        "operation": op_name,
        "lane": spec["lane"],
        "description": spec["description"],
        "pid": os.getpid(),
        "interpreter": sys.executable,
        "started_at": _now(),
    }

    if str(CB_SRC) not in sys.path:
        sys.path.insert(0, str(CB_SRC))

    deps = declared_dependencies()
    dep_import_names: list[str] = []
    for row in deps:
        dep_import_names.extend(import_names_for(row["distribution"]))
    dep_import_names = sorted(set(dep_import_names))
    dep_dirs: dict[str, list[str]] = {
        name: package_paths(name) for name in dep_import_names
    }
    result["dependency_import_names"] = dep_import_names
    result["dependency_package_paths"] = dep_dirs

    # -- phase 1: pre-import everything OUTSIDE the measurement window -------
    import importlib

    preimport_errors: dict[str, str] = {}
    for module_name in dep_import_names + _CB_PREIMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - recorded, not fatal
            preimport_errors[module_name] = f"{type(exc).__name__}: {exc}"
    result["preimport_errors"] = preimport_errors

    # -- measurement scaffolding ---------------------------------------------
    rc_path = opdir / "coveragerc"
    # Grandchild processes spawned by the operation inherit this environment;
    # the site-packages coverage .pth hook starts coverage for them.  This
    # child's own startup has already passed, so only the operation window is
    # measured in-process below.
    os.environ["COVERAGE_PROCESS_START"] = str(rc_path)

    import coverage

    cov = coverage.Coverage(config_file=str(rc_path))

    maude_state = {"injections": 0}
    if spec["maude_prelude"]:
        maude_prefixes = [
            path + os.sep if Path(path).is_dir() else path
            for path in dep_dirs.get("maude", [])
        ]
        maude_state = _install_maude_worker_tracer(
            opdir / "maude_worker_trace.tsv", maude_prefixes
        )

    recorder = None
    if spec["native_profile"]:
        recorder = _NativeCallRecorder(set(dep_import_names))

    # -- phase 2: run the real operation under measurement -------------------
    op_error = None
    cov.start()
    if recorder is not None:
        sys.setprofile(recorder)
    started = time.monotonic()
    try:
        summary = _OP_FUNCTIONS[op_name](opdir)
    except BaseException as exc:  # noqa: BLE001 - the receipt records it
        summary = None
        op_error = {
            "type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(limit=30),
        }
    finally:
        if recorder is not None:
            sys.setprofile(None)
        cov.stop()
        cov.save()
    result["wall_seconds"] = round(time.monotonic() - started, 3)
    result["operation_summary"] = summary
    result["operation_error"] = op_error
    result["maude_worker_injections"] = maude_state["injections"]
    if recorder is not None:
        result["native_calls"] = {
            top: {"first": recorder.first[top], "count": recorder.counts[top]}
            for top in sorted(recorder.first)
        }
    result["completed_at"] = _now()
    (opdir / "op_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if op_error is None else 3


# ---------------------------------------------------------------------------
# Parent-side: orchestration and analysis.
# ---------------------------------------------------------------------------


def _write_coveragerc(rc_path: Path, data_file: Path, include_patterns: list[str]) -> None:
    include_lines = "\n".join(f"    {pattern}" for pattern in sorted(set(include_patterns)))
    rc_path.write_text(
        "[run]\n"
        "parallel = true\n"
        f"data_file = {data_file}\n"
        "include =\n"
        f"{include_lines}\n"
        "disable_warnings =\n"
        "    no-data-collected\n"
        "    module-not-measured\n"
        "    couldnt-parse\n",
        encoding="utf-8",
    )


def _function_body_spans(source_path: Path) -> list[tuple[int, int]]:
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, ValueError, OSError):
        return []
    spans: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            start = node.body[0].lineno
            end = node.end_lineno or start
            spans.append((start, end))
    return spans


def _classify_lines(source_path: Path, lines: set[int]) -> tuple[list[int], list[int]]:
    """Split executed lines into (function-body lines, module-level lines)."""
    spans = _function_body_spans(source_path)
    function_lines: list[int] = []
    module_lines: list[int] = []
    for line in sorted(lines):
        if any(start <= line <= end for start, end in spans):
            function_lines.append(line)
        else:
            module_lines.append(line)
    return function_lines, module_lines


def _coverage_files(opdir: Path) -> list[Path]:
    return sorted(
        path
        for path in opdir.iterdir()
        if path.name.startswith(".coverage.") and path.is_file()
    )


def _pid_of_coverage_file(path: Path) -> int | None:
    # coverage 7.15 parallel suffix: .coverage.<host>.pid<pid>.<rand>.<rand>
    match = re.search(r"\.pid(\d+)\.", path.name)
    if match is None:
        # older format: .coverage.<host>.<pid>.X<rand>
        match = re.search(r"\.(\d+)\.X[A-Za-z0-9]+", path.name)
    return int(match.group(1)) if match else None


def analyze(workdir: Path, op_names: list[str]) -> dict:
    import coverage

    deps = declared_dependencies()
    roles = registry_roles()
    dep_rows: list[dict] = []
    for row in deps:
        names = import_names_for(row["distribution"])
        paths: list[str] = []
        for name in names:
            paths.extend(package_paths(name))
        dep_rows.append(
            {
                **row,
                "import_names": names,
                "package_paths": paths,
                **roles.get(_canonical_dist(row["distribution"]), {}),
            }
        )

    op_reports: dict[str, dict] = {}
    for op_name in op_names:
        opdir = workdir / op_name
        report: dict = {"operation": op_name}
        op_result_path = opdir / "op_result.json"
        if op_result_path.is_file():
            report["op_result"] = _read_json(op_result_path)
        else:
            report["op_result"] = None
        child_pid = (report["op_result"] or {}).get("pid")

        evidence_by_file: dict[str, dict] = {}
        for data_path in _coverage_files(opdir):
            data = coverage.CoverageData(basename=str(data_path))
            try:
                data.read()
            except Exception:  # noqa: BLE001 - unreadable shard is skipped
                continue
            source_pid = _pid_of_coverage_file(data_path)
            phase = (
                "operation"
                if child_pid is not None and source_pid == child_pid
                else "subprocess_lifetime"
            )
            for measured in data.measured_files():
                lines = set(data.lines(measured) or [])
                if not lines:
                    continue
                entry = evidence_by_file.setdefault(
                    measured, {"operation": set(), "subprocess_lifetime": set()}
                )
                entry[phase] |= lines
        report["coverage_files"] = [p.name for p in _coverage_files(opdir)]
        report["evidence_by_file"] = evidence_by_file

        maude_trace = opdir / "maude_worker_trace.tsv"
        worker_calls: list[dict] = []
        if maude_trace.is_file():
            for raw_line in maude_trace.read_text(encoding="utf-8").splitlines():
                parts = raw_line.split("\t")
                if len(parts) == 3:
                    worker_calls.append(
                        {
                            "file": parts[0],
                            "line": int(parts[1]),
                            "function": parts[2],
                        }
                    )
        report["maude_worker_calls"] = worker_calls
        op_reports[op_name] = report

    # ---- per-dependency verdicts ------------------------------------------
    dependency_receipts: list[dict] = []
    for dep in dep_rows:
        prefixes = tuple(dep["package_paths"])
        evidence: list[dict] = []
        for op_name in op_names:
            report = op_reports[op_name]
            lane = OPS[op_name]["lane"]
            op_result = report["op_result"] or {}

            # tier 1 / tier 4: coverage lines inside the package
            for measured, phases in sorted(report["evidence_by_file"].items()):
                if not any(_path_matches(measured, p) for p in prefixes):
                    continue
                for phase in ("operation", "subprocess_lifetime"):
                    lines = phases[phase]
                    if not lines:
                        continue
                    function_lines, module_lines = _classify_lines(
                        Path(measured), lines
                    )
                    if function_lines:
                        evidence.append(
                            {
                                "tier": (
                                    "operation_python_call"
                                    if phase == "operation"
                                    else "subprocess_python_call"
                                ),
                                "operation": op_name,
                                "lane": lane,
                                "file": measured,
                                "first_function_body_line": function_lines[0],
                                "function_body_lines": len(function_lines),
                                "module_level_lines": len(module_lines),
                            }
                        )
                    elif module_lines:
                        evidence.append(
                            {
                                "tier": "module_level_only",
                                "operation": op_name,
                                "lane": lane,
                                "file": measured,
                                "first_line": module_lines[0],
                                "module_level_lines": len(module_lines),
                            }
                        )

            # tier 2: native c_calls
            native = (op_result.get("native_calls") or {})
            for import_name in dep["import_names"]:
                if import_name in native:
                    row = native[import_name]
                    evidence.append(
                        {
                            "tier": "native_c_call",
                            "operation": op_name,
                            "lane": lane,
                            "native_module": row["first"]["native_module"],
                            "native_callable": row["first"]["native_callable"],
                            "caller_file": row["first"]["caller_file"],
                            "caller_line": row["first"]["caller_line"],
                            "caller_function": row["first"]["caller_function"],
                            "call_count": row["count"],
                        }
                    )

            # tier 3: hermetic maude worker calls
            if "maude" in dep["import_names"]:
                function_calls = [
                    call
                    for call in report["maude_worker_calls"]
                    if call["function"] != "<module>"
                ]
                if function_calls:
                    first = function_calls[0]
                    evidence.append(
                        {
                            "tier": "hermetic_worker_python_call",
                            "operation": op_name,
                            "lane": lane,
                            "file": first["file"],
                            "first_function_line": first["line"],
                            "first_function": first["function"],
                            "distinct_functions": len(
                                {
                                    (c["file"], c["function"], c["line"])
                                    for c in function_calls
                                }
                            ),
                            "worker_injections": op_result.get(
                                "maude_worker_injections"
                            ),
                        }
                    )

        strong_tiers = {
            "operation_python_call",
            "native_c_call",
            "hermetic_worker_python_call",
        }
        production_strong = [
            row
            for row in evidence
            if row["tier"] in strong_tiers and row["lane"] == "production"
        ]
        any_strong = [row for row in evidence if row["tier"] in strong_tiers]
        weak = [row for row in evidence if row["tier"] not in strong_tiers]
        if production_strong:
            verdict = "REACHED"
            primary = production_strong[0]
        elif any_strong:
            verdict = "REACHED_TEST_LANE_ONLY"
            primary = any_strong[0]
        elif weak:
            verdict = "IMPORT_ONLY"
            primary = weak[0]
        else:
            verdict = "NEVER_REACHED"
            primary = None
        dependency_receipts.append(
            {
                "distribution": dep["distribution"],
                "requirement": dep["requirement"],
                "declared_in": dep["declared_in"],
                "import_names": dep["import_names"],
                "cb_roles": dep.get("cb_roles"),
                "verdict": verdict,
                "primary_evidence": primary,
                "evidence": evidence,
            }
        )

    # strip raw line sets from op reports for the receipt (bulky, derivable)
    for report in op_reports.values():
        report["evidence_by_file"] = {
            measured: {
                phase: sorted(lines)[:20]
                for phase, lines in phases.items()
                if lines
            }
            for measured, phases in report["evidence_by_file"].items()
        }
        report["maude_worker_calls"] = report["maude_worker_calls"][:40]

    return {
        "schema": SCHEMA,
        "generated_at": _now(),
        "interpreter": sys.executable,
        "python_version": sys.version,
        "cb_root": str(CB_ROOT),
        "workdir": str(workdir),
        "method": (
            "each operation runs in a fresh child process; every declared "
            "dependency and the ConstraintBox modules are imported BEFORE "
            "measurement starts, so import-time execution is excluded; the "
            "operation then runs under coverage (include-filtered to the "
            "dependency package directories) plus a sys.setprofile c_call "
            "recorder; grandchild processes are covered by the site-packages "
            "coverage .pth hook via COVERAGE_PROCESS_START; the hermetic "
            "`python -I` Maude worker (scrubbed environment, unreachable by "
            "any env-based tracer) is observed by prepending a settrace "
            "prelude to its byte-identical bootstrap at spawn time; REACHED "
            "requires a function-body line, a native c_call, or a worker "
            "function call during a production operation — module-level "
            "(import) lines never suffice"
        ),
        "claim_ceiling": (
            "execution-reachability evidence only; no correctness, semantic, "
            "or promotion claim"
        ),
        "promotion_allowed": False,
        "operations": {
            name: {
                "lane": OPS[name]["lane"],
                "description": OPS[name]["description"],
                "op_result": op_reports[name]["op_result"],
                "coverage_files": op_reports[name]["coverage_files"],
                "evidence_by_file_head": op_reports[name]["evidence_by_file"],
                "maude_worker_calls_head": op_reports[name]["maude_worker_calls"],
            }
            for name in op_names
        },
        "dependencies": dependency_receipts,
    }


def _print_report(receipt: dict) -> None:
    print("=" * 78)
    print("ConstraintBox dependency reachability proof")
    print(f"generated_at: {receipt['generated_at']}")
    print(f"interpreter:  {receipt['interpreter']}")
    print(f"workdir:      {receipt['workdir']}")
    print("=" * 78)
    print("\nOperations driven (real ConstraintBox surfaces):")
    for name, op in receipt["operations"].items():
        op_result = op["op_result"] or {}
        summary = op_result.get("operation_summary")
        error = op_result.get("operation_error")
        wall = op_result.get("wall_seconds")
        line = f"  {name} [{op['lane']}] wall={wall}s"
        if error:
            line += f"  ERROR={error['type']}: {error['error'][:120]}"
        print(line)
        if isinstance(summary, dict):
            compact = {
                key: value
                for key, value in summary.items()
                if not isinstance(value, (dict, list))
            }
            print(f"    summary: {json.dumps(compact, sort_keys=True)}")
            for key, value in summary.items():
                if isinstance(value, (dict, list)):
                    print(f"    {key}: {json.dumps(value, sort_keys=True)[:220]}")
    print("\nPer-dependency verdicts:")
    reached, never = [], []
    for dep in receipt["dependencies"]:
        declared_in = ", ".join(dep["declared_in"])
        print(
            f"\n  {dep['distribution']} ({dep['requirement']}; "
            f"declared in {declared_in}) -> {dep['verdict']}"
        )
        primary = dep["primary_evidence"]
        if primary:
            print(f"    primary: {json.dumps(primary, sort_keys=True)}")
        by_tier: dict[str, int] = {}
        for row in dep["evidence"]:
            by_tier[row["tier"]] = by_tier.get(row["tier"], 0) + 1
        if by_tier:
            print(f"    evidence rows by tier: {json.dumps(by_tier, sort_keys=True)}")
        for row in dep["evidence"][:6]:
            print(f"      - {json.dumps(row, sort_keys=True)[:240]}")
        if dep["verdict"] in ("REACHED",):
            reached.append(dep["distribution"])
        elif dep["verdict"] in ("NEVER_REACHED", "IMPORT_ONLY"):
            never.append(f"{dep['distribution']} ({dep['verdict']})")
    print("\n" + "=" * 78)
    print(f"REACHED by production operations: {', '.join(reached) or '(none)'}")
    test_only = [
        dep["distribution"]
        for dep in receipt["dependencies"]
        if dep["verdict"] == "REACHED_TEST_LANE_ONLY"
    ]
    if test_only:
        print(f"REACHED only in the [test] extra lane: {', '.join(test_only)}")
    print(f"NOT reached (import-only or never): {', '.join(never) or '(none)'}")
    print("=" * 78)


def run_parent(args) -> int:
    if args.workdir:
        workdir = Path(args.workdir).resolve()
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        workdir = Path(tempfile.mkdtemp(prefix="cb_prove_deps_"))

    op_names = list(OPS)
    if args.ops:
        requested = [name.strip() for name in args.ops.split(",") if name.strip()]
        unknown = [name for name in requested if name not in OPS]
        if unknown:
            print(f"unknown operations: {unknown}; known: {list(OPS)}", file=sys.stderr)
            return 2
        op_names = requested

    deps = declared_dependencies()
    include_patterns: list[str] = []
    for row in deps:
        for import_name in import_names_for(row["distribution"]):
            for path in package_paths(import_name):
                include_patterns.append(
                    f"{path}/*" if Path(path).is_dir() else path
                )
    if not include_patterns:
        print("no dependency package paths resolved; aborting", file=sys.stderr)
        return 2

    print(f"workdir: {workdir}")
    print(f"declared dependencies: {[row['requirement'] for row in deps]}")

    for op_name in op_names:
        opdir = workdir / op_name
        if opdir.exists():
            shutil.rmtree(opdir)
        opdir.mkdir(parents=True)
        _write_coveragerc(opdir / "coveragerc", opdir / ".coverage", include_patterns)

        env = dict(os.environ)
        env.pop("COVERAGE_PROCESS_START", None)  # child sets it itself, post-startup
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{CB_SRC}:{existing}" if existing else str(CB_SRC)
        )
        if op_name == "box_pipeline":
            env.setdefault("CONSTRAINTBOX_PROVIDER_HMAC_KEY", "cb-prove-deps-offline-key")
        command = [sys.executable, str(Path(__file__).resolve()), "--op", op_name,
                   "--opdir", str(opdir)]
        print(f"\n--- running operation: {op_name} (timeout {OPS[op_name]['timeout']}s)")
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=str(opdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=OPS[op_name]["timeout"],
            )
            (opdir / "child_stdout.txt").write_text(completed.stdout, encoding="utf-8")
            (opdir / "child_stderr.txt").write_text(completed.stderr, encoding="utf-8")
            print(
                f"    child exit={completed.returncode} "
                f"wall={round(time.monotonic() - started, 1)}s"
            )
            if completed.returncode not in (0, 3):
                print(f"    stderr tail: {completed.stderr[-500:]}")
        except subprocess.TimeoutExpired as exc:
            (opdir / "child_stdout.txt").write_text(
                (exc.stdout or b"").decode("utf-8", "replace")
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or ""),
                encoding="utf-8",
            )
            print(f"    TIMEOUT after {OPS[op_name]['timeout']}s (recorded honestly)")

    receipt = analyze(workdir, op_names)
    _print_report(receipt)

    RECEIPT_OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = RECEIPT_OUT.with_name(f".{RECEIPT_OUT.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, RECEIPT_OUT)
    print(f"\nreceipt written: {RECEIPT_OUT}")
    if not args.keep and not args.workdir:
        print(f"workdir retained for audit: {workdir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--op", help="(internal) run one operation in-process")
    parser.add_argument("--opdir", help="(internal) operation working directory")
    parser.add_argument("--workdir", help="parent working directory (default: mkdtemp)")
    parser.add_argument("--ops", help="comma-separated subset of operations")
    parser.add_argument(
        "--keep", action="store_true", help="keep the working directory"
    )
    args = parser.parse_args()
    if args.op:
        if not args.opdir:
            print("--op requires --opdir", file=sys.stderr)
            return 2
        return run_child(args.op, Path(args.opdir).resolve())
    return run_parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
