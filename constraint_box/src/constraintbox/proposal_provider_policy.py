"""Controller-owned route selection for untrusted proposal generators.

The selected provider can generate candidate bytes only.  It never selects a
ConstraintBox tool, gate, retry, terminal state, ClaimGate outcome, or claim
scope.  A system operator may select one pre-registered route before startup
through an environment value; neither a user request nor model output is read
by this module.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .intake import canonical_json


POLICY_SCHEMA = "constraintbox.proposal-provider-policy.v1"
ROUTE_ENV = "CONSTRAINTBOX_PROPOSAL_PROVIDER"
DEFAULT_ROUTE = "local_tool"
MAX_TOKENS = 768
TEMPERATURE = 0.0


class ProposalProviderPolicyError(ValueError):
    """The fixed provider policy cannot safely resolve a proposal route."""


@dataclass(frozen=True)
class ProposalProviderRoute:
    route: str
    component_key: str
    requested_model: str
    credential_env: str | None
    selection_basis: str


@dataclass(frozen=True)
class ProposalProviderSelection:
    """One resolved controller route, excluding credential material."""

    route: ProposalProviderRoute
    provider: Any
    policy_sha256: str
    policy_source_sha256: str
    operator_selected: bool

    def public_binding(self) -> dict[str, Any]:
        return {
            "schema": POLICY_SCHEMA,
            "route": self.route.route,
            "component_key": self.route.component_key,
            "requested_model": self.route.requested_model,
            "credential_env": self.route.credential_env,
            "credential_configured": self.route.credential_env is not None,
            "selection_basis": self.route.selection_basis,
            "operator_selected": self.operator_selected,
            "policy_sha256": self.policy_sha256,
            "policy_source_sha256": self.policy_source_sha256,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "llm_decision_authority": False,
            "promotion_allowed": False,
        }


ROUTES: Mapping[str, ProposalProviderRoute] = MappingProxyType(
    {
        # The old requested_model "codex-cli-default" was a placeholder that
        # named no real model: the dispatch carried no ``-m``, codex silently
        # picked its default, and the receipt's declaration could never be
        # checked against bytes.  Measured 2026-08-08 on this machine: the
        # unpinned default resolves to gpt-5.6-sol.  The route now REQUESTS
        # that model explicitly and the dispatch binds it with ``-m`` (CLI
        # enforced; an unknown slug returns HTTP 400), so the rollout
        # observation can confirm or refute the request.
        "local_tool": ProposalProviderRoute(
            route="local_tool",
            component_key="LocalToolProvider",
            requested_model="gpt-5.6-sol",
            credential_env=None,
            selection_basis="default_static_controller_route",
        ),
        "openrouter": ProposalProviderRoute(
            route="openrouter",
            component_key="OpenRouterProvider",
            requested_model="openrouter/free",
            credential_env="OPENROUTER_API_KEY",
            selection_basis=(
                "explicit_operator_runtime_route_from_static_controller_registry"
            ),
        ),
        "nvidia": ProposalProviderRoute(
            route="nvidia",
            component_key="NvidiaProvider",
            requested_model="nvidia/nemotron-3-nano-30b-a3b",
            credential_env="NVIDIA_API_KEY",
            selection_basis=(
                "explicit_operator_runtime_route_from_static_controller_registry"
            ),
        ),
        # Codex CLI authenticates from its own CODEX_HOME, so this box holds no
        # credential for it: credential_env is None and that is the honest value,
        # not a missing one. The model is bound with `-m`, which the CLI enforces
        # (an unknown slug returns HTTP 400). `-p`/`--profile` is deliberately NOT
        # used: it accepts any string and silently falls back to the default
        # model, which would put a lane name on a receipt for a lane that never
        # ran. Measured 2026-08-08: `-p luna` and `-p <nonsense>` both returned
        # gpt-5.6-sol.
        "codex_luna": ProposalProviderRoute(
            route="codex_luna",
            component_key="CodexLunaProvider",
            requested_model="gpt-5.6-luna",
            credential_env=None,
            selection_basis=(
                "explicit_operator_runtime_route_from_static_controller_registry"
            ),
        ),
        "codex_sol": ProposalProviderRoute(
            route="codex_sol",
            component_key="CodexSolProvider",
            requested_model="gpt-5.6-sol",
            credential_env=None,
            selection_basis=(
                "explicit_operator_runtime_route_from_static_controller_registry"
            ),
        ),
    }
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _policy_body(route: ProposalProviderRoute) -> dict[str, Any]:
    return {
        "schema": POLICY_SCHEMA,
        "route": route.route,
        "component_key": route.component_key,
        "requested_model": route.requested_model,
        "credential_env": route.credential_env,
        "selection_basis": route.selection_basis,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "route_env": ROUTE_ENV,
        "route_env_is_not_request_or_model_input": True,
        "llm_decision_authority": False,
        "promotion_allowed": False,
    }


def route_policy_sha256(route: ProposalProviderRoute) -> str:
    """Return the exact static policy digest for one registered route."""

    if not isinstance(route, ProposalProviderRoute):
        raise ProposalProviderPolicyError("proposal route must be controller-owned")
    return _sha256(canonical_json(_policy_body(route)))


def _source_sha256() -> str:
    try:
        return _sha256(Path(__file__).read_bytes())
    except OSError as exc:
        raise ProposalProviderPolicyError(
            f"proposal-provider policy source is unavailable: {exc}"
        ) from exc


def select_proposal_provider(
    components: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
) -> ProposalProviderSelection:
    """Resolve one pre-registered provider without a request/model override.

    An explicit operator route never silently falls back to the local Codex
    route: a missing credential therefore parks the caller rather than spending
    another provider's quota or changing the declared route.
    """

    if not isinstance(components, Mapping):
        raise ProposalProviderPolicyError("provider components must be a mapping")
    environment = os.environ if environ is None else environ
    raw_route = environment.get(ROUTE_ENV)
    if raw_route is None:
        route_name = DEFAULT_ROUTE
        operator_selected = False
    elif not isinstance(raw_route, str) or raw_route not in ROUTES:
        raise ProposalProviderPolicyError(
            f"{ROUTE_ENV} must be one fixed route: {sorted(ROUTES)}"
        )
    else:
        route_name = raw_route
        operator_selected = True
    route = ROUTES[route_name]
    factory = components.get(route.component_key)
    if not callable(factory):
        raise ProposalProviderPolicyError(
            f"registered provider component is unavailable: {route.component_key}"
        )
    if route.credential_env is None:
        provider = factory()
    else:
        api_key = environment.get(route.credential_env)
        if not isinstance(api_key, str) or not api_key:
            raise ProposalProviderPolicyError(
                f"registered provider route requires {route.credential_env}"
            )
        provider = factory(api_key=api_key)
    if getattr(provider, "name", None) != route.route:
        raise ProposalProviderPolicyError(
            "registered provider identity differs from the selected controller route"
        )
    return ProposalProviderSelection(
        route=route,
        provider=provider,
        policy_sha256=route_policy_sha256(route),
        policy_source_sha256=_source_sha256(),
        operator_selected=operator_selected,
    )
