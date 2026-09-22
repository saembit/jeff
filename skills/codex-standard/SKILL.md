---
name: codex-standard
description: Mid Codex tier (tier 1, medium reasoning) for routine work such as unit tests, small features with a clear spec, known cause bug fixes, doc sync, small refactors, etc. Use when Jev routed to tier 1 / codex-standard or for well specified work in one to three files.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-standard

Runs the task on codex at tier 1 with the workspace-write sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/jeff-work, which runs codex-run, verifies with jev-verify and escalates one tier on a miss. Good for tests against an existing function, a described feature in a couple of files or a bug whose cause is already known. Put the acceptance criteria and the test command in the task text.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 3600000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jeff-work" --tier 1 --sandbox workspace-write --cd "$PWD" - < "$WORK/task.txt"
```

3. Relay the report block it prints. VERDICT pass means done, escalate means it already retried one tier up and still missed so show the summary and notes to the user, blocked means the worker left a question so show the notes

Only override the tier with --tier when the user asked for a specific model, the tier to model mapping is in lib/registry.json.
