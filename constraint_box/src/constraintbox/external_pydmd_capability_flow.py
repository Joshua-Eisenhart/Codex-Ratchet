"""Caller-reachable Mini-Lev wrapper for the fixed external PyDMD profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .external_s3_capability import PYDMD_PROFILE
from .external_s3_capability_flow import (
    ExternalS3CapabilityFlowError,
    _FLOW_NAMES,
    _run_s3_capability_flow,
)


CAPABILITY_RECEIPT_NAME = _FLOW_NAMES[PYDMD_PROFILE.capability_id]["receipt"]
FLOW_RECEIPT_NAME = _FLOW_NAMES[PYDMD_PROFILE.capability_id]["flow_receipt"]
FLOW_LEDGER_NAME = _FLOW_NAMES[PYDMD_PROFILE.capability_id]["ledger"]
ExternalPyDMDCapabilityFlowError = ExternalS3CapabilityFlowError


def run_pydmd_capability_flow(*, request_id: str, run_root: Path) -> dict[str, Any]:
    return _run_s3_capability_flow(PYDMD_PROFILE, request_id=request_id, run_root=run_root)
