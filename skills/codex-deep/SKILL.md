---
name: codex-deep
description: Top Codex tier (tier 2 high reasoning, tier 3 xhigh) for hard work such as multi file refactors, unknown cause debugging, integration, security sensitive changes, etc. Use when Jev routed to tier 2 or 3 / codex-deep or when a cheaper tier escalated.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-deep

Runs the task on codex at tier 2 with the workspace-write sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/jeff-work, which runs codex-run, verifies with jev-verify and escalates one tier on a miss. Good for investigation heavy tasks, cross cutting refactors and root causing flaky failures. For tier 3 work (architecture, security, ambiguous spec) pass --tier 3 for xhigh reasoning. Runs take several minutes, don't interrupt them.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 3600000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jeff-work" --tier 2 --sandbox workspace-write --cd "$PWD" - < "$WORK/task.txt"
```

3. Relay the report block it prints. VERDICT pass means done, escalate means it already retried one tier up and still missed so show the summary and notes to the user, blocked means the worker left a question so show the notes

Only override the tier with --tier when the user asked for a specific model, the tier to model mapping is in lib/registry.json.
