# Portable plural host-hook candidate

This directory contains one host-neutral event envelope and four thin host
shims.  The adapter captures identifiers and digests, removes an unmanaged
host-process launch at a pre-tool boundary, relays typed proposal data as
observation, and preserves cancellation.  It does not evaluate a CB
operation, select a provider, or make a semantic disposition.

The seam is bound to an installed product root and an explicit contained Light
interpreter.  The shim itself is always policed by the fixed macOS bootstrap
`/usr/bin/python3`; the Light path is attested data, not the policing
executable.  It does not import from the source checkout or set `PYTHONPATH`:

```text
CB_PRODUCT_ROOT=/absolute/path/to/installed/product \
CB_LIGHT_PYTHON=/absolute/path/to/installed/product/.venv/bin/python \
CB_HOOK_EVENT_LOG=/absolute/path/to/installed/product/integrated_system/runs/hook-events.jsonl \
hooks/cb_hook.sh claude <payload.json
```

Events always append to the canonical ignored runtime path
`CB_PRODUCT_ROOT/integrated_system/runs/hook-events.jsonl`; ambient log
variables cannot redirect them into source or outside the product.  Each
accepted, refused, cancelled, or session event is one canonical, locked,
flushed, fsynced JSONL record.  A failed log write is fail-closed.

The Light path must be a lexical product-local `venv/bin/python` entrypoint
with a regular, non-symlink product-local `pyvenv.cfg`.  Its resolved target
may be the system native Python only under that valid venv identity; config,
entrypoint, target, and hook-source SHA-256 values are retained in binding and
event records.  Direct external interpreters, arbitrary shims, fake binaries,
config symlinks, and traversal hold.

Provider process ownership comes only from a matching, product-confined
dispatch lease and on-disk nonce.  A CB-looking command name or module name is
not ownership evidence.  The bounded classifier recognizes literal common
shell/Python process forms; dynamic generated code remains unclassified.

Hermes `on_session_end` with `extra.interrupted=true` is captured as
`CANCELLED_NO_AUTHORITY` and emits Hermes' passive `{"action":"allow"}` wire
with a nonblocking return code; this is lifecycle evidence, not a Hermes stop
veto.  Only `pre_tool_call` can emit a Hermes block.

`portable_host_hook.py` emits a stable envelope when called with
`--print-envelope`.  Without that option it emits only a host-native denial
wire when authority must be removed; ordinary passthrough remains silent.

`templates/` contains the Codex, Claude Code, Grok CLI, and Hermes entrypoint
templates.  Set `CB_HOOK_ROOT` to this installed hooks directory and retain
the two explicit bindings above before connecting a host.  Existing
`claude/hooks/` files are compatibility wrappers around the same seam.

The contained installer has four explicit modes.  `plan` is the default and
never mutates a path; `apply`, `verify`, and `rollback` require explicit
staged host-root/config paths and keep their backups/receipts under the
ignored product runtime area `integrated_system/runs/host-hook-installer/`.

The staged config inventory is strict: Codex uses `.codex/hooks.json`, Claude
uses `.claude/settings.json` (or `settings.local.json`), Grok uses JSON hook
files under `.grok/hooks/` (with the staged `hooks.json` fixture form), and
Hermes uses `.hermes/config.yaml`/`.yml`.  Scalar roots, duplicate JSON/YAML
keys, unsupported extensions, and raw parser failures are refused.

When direct Grok and global Claude hooks share a staged host root, pass the
explicit canonical `--grok-compat-config <host-root>/.grok/config.toml` target.
The installer updates only `[compat.claude] hooks = false`; without that target
it holds with `HOLD_GROK_DOUBLE_EXECUTION`.  The TOML target is backed up,
hashed, verified, and rolled back like every other target.

`--force-migration` is limited to recognized old canonical-checkout
`constraint_box/hooks/universal/cb_hook.sh <host>` entries (including the old
Hermes managed form).  It requires repeated explicit bindings of the form
`--legacy-hook-source HOST=/.../Codex-Ratchet/constraint_box/hooks/universal/cb_hook.sh`,
`--legacy-hook-source-sha256 HOST=SHA256`, and
`--legacy-hook-source-mode HOST=MODE`; those path/hash/mode bindings are sealed
into the plan.  Foreign, lookalike, substring, symlink, fake, or other-checkout
commands remain untouched and cause a hold.
Force migration also requires the legacy source checkout and the new product
checkout/worktree to resolve to the same canonical Git common directory and
repository identity; that identity digest is sealed into the plan and checked
again on apply, replay, verify, and rollback.

```text
python3 hooks/host_hook_installer.py plan \
  --product-root /absolute/path/to/installed/product \
  --light-interpreter /absolute/path/to/installed/product/.venv/bin/python \
  --host-root claude=/absolute/path/to/staged-home \
  --config claude=/absolute/path/to/staged-home/.claude/settings.json
```

`apply` backs up each changed config before an atomic file+directory-fsynced
replace, preserves unrelated settings/hooks, records before/after/backup
hashes, and restores already-written targets if a later write is interrupted.
It consumes the sealed `plan` JSON (`--plan /path/to/plan.json`) and refuses a
missing, forged, HOLD, stale, or run-id-mismatched plan; applying the same plan
again replays the original receipt without replacing its backup authority.
Receipts self-digest their plan/run/mode/path/hash/mode bindings and never
overwrite an existing run id.  `verify` refuses source/script chmod drift,
config/backup tamper, duplicate managed entries, and target escapes.
`rollback` accepts only an untampered `APPLIED` receipt and refuses to overwrite
an externally changed target.  The installer never reads credential paths or
launches providers.

Verification and rollback require the caller to retain both sealed artifacts
and their expected digests:

```text
python3 hooks/host_hook_installer.py verify \
  --plan /staged/plan.json --expected-plan-sha256 PLAN_SHA256 \
  --receipt /product/integrated_system/runs/host-hook-installer/RUN/receipt.json \
  --expected-receipt-sha256 RECEIPT_SHA256
```

The compatibility wrapper `install_plan.py` retains the historical plan API
and dispatches these same mode names when the first argument is `plan`,
`apply`, `verify`, or `rollback`.

The original plan-only surface remains available:

```text
python3 hooks/install_plan.py \
  --product-root /absolute/path/to/installed/product \
  --light-interpreter /absolute/path/to/installed/product/.venv/bin/python \
  --target-root /absolute/path/to/review-target
```

The command prints intended template/binding changes and never writes the
target or any current home configuration.  It returns `HOLD` when the venv,
source, bootstrap, or other explicit runtime binding is absent.

Claim ceiling: candidate source and fixture tests only; no host activation,
provider execution, promotion, or semantic CB admission.
