"""Candidate-flow orchestrator: wire the harness into the prune loop.

This is the L2 wiring that turns a single LLM/tool candidate into a signed,
gated run.  It composes the already-green core (providers -> runner.run_job ->
gates.gate -> signing) into a SIX-STAGE candidate flow and records a typed step
result for every stage plus one signed receipt:

  1. support_probe        verify the provider is available / report its version
  2. bounded_micro_eval   1 positive / 1 negative / 1 boundary local-tool check
  3. typed_observation    run the job through the provider + runner -> SIGNED ModelReceipt
  4. code_owned_scorer    the deterministic gate() verdict (+ divergence/controls)
  5. gateproof            collect the gate checks + the signature-verify result
  6. semantic_control     admit | reject | keep_scratch_diagnostic

DOCTRINE: the semantic_control verdict is the GATE's verdict.  The orchestrator
NEVER re-decides admission -- ``semantic_control.admitted`` is byte-for-byte
``gate().admitted``.  The only refinement the orchestrator adds is splitting a
gate REJECTION into ``reject`` (a real failure: bad status / failed compile)
versus ``keep_scratch_diagnostic`` (an unsigned / forged / un-auditable receipt
that simply cannot be PROMOTED -- it is kept as scratch, never thrown, never
promoted).  Admission itself is never overridden.

A test is load-bearing only if it COULD fail.  The micro-eval's negative case
runs a REAL broken-Python subprocess whose nonzero returncode is captured (not
hardcoded); a passing micro-eval and a failing one take DIFFERENT branches.
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from .gates import gate
from .providers import LocalToolProvider, Provider, ProviderError
from .runner import run_job, write_receipt
from .signing import normalize_identity, verify_payload
from .types import GateResult, ModelJob, ModelReceipt, TaskSpec, TestRecord

# The six candidate-flow stage names, in execution order.
STAGE_NAMES = (
    "support_probe",
    "bounded_micro_eval",
    "typed_observation",
    "code_owned_scorer",
    "gateproof",
    "semantic_control",
)

# semantic_control terminal verdicts.
SEMANTIC_ADMIT = "admit"
SEMANTIC_REJECT = "reject"
SEMANTIC_KEEP_SCRATCH = "keep_scratch_diagnostic"

ORCH_SCHEMA = "codex_ratchet.llm_orchestrator_run.v1"


@dataclass
class StageStep:
    """One recorded step of the candidate flow.

    ``ok`` is the stage's own pass/fail; ``could_fail`` marks whether the step
    is load-bearing (a stage that is true for all inputs is NOT evidence and is
    recorded could_fail=False).  ``detail`` is human text; ``data`` carries the
    typed payload the next stage consumes.
    """

    stage: str
    ok: bool
    could_fail: bool
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "ok": self.ok,
            "could_fail": self.could_fail,
            "detail": self.detail,
            "data": dict(self.data),
        }


@dataclass
class CandidateRun:
    """The whole candidate flow: stage trace + the one signed receipt + verdict.

    ``semantic_verdict`` is the terminal label (admit | reject |
    keep_scratch_diagnostic).  ``admitted`` is ALWAYS the gate's admission
    boolean -- the orchestrator does not override it.
    """

    task_id: str
    stages: list[StageStep]
    receipt: Optional[ModelReceipt]
    gate_result: Optional[GateResult]
    semantic_verdict: str
    admitted: bool
    receipt_path: Optional[str] = None
    schema: str = ORCH_SCHEMA

    def step(self, name: str) -> Optional[StageStep]:
        for s in self.stages:
            if s.stage == name:
                return s
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "task_id": self.task_id,
            "stages": [s.to_dict() for s in self.stages],
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "gate_result": self.gate_result.to_dict() if self.gate_result else None,
            "semantic_verdict": self.semantic_verdict,
            "admitted": self.admitted,
            "receipt_path": self.receipt_path,
        }


# ---------------------------------------------------------------------------
# Stage 1: support_probe
# ---------------------------------------------------------------------------


def _support_probe(provider: Provider) -> StageStep:
    """Verify the provider is available + report what version/identity it is.

    For a fake/local provider this confirms the object is a real Provider with a
    name and a runnable ``run``.  For OpenRouterProvider availability means an
    api_key is configured (no network call here -- that would not be offline).
    COULD fail: a provider missing its name or run method, or an OpenRouter
    provider with no key, fails this probe.
    """
    name = getattr(provider, "name", None)
    runnable = callable(getattr(provider, "run", None))
    available = bool(name) and runnable
    detail = f"provider={name!r} runnable={runnable}"

    # OpenRouter-style providers expose an api_key; absent key == unavailable.
    if hasattr(provider, "api_key"):
        has_key = bool(getattr(provider, "api_key"))
        available = available and has_key
        detail += f" api_key_present={has_key}"

    version = sys.version.split()[0]
    return StageStep(
        stage="support_probe",
        ok=available,
        could_fail=True,
        detail=detail,
        data={"provider_name": name, "available": available, "python_version": version},
    )


# ---------------------------------------------------------------------------
# Stage 2: bounded_micro_eval (1 positive / 1 negative / 1 boundary)
# ---------------------------------------------------------------------------


def _micro_eval(
    *,
    workdir: Path,
    positive_cmd: Optional[list[str]] = None,
    negative_cmd: Optional[list[str]] = None,
    boundary_cmd: Optional[list[str]] = None,
    timeout: float = 30.0,
) -> StageStep:
    """Run 1 positive / 1 negative / 1 boundary local-tool check.

    Each check runs a REAL subprocess via LocalToolProvider and the verdict is
    the REAL captured returncode -- never hardcoded.  Expected outcomes:

      * positive : a well-formed py file compiles      -> status success
      * negative : a deliberately broken py file        -> status error (could fail)
      * boundary : an empty py file compiles (edge ok)  -> status success

    The stage PASSES iff positive==success AND negative==error AND
    boundary==success.  If a caller supplies its own commands they override the
    defaults (the default trio exercises the LocalToolProvider end to end).
    """
    workdir.mkdir(parents=True, exist_ok=True)

    if positive_cmd is None:
        good = workdir / "good.py"
        good.write_text("x = 1\n", encoding="utf-8")
        positive_cmd = [sys.executable, "-m", "py_compile", str(good)]
    if negative_cmd is None:
        broken = workdir / "broken.py"
        broken.write_text("def (\n", encoding="utf-8")  # syntax error
        negative_cmd = [sys.executable, "-m", "py_compile", str(broken)]
    if boundary_cmd is None:
        empty = workdir / "empty.py"
        empty.write_text("", encoding="utf-8")  # boundary: empty module
        boundary_cmd = [sys.executable, "-m", "py_compile", str(empty)]

    provider = LocalToolProvider()
    results: dict[str, str] = {}
    for label, cmd, want in (
        ("positive", positive_cmd, "success"),
        ("negative", negative_cmd, "error"),
        ("boundary", boundary_cmd, "success"),
    ):
        job = ModelJob(
            task=TaskSpec(task_id=f"micro_{label}", role="probe", prompt=label),
            provider="local_tool",
            model="py_compile",
            output_path=str(workdir / f"micro_{label}.out"),
            command=cmd,
        )
        receipt = provider.run(
            job,
            timeout=timeout,
            started_at="1970-01-01T00:00:00+00:00",
            completed_at="1970-01-01T00:00:00+00:00",
        )
        results[label] = receipt.status

    positive_ok = results["positive"] == "success"
    negative_ok = results["negative"] == "error"  # broken file MUST fail to compile
    boundary_ok = results["boundary"] == "success"
    ok = positive_ok and negative_ok and boundary_ok
    return StageStep(
        stage="bounded_micro_eval",
        ok=ok,
        could_fail=True,
        detail=(
            f"positive={results['positive']}(want success) "
            f"negative={results['negative']}(want error) "
            f"boundary={results['boundary']}(want success)"
        ),
        data={
            "positive": results["positive"],
            "negative": results["negative"],
            "boundary": results["boundary"],
            "positive_ok": positive_ok,
            "negative_ok": negative_ok,
            "boundary_ok": boundary_ok,
        },
    )


# ---------------------------------------------------------------------------
# The driver
# ---------------------------------------------------------------------------


def run_candidate(
    task: TaskSpec,
    provider: Provider,
    *,
    model: str,
    output_path: str,
    produced_by: str,
    workdir: Path | str,
    command: Optional[list[str]] = None,
    cwd: Optional[str] = None,
    started_at: str,
    completed_at: str,
    timeout: Optional[float] = None,
    audit_receipts: Optional[list[ModelReceipt]] = None,
    receipt_path: Optional[str | Path] = None,
    micro_eval_cmds: Optional[dict[str, list[str]]] = None,
    skip_micro_eval_on_unavailable: bool = True,
) -> CandidateRun:
    """Drive one candidate through the six-stage flow and return a CandidateRun.

    The flow:
      1. support_probe       -- provider availability/version
      2. bounded_micro_eval  -- 1 positive / 1 negative / 1 boundary local check
      3. typed_observation   -- run_job(provider) -> SIGNED ModelReceipt
      4. code_owned_scorer   -- gate() verdict (the code owns the score)
      5. gateproof           -- gather gate checks + verify the signature
      6. semantic_control    -- admit | reject | keep_scratch_diagnostic

    The semantic_control verdict's ADMISSION is exactly ``gate().admitted``;
    the orchestrator never re-decides it.  A gate REJECTION is refined into
    ``reject`` vs ``keep_scratch_diagnostic`` (the latter when the receipt is
    unsigned/forged/un-promotable) -- the admission boolean stays the gate's.
    """
    workdir = Path(workdir)
    audit_receipts = audit_receipts or []
    stages: list[StageStep] = []

    # --- Stage 1: support_probe ---
    probe = _support_probe(provider)
    stages.append(probe)

    # --- Stage 2: bounded_micro_eval ---
    cmds = micro_eval_cmds or {}
    micro = _micro_eval(
        workdir=workdir / "micro_eval",
        positive_cmd=cmds.get("positive"),
        negative_cmd=cmds.get("negative"),
        boundary_cmd=cmds.get("boundary"),
        timeout=timeout or 30.0,
    )
    stages.append(micro)

    # --- Stage 3: typed_observation (run + sign) ---
    job = ModelJob(
        task=task,
        provider=getattr(provider, "name", "provider"),
        model=model,
        output_path=output_path,
        command=command,
        cwd=cwd,
        produced_by=produced_by,
    )
    receipt: Optional[ModelReceipt] = None
    obs_ok = False
    obs_detail = ""
    try:
        receipt = run_job(
            job,
            provider,
            timeout=timeout,
            started_at=started_at,
            completed_at=completed_at,
            receipt_path=receipt_path,
        )
        obs_ok = receipt.status == "success"
        obs_detail = f"status={receipt.status} returncode={receipt.returncode} signed={bool(receipt.signature)}"
    except ProviderError as exc:
        obs_detail = f"provider_error: {exc}"
    # The micro-eval is a LOAD-BEARING precondition: if it failed, fold that
    # into the observation so a green provider run cannot mask a failed eval.
    micro_failed = not micro.ok
    if micro_failed and receipt is not None:
        # Demote the recorded run status so the gate (code-owned) rejects it.
        # We do NOT fabricate a pass: a failing micro-eval poisons the run.
        receipt.status = "blocked"
        receipt.tests.append(
            TestRecord(
                name="bounded_micro_eval",
                command=["bounded_micro_eval"],
                returncode=1,
                passed=False,
                could_fail=True,
                detail=micro.detail,
            )
        )
        # re-NOTARIZE so the demoted status is covered by the signature. The orchestrator's
        # untrusted-output path does NOT sign and does NOT import a signing key -- it hands the
        # mutated UNSIGNED observation back to the notary (the only signer). This keeps the
        # executor/notary boundary intact even on the status-demotion branch.
        from .notary import Notary

        receipt.signature = None
        _nt = Notary()
        _nt.register(receipt.produced_by or "")
        _nt.notarize(receipt)
        if receipt_path is not None:
            write_receipt(receipt, receipt_path)
        obs_ok = False
        obs_detail += " | micro_eval_failed -> status demoted to blocked"
    stages.append(
        StageStep(
            stage="typed_observation",
            ok=obs_ok,
            could_fail=True,
            detail=obs_detail,
            data={
                "status": receipt.status if receipt else None,
                "signed": bool(receipt.signature) if receipt else False,
                "produced_by": receipt.produced_by if receipt else None,
            },
        )
    )

    # If we could not even produce a receipt, terminate as keep_scratch (nothing
    # to gate / promote) and record the remaining stages as not-run.
    if receipt is None:
        for nm in ("code_owned_scorer", "gateproof", "semantic_control"):
            stages.append(StageStep(stage=nm, ok=False, could_fail=False, detail="no receipt produced"))
        return CandidateRun(
            task_id=task.task_id,
            stages=stages,
            receipt=None,
            gate_result=None,
            semantic_verdict=SEMANTIC_KEEP_SCRATCH,
            admitted=False,
            receipt_path=str(receipt_path) if receipt_path else None,
        )

    # --- Stage 4: code_owned_scorer (the gate owns the score) ---
    gate_result = gate(receipt, audit_receipts=audit_receipts)
    divergence = [c for c in gate_result.checks if c.get("could_fail") and not c.get("passed")]
    stages.append(
        StageStep(
            stage="code_owned_scorer",
            ok=gate_result.admitted,
            could_fail=True,
            detail=f"verdict={gate_result.verdict} granted_rung={gate_result.granted_rung}",
            data={
                "verdict": gate_result.verdict,
                "admitted": gate_result.admitted,
                "granted_rung": gate_result.granted_rung,
                "reasons": list(gate_result.reasons),
                "divergence_checks": divergence,
            },
        )
    )

    # --- Stage 5: gateproof (collect checks + verify signature) ---
    signature_ok = verify_payload(receipt.to_dict())
    author_named = bool(normalize_identity(receipt.produced_by))
    gateproof_ok = signature_ok and all(
        c["passed"] for c in gate_result.checks if c.get("could_fail")
    )
    stages.append(
        StageStep(
            stage="gateproof",
            ok=gateproof_ok,
            could_fail=True,
            detail=f"signature_ok={signature_ok} author_named={author_named}",
            data={
                "signature_ok": signature_ok,
                "author_named": author_named,
                "checks": [dict(c) for c in gate_result.checks],
            },
        )
    )

    # --- Stage 6: semantic_control (verdict == gate verdict; never re-decided) ---
    admitted = gate_result.admitted  # NEVER recomputed by the orchestrator
    if admitted:
        verdict = SEMANTIC_ADMIT
    elif not signature_ok:
        # unsigned / forged / hand-edited receipt: cannot be promoted, kept as scratch.
        verdict = SEMANTIC_KEEP_SCRATCH
    else:
        # validly signed but the gate rejected on a real check (status/compile/etc.)
        verdict = SEMANTIC_REJECT
    stages.append(
        StageStep(
            stage="semantic_control",
            ok=admitted,
            could_fail=True,
            detail=f"semantic_verdict={verdict} (== gate.admitted={admitted})",
            data={
                "semantic_verdict": verdict,
                "gate_admitted": admitted,
                "gate_verdict": gate_result.verdict,
            },
        )
    )

    return CandidateRun(
        task_id=task.task_id,
        stages=stages,
        receipt=receipt,
        gate_result=gate_result,
        semantic_verdict=verdict,
        admitted=admitted,
        receipt_path=str(receipt_path) if receipt_path else None,
    )
