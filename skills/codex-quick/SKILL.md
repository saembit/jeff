---
name: codex-quick
description: Cheapest Codex tier (tier 0, low reasoning) for mechanical edits such as renames, typos, docstrings, formatting, one line fixes, commit messages, etc. Use when the task is obvious and easy to check or when Jev routed to tier 0 / codex-quick.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-quick

Runs the task on codex at tier 0 with the workspace-write sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/jeff-work, which runs codex-run, verifies with jev-verify and escalates one tier on a miss. Good for symbol renames across files, docstrings, formatting and trivial fixes where the diff is obviously right, not for anything that needs investigation. If the task turns out to need judgment the verify step escalates it.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 3600000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jeff-work" --tier 0 --sandbox workspace-write --cd "$PWD" - < "$WORK/task.txt"
```

3. Relay the report block it prints. VERDICT pass means done, escalate means it already retried one tier up and still missed so show the summary and notes to the user, blocked means the worker left a question so show the notes

Only override the tier with --tier when the user asked for a specific model, the tier to model mapping is in lib/registry.json.
