---
name: codex-deep
description: Top Codex tier (tier 2 high reasoning, tier 3 xhigh) for hard work such as multi file refactors, unknown cause debugging, integration, security sensitive changes, etc. Use when Jev routed to tier 2 or 3 / codex-deep or when a cheaper tier escalated.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-deep

Runs the task on codex at tier 2 with the workspace-write sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/codex-run. Good for investigation heavy tasks, cross cutting refactors and root causing flaky failures. For tier 3 work (architecture, security, ambiguous spec) pass --tier 3 for xhigh reasoning. Runs take several minutes, don't interrupt them.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 1800000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/codex-run" --tier 2 --sandbox workspace-write --cd "$PWD" --out "$WORK/result.json" - < "$WORK/task.txt"
```

3. Verify it

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-verify" --task "$(cat "$WORK/task.txt")" --result "$WORK/result.json" --diff-stat "$(git diff --stat)" --tier 2
```

4. pass means report the summary and files, escalate means rerun step 2 once with --tier set to next_tier, blocked means show the worker's notes to the user

Only override the tier with --model and --effort when the user asked for a specific model.
