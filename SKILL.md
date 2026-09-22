---
name: jeff
description: Orchestrate a multi part task with Jev picking the model tier, provider (Claude or Codex), skill, sandbox and parallelism for each subtask so cheap work goes to cheap models. Use for "/jeff <task>", "orchestrate this", "split this up and route it", "use the cheapest model that can do this", "farm this out to codex" or any request to run subtasks in parallel across models.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/*) Bash(git *) Read Agent Workflow
---

# jeff

Jev answers typed questions with probabilities, it doesn't plan or write code. You decompose, Jev routes, workers run, Jev verifies. The scripts are in ${CLAUDE_PLUGIN_ROOT}/bin and the registry is ${CLAUDE_PLUGIN_ROOT}/lib/registry.json.

# Decompose

Break $ARGUMENTS (or the task in context) into 2 to 12 subtasks that a fresh agent could do with just the repo and the text. Include files when you know them since Jev uses them for conflict detection, include depends_on only for real ordering needs, and don't add a review everything subtask since verify is built in. A single small task is just one subtask.

```json
{"subtasks": [
  {"id": "s1", "title": "...", "description": "...", "files": ["src/a.py"], "depends_on": []}
]}
```

# Route

Write the json to a temp file and run it through the router.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-route" < subtasks.json
```

Every decision has tier, provider, model, effort, skill, sandbox, parallel_group, risk, require_approval, confidence and fallback. The fallback list is the fields Jev wasn't sure about, decide those yourself and say why in a line. Anything with require_approval true gets asked about before it runs, never auto run destructive work. Don't second guess the confident decisions, if you disagree say so in a line and follow it anyway unless it's unsafe.

# Dispatch

Run the parallel group at the same time and the serial ones in depends_on order after. For codex subtasks spawn jeff:codex-worker with this prompt, the header first and the subtask text after it.

```
JEFF ROUTE tier=<tier> (<tier_name>) provider=codex model=<model> effort=<effort> skill=<skill> sandbox=<sandbox> risk=<risk> require_approval=false confidence=<confidence> fallback=none bin=${CLAUDE_PLUGIN_ROOT}/bin cwd=<repo path>

<subtask description plus file hints>
```

Two codex workers writing the same tree collide, so for parallel writers pass isolation worktree on the Agent call and merge after. For claude subtasks spawn an Agent with model set to the decision's model (haiku, sonnet, opus, fable) and put JEFF:PIN in the prompt so the hook doesn't route it again. More than 4 subtasks or a mix of parallel and serial is a job for the Workflow tool, same prompt shape per agent call, label each one id:provider:model.

# Verify and merge

Codex workers verify themselves and escalate one tier on a miss. For claude workers write the result as ${CLAUDE_PLUGIN_ROOT}/lib/result.schema.json and run verify.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/jev-verify" --task "<text>" --result result.json --diff-stat "$(git diff --stat)" --tier <tier>
```

escalate means rerun on next_tier, blocked means show the worker's notes to the user.

# Report

One table with subtask, provider, model, verdict and files, then anything blocked, then the total Jev input tokens from the raw field. Don't narrate the routing.

# Tuning

Routing quality comes from the text in lib/registry.json, the tier describe fields, redo_cost, risk and the skills. Change the wording there and run tests/route-eval.py. policy.provider_preference can be claude, codex or balanced.
