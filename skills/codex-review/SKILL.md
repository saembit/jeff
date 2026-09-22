---
name: codex-review
description: Read only code review on the mid Codex tier of a diff, branch or file set, returns findings and never edits. Use when Jev routed to codex-review or for 'have codex review this', 'second opinion on this diff'.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-review

Runs the task on codex at tier 1 with the read-only sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/jeff-work, which runs codex-run, verifies with jev-verify and escalates one tier on a miss. The task text has to name the scope, git diff main...HEAD, a file list or a directory, and ask for findings as path:line: severity: problem. fix. and nothing else. The sandbox is read only so the worker can't change anything and the verify step checks the review covered the scope.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 3600000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jeff-work" --tier 1 --sandbox read-only --cd "$PWD" - < "$WORK/task.txt"
```

3. Relay the report block it prints. VERDICT pass means done, escalate means it already retried one tier up and still missed so show the summary and notes to the user, blocked means the worker left a question so show the notes

Only override the tier with --tier when the user asked for a specific model, the tier to model mapping is in lib/registry.json.
