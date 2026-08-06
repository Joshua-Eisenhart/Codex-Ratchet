# Version policy

The stack version and component versions are independent.

- `system_v9/VERSION` identifies the repository release spine.
- Every product root has its own `VERSION` file.
- A bridge schema has its own schema version and may evolve without forcing a
  component major version.
- `devN` versions are runnable candidates, not release or promotion claims.
- Existing receipts keep their producer version and source hash. V9 never
  rewrites an old receipt merely to make it look current.
- A component version changes only when that component's public interface,
  packaging, or behavior changes. A stack release records the exact component
  versions it assembles.

ClaimGate, Sim Engines, and Holodeck had no authoritative product version in
the audited tree. Their `0.1.0.dev1` values are explicitly the first repository
versions, not a claim about earlier archive numbering.
