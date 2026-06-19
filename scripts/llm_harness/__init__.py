"""Offline deterministic core of the LLM harness.

The DETERMINISTIC PRUNE layer of the inverted-tree engine: determinism applies
to the SELECTION (receipt schema, gate verdict, recorded test commands,
artifact hashes, accept/reject) -- NOT to model outputs.
"""
from __future__ import annotations

from .types import (
    RECEIPT_SCHEMA,
    VALID_CLASSIFICATIONS,
    VALID_STATUSES,
    GATE_CEILING_LADDER,
    CANONICAL_FINISH_REASONS,
    TaskSpec,
    ModelJob,
    ModelReceipt,
    TestRecord,
    GateResult,
    HarnessRun,
    sha256_text,
    sha256_bytes,
    canonicalize_content,
    content_canonical_hash,
    sandbox_config_hash,
)
from .providers import (
    Provider,
    ProviderError,
    FakeSuccessProvider,
    FakeFailureProvider,
    FakeTimeoutProvider,
    FakeMalformedProvider,
    LocalToolProvider,
    OpenRouterProvider,
    map_openrouter_response,
    OPENROUTER_ENDPOINT,
)
from .runner import run_job, write_receipt, canonical_receipt_json
# Importing notary registers the per-identity verification key resolver into signing.verify_payload
# (so gate() can verify per-identity signatures) AND is the ONLY signer in the harness.
from .notary import (
    Notary,
    KeyRegistry,
    NotarizeResult,
    key_id_for,
    DEFAULT_PRODUCER,
)
from .gates import gate
from .orchestrator import (
    run_candidate,
    CandidateRun,
    StageStep,
    STAGE_NAMES,
    SEMANTIC_ADMIT,
    SEMANTIC_REJECT,
    SEMANTIC_KEEP_SCRATCH,
    ORCH_SCHEMA,
)
from .controller_adapter import (
    receipt_to_controller_drop,
    write_controller_drop,
    load_controller_drop,
    drop_signature_verifies,
    controller_results_dir,
    DROP_SCHEMA,
)

__all__ = [
    "RECEIPT_SCHEMA",
    "VALID_CLASSIFICATIONS",
    "VALID_STATUSES",
    "GATE_CEILING_LADDER",
    "CANONICAL_FINISH_REASONS",
    "TaskSpec",
    "ModelJob",
    "ModelReceipt",
    "TestRecord",
    "GateResult",
    "HarnessRun",
    "sha256_text",
    "sha256_bytes",
    "canonicalize_content",
    "content_canonical_hash",
    "sandbox_config_hash",
    "Provider",
    "ProviderError",
    "FakeSuccessProvider",
    "FakeFailureProvider",
    "FakeTimeoutProvider",
    "FakeMalformedProvider",
    "LocalToolProvider",
    "OpenRouterProvider",
    "map_openrouter_response",
    "OPENROUTER_ENDPOINT",
    "run_job",
    "write_receipt",
    "canonical_receipt_json",
    "Notary",
    "KeyRegistry",
    "NotarizeResult",
    "key_id_for",
    "DEFAULT_PRODUCER",
    "gate",
    "run_candidate",
    "CandidateRun",
    "StageStep",
    "STAGE_NAMES",
    "SEMANTIC_ADMIT",
    "SEMANTIC_REJECT",
    "SEMANTIC_KEEP_SCRATCH",
    "ORCH_SCHEMA",
    "receipt_to_controller_drop",
    "write_controller_drop",
    "load_controller_drop",
    "drop_signature_verifies",
    "controller_results_dir",
    "DROP_SCHEMA",
]
