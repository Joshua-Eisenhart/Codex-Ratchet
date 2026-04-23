# Telegram One-Shot Run Prompt

Use this as the model for a manual Telegram launch.

Default rule:
- the launch message should usually specify duration, run intent, and reporting
- Hermes should select work from the live queue/control surfaces by default
- the user should only specify the exact task when intentionally overriding the queue

Recommended minimal template:

"Run for <DURATION> minutes from the live queue. Report progress and health."

Expanded template:

"Run for <DURATION> minutes from the live queue on Codex Ratchet. Use Hermes as controller. Keep geometry-before-axis. Use one primary lane plus one maintenance lane. Use Claude Code sonnet low if useful. Send launch acknowledgement, periodic progress and health updates, and a final audit closeout. Continuity should come from the repo control surfaces and wiki, not from vague memory alone. Avoid system bloat."

Examples:

1. "Run for 1 hour from the live queue. Report progress and health."

2. "Run for 1 hour from the live queue. Use the plan. Report progress and health."

3. "Do a 60-minute bounded run from the live queue. Report progress and health."

4. "Run for 1 hour from the live queue. Geometry-first. Report progress and health."

5. "Run for 1 hour from the live queue. Maintenance-heavy. Report progress and health."

6. "Run for 1 hour from the live queue. Use Claude Code if useful. Report progress and health."
