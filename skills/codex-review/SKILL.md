---
name: codex-review
description: Read only code review on the mid Codex tier of a diff, branch or file set, returns findings and never edits. Use when Jev routed to codex-review or for 'have codex review this', 'second opinion on this diff'.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-review

Runs the task on codex at tier 1 with the read-only sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/codex-run. The task text has to name the scope, git diff main...HEAD, a file list or a directory, and ask for findings as path:line: severity: problem. fix. and nothing else. The sandbox is read only so the worker can't change anything and the verify step checks the review covered the scope.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 1800000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/codex-run" --tier 1 --sandbox read-only --cd "$PWD" --out "$WORK/result.json" - < "$WORK/task.txt"
```

3. Verify it

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-verify" --task "$(cat "$WORK/task.txt")" --result "$WORK/result.json" --diff-stat "$(git diff --stat)" --tier 1
```

4. pass means report the summary and files, escalate means rerun step 2 once with --tier set to next_tier, blocked means show the worker's notes to the user

Only override the tier with --model and --effort when the user asked for a specific model.
