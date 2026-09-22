---
name: codex-standard
description: Mid Codex tier (tier 1, medium reasoning) for routine work such as unit tests, small features with a clear spec, known cause bug fixes, doc sync, small refactors, etc. Use when Jev routed to tier 1 / codex-standard or for well specified work in one to three files.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-standard

Runs the task on codex at tier 1 with the workspace-write sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/codex-run. Good for tests against an existing function, a described feature in a couple of files or a bug whose cause is already known. Put the acceptance criteria and the test command in the task text.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 1800000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/codex-run" --tier 1 --sandbox workspace-write --cd "$PWD" --out "$WORK/result.json" - < "$WORK/task.txt"
```

3. Verify it

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-verify" --task "$(cat "$WORK/task.txt")" --result "$WORK/result.json" --diff-stat "$(git diff --stat)" --tier 1
```

4. pass means report the summary and files, escalate means rerun step 2 once with --tier set to next_tier, blocked means show the worker's notes to the user

Only override the tier with --model and --effort when the user asked for a specific model.
