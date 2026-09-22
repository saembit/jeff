# jeff

![my name is jeff](assets/my-name-is-jeff.jpg)

Jev routed multi model orchestration for Claude Code

# TOC
- [About](#about)
- [How it works](#how-it-works)
- [Tiers](#tiers)
- [Setup](#setup)
- [Use](#use)
- [Layout](#layout)
- [Tuning](#tuning)

# About

jeff is a Claude Code plugin that came from being annoyed at paying frontier model prices for renames, docstrings, lookups, etc. that a cheap model would do fine. It uses Jev, the System One model from TypeSafe, to look at every subtask and decide what tier of model it needs, whether it should run on Claude or on Codex, which skill fits, whether it needs write access and whether it can run in parallel with the other subtasks. Jev doesn't plan or write code, it answers typed questions with a probability in under a second for a fraction of a cent, so the routing is fast and cheap enough to run on every subagent spawn. It may not route perfectly but it's better than sending everything to the biggest model.

# How it works

Claude breaks the task into subtasks, jev-route asks Jev about all of them in one request, the workers run (Claude subagents or codex exec) and jev-verify asks Jev if each result actually did the task. A miss gets escalated one tier and rerun, a worker that leaves an open question gets flagged for you, and anything Jev rates as destructive such as dropping tables, force pushing, etc. never runs without asking first.

# Tiers

| Tier | Claude | Codex | What goes here |
|---|---|---|---|
| 0 trivial | haiku, low | gpt-5.6-terra, low | renames, docstrings, lookups, formatting |
| 1 routine | sonnet, medium | gpt-5.6-sol, medium | tests, small features, known cause fixes, review |
| 2 hard | opus, high | gpt-6-astra, high | multi file refactors, unknown cause debugging |
| 3 frontier | fable, xhigh | gpt-6-astra, xhigh | architecture, security, ambiguous specs |

The tier is the difficulty Jev picks, minus one when a wrong answer is cheap to redo and plus one when it's expensive. Provider defaults to Codex whenever the task is self contained so Claude quota is saved for the work that needs the conversation, change policy.provider_preference in lib/registry.json to claude or balanced if you want it the other way.

# Setup

1. Put your TypeSafe key in ~/.config/typesafe/env as export TYPESAFE_API_KEY=... (chmod 600) and source it from your shell, or store it with pass as typesafe/api-key
2. Have the codex cli on PATH and logged in, this is optional and without it everything routes to the Claude tiers
3. Install the plugin

```
claude plugin marketplace add saembit/jeff
claude plugin install jeff@jeff
```

For local dev symlink the repo at ~/.claude/skills/jeff instead and it loads as jeff@skills-dir, don't do both or every skill shows up twice.

# Use

/jeff followed by a task runs the whole loop, decompose, route, dispatch, verify. The codex-quick, codex-standard, codex-deep, codex-review and codex-research skills can be called on their own when you already know what you want. With JEFF_HOOK=on in your environment every plain Agent spawn gets routed by the hook too, it's opt in because rerouting everything is a lot for a default, and JEFF:PIN in a prompt leaves that one call alone.

# Layout

- bin/jev-route, subtasks json in and a decision per subtask out
- bin/jev-verify, task and result in and pass, escalate or blocked out
- bin/codex-run, wraps codex exec with the tier's model and effort, the sandbox and an output schema
- bin/jeff-work, runs codex-run then jev-verify, escalates one tier on a miss, keeps every attempt's files and prints the report block
- lib/registry.json, tiers, thresholds and the skill catalog, this is what Jev reads
- lib/result.schema.json, the shape every worker has to return
- SKILL.md, the /jeff skill
- skills/codex-*, the five codex skills
- agents/codex-worker.md, bash only subagent that runs jeff-work
- hooks/route-agent.py, the PreToolUse hook
- tests/tasks.json and tests/route-eval.py, labeled routing cases and the script that scores them

The scripts in bin will move into [jeff-cli](https://github.com/saembit/jeff-cli) once that exists and this plugin will just be the skills, the agent and the hook.

# Tuning

Everything Jev reads is plain text in lib/registry.json, the tier descriptions, the redo_cost and risk levels and the skill catalog. Change the wording, run tests/route-eval.py and see what moved. The 12 seed tasks currently score 75% exact tier, 92% within one, 75 to 83% provider depending on the run, 100% writes and 100% risk on about 14k Jev input tokens per run. Add a case to tests/tasks.json whenever a routing surprises you.
