---
name: codex-quick
description: Cheapest Codex tier (tier 0, low reasoning) for mechanical edits such as renames, typos, docstrings, formatting, one line fixes, commit messages, etc. Use when the task is obvious and easy to check or when Jev routed to tier 0 / codex-quick.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-quick

Runs the task on codex at tier 0 with the workspace-write sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/codex-run. Good for symbol renames across files, docstrings, formatting and trivial fixes where the diff is obviously right, not for anything that needs investigation. If the task turns out to need judgment the verify step escalates it.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 1800000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/codex-run" --tier 0 --sandbox workspace-write --cd "$PWD" --out "$WORK/result.json" - < "$WORK/task.txt"
```

3. Verify it

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-verify" --task "$(cat "$WORK/task.txt")" --result "$WORK/result.json" --diff-stat "$(git diff --stat)" --tier 0
```

4. pass means report the summary and files, escalate means rerun step 2 once with --tier set to next_tier, blocked means show the worker's notes to the user

Only override the tier with --model and --effort when the user asked for a specific model.
