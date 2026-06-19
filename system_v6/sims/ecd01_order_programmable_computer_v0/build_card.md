# BUILD CARD - ecd01_order_programmable_computer_v0

Repo: `/Users/joshuaeisenhart/Codex-Ratchet`

Build scope: `system_v6/sims/ecd01_order_programmable_computer_v0/` only. File-disjoint packet.
No `git add`; no commit.

Ceiling: `capability_discriminator_only`.

Authority:

- Capability registry: `system_v6/receipts/engine_capability_differentiators_20260612.md`
  at commit `7c3f4b48d`, ECD.01 section and baseline contract.
- Axis-4 fixture: `system_v6/sims/discrete_axis4_composition_v0/` at commit `99c4f84b3`.
- Szilard baseline: `system_v6/sims/carnot_szilard_landauer_ledger_v1/`.

Discriminator:

- Same finite carrier as the committed Axis-4 fixture.
- Realize distinct pinned stage orders using the same primitive channel pair.
- Compute the resulting finite channels and the pairwise channel-distance diversity matrix.
- The capability metric is the pair `(distinct_channel_count, pairwise_positive_distance_count)`.
- The plain single-loop Szilard baseline must produce strictly smaller diversity under its
  admissible stroke orderings; if it does not, this discriminator dies honestly.

Controls:

- Commuting-generator engine: diversity must collapse.
- Shuffled labels: channel diversity must survive relabeling, proving this is not label spelling.
- Falsifier reachable: if the Szilard distinct-channel count is not smaller, the packet must fail.

Standard contract:

- Three-engine lanes: Julia, JAX/Python, PyTorch.
- Use `scripts/build_three_engine_envelope.py`.
- Use `scripts/builder_audit_boundary.py`; builder emits no `audit_verdict.md`.
- `classification="scratch_diagnostic"`, `promotion_allowed=false`,
  `formal_admission_allowed=false`.
- Result must name allowed and disallowed claims explicitly.
