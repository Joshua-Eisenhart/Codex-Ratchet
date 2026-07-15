# Provider Advisory Control v1

This is the repo-held control boundary for NVIDIA NIM and xAI advisory lanes.
It does not call completions and it can never open a Ratchet gate.

The catalog command discovers exact model IDs from the provider's current
/models endpoint. The preflight command compares one exact model against a
current catalog, an owner-supplied account/model quota policy, and a local
request ledger. Missing or stale catalog data, an absent model, an unknown
limit, or exhausted quota always returns HOLD.

No universal NVIDIA or xAI free-tier rate is encoded. The authority is the
owner's account/team console or observed response headers. This avoids turning
forum guidance or an old model catalog into dispatch policy.

Fixture-only validation:

    python3 -m pytest -q system_v5/ops/tooling/provider_advisory_control_v1/test_provider_advisory_control.py

A live catalog refresh is read-only and zero-inference:

    python3 system_v5/ops/tooling/provider_advisory_control_v1/provider_advisory_control.py catalog \
      --provider nvidia \
      --out /tmp/nvidia-catalog-receipt.json

Every receipt carries advisory_only=true, gate_authority=false,
evidence_allowed=false, and all promotion/admission/science flags false. The
independent validator rejects a receipt if any of those fences opens.
