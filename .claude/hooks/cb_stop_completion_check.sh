#!/bin/bash
# Stop fires at EVERY turn end, not only on a "done" claim. Blocking here (exit 2)
# made the session unusable: every reply was refused and the JSON receipt was
# printed back into the transcript.
#
# The check still runs and still writes its receipt to the hash chain, so the
# open-holds record is unchanged and auditable. It just does not block the turn
# and does not print. Read the state with:
#   python3 -m constraint_box.hookkernel.kernel task_completion_claimed --payload-json '{}'
#
# The hard block belongs on an explicit completion-claim event, not on Stop.
input=$(cat)
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
  -m constraint_box.hookkernel.kernel task_completion_claimed \
  --payload-json "$input" >/dev/null 2>&1
exit 0
