# Clifford Edge Semantics Audit

- generated_utc: `2026-03-21T23:50:35Z`
- status: `ok`
- audit_only: `True`
- do_not_promote: `True`

## Safe Now
- Treat Clifford semantics as a read-only sidecar over admitted low-control relations only: DEPENDS_ON, EXCLUDES, STRUCTURALLY_RELATED, RELATED_TO.
- Use current scalar/string edge attributes only as carriers or source fields for future GA payload construction; keep canonical graph storage unchanged.
- Prefer clifford as the primary GA math sidecar now that it is installed and passes a live Cl(3) multivector check.
- Treat kingdon as an optional PyTorch-coupled bridge sidecar, not the primary semantic owner.

## Deferred Now
- Keep entropy_state, correlation_entropy, orientation_basis, clifford_grade, and obstruction_score as deferred edge payload fields rather than live canonical attributes.
- Keep any grade-specific or basis-specific encoding in sidecar packets or projections until an explicit edge payload schema lands.
- Keep SKILL edges out of GA semantics while skill-to-kernel seeding remains fail-closed.

## Forbidden Now
- Do not treat Clifford or GA structures as canonical graph storage.
- Do not attach GA semantics to OVERLAPS while that relation remains quarantined out of equal-weight topology.
- Do not use Clifford semantics as a workaround for missing owner-bound skill-to-kernel identity.

## Recommended Next Actions
- If the graph lane continues, land one bounded edge-payload-schema audit or probe over admitted low-control relations before any runtime mutation or training claim.
- Keep kingdon in optional bridge status until a concrete PyG-coupled payload path is needed.
- Hold run_real_ratchet dispatch/refactor debt in watch-only mode; it remains secondary to the current graph-side bounded tranche.

## Issues
- none
