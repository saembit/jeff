---
name: codex-research
description: Read only investigation on the cheapest Codex tier to map code, trace call paths, list usages or summarize how something works, never edits. Use when Jev routed to codex-research or for cheap 'find where X happens' lookups that would otherwise burn Claude context.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read
---

# codex-research

Runs the task on codex at tier 0 with the read-only sandbox through ${CLAUDE_PLUGIN_ROOT}/bin/jeff-work, which runs codex-run, verifies with jev-verify and escalates one tier on a miss. The task text has to say exactly what to report and in what shape such as a file:line table, a call graph, a prose summary, etc. Findings come back in the report's SUMMARY and NOTES lines, relay them without rereading the files yourself unless asked. Use --tier 1 for research that needs judgment and not just lookup.

# Run

1. Write the task text to a temp file with the file paths, the acceptance criteria and the repo's test command if you know it
2. Run it and let it finish, Bash timeout of at least 3600000 ms

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jeff-work" --tier 0 --sandbox read-only --cd "$PWD" - < "$WORK/task.txt"
```

3. Relay the report block it prints. VERDICT pass means done, escalate means it already retried one tier up and still missed so show the summary and notes to the user, blocked means the worker left a question so show the notes

Only override the tier with --tier when the user asked for a specific model, the tier to model mapping is in lib/registry.json.
