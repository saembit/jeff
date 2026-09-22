---
name: codex-research
description: Read only investigation on the cheapest Codex tier to map code, trace call paths, list usages or summarize how something works, never edits. Use when Jev routed to codex-research or for cheap 'find where X happens' lookups that would otherwise burn Claude context.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-research

Runs the task on codex at tier 0 with the read-only sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/codex-run. The task text has to say exactly what to report and in what shape such as a file:line table, a call graph, a prose summary, etc. Findings come back in the result's summary and notes, relay them without rereading the files yourself unless asked. Use --tier 1 for research that needs judgment and not just lookup.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 1800000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/codex-run" --tier 0 --sandbox read-only --cd "$PWD" --out "$WORK/result.json" - < "$WORK/task.txt"
```

3. Verify it

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-verify" --task "$(cat "$WORK/task.txt")" --result "$WORK/result.json" --diff-stat "$(git diff --stat)" --tier 0
```

4. pass means report the summary and files, escalate means rerun step 2 once with --tier set to next_tier, blocked means show the worker's notes to the user

Only override the tier with --model and --effort when the user asked for a specific model.
