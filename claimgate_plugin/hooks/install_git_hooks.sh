#!/bin/bash
# Install the fired-side ClaimGate git hooks into this repo's .git/hooks/.
# Idempotent. The installed pre-commit is a thin wrapper that always execs the
# version-controlled script, so updates to the gate ship with the repo, not the
# untracked .git/hooks/ copy.
set -euo pipefail
repo=$(git rev-parse --show-toplevel)
hookdir="$repo/.git/hooks"
mkdir -p "$hookdir"

precommit="$hookdir/pre-commit"
if [[ -f "$precommit" ]] && ! grep -q "pre_commit_gate_receipts.sh" "$precommit" 2>/dev/null; then
  cp "$precommit" "$precommit.pre-claimgate.bak"
  echo "[install] backed up existing pre-commit -> pre-commit.pre-claimgate.bak"
fi

cat > "$precommit" <<'WRAP'
#!/bin/bash
# fired-side ClaimGate — execs the version-controlled gate (do not edit here)
exec bash "$(git rev-parse --show-toplevel)/claimgate_plugin/hooks/pre_commit_gate_receipts.sh"
WRAP
chmod +x "$precommit"
chmod +x "$repo/claimgate_plugin/hooks/pre_commit_gate_receipts.sh"
echo "[install] fired-side ClaimGate pre-commit installed -> $precommit"
echo "[install] every staged ratchet receipt is now gated at commit; REJECTED (exit 1) blocks the commit."
