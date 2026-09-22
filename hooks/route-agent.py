#!/usr/bin/env python3
"""
route-agent
PreToolUse hook on the Agent tool that lets Jev pick the provider, model and tier

Only plain spawns get rerouted (no subagent_type or general-purpose), specialized agents
keep their own settings. Codex work gets the subagent swapped to jeff:codex-worker with a
routing header on the prompt, Claude work gets the model set. The decision is always attached
as additionalContext. Any error exits 0 with no output so the original call goes through.

Opt in with JEFF_HOOK=on. Put JEFF:PIN in a prompt to leave that call alone.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# The plugin root and the router script
ROOT = Path(__file__).resolve().parent.parent
ROUTER = ROOT / "bin" / "jev-route"
# The agent codex work gets sent to
WORKER_AGENT = "jeff:codex-worker"
# Subagent types that count as plain spawns
GENERIC_TYPES = {"", "general-purpose", "claude"}
# Prompts shorter than this aren't worth routing
MIN_PROMPT_CHARS = 40
# How long to wait on the router
ROUTE_TIMEOUT = 25


def log(msg: str) -> None:
    """
    log
    Appends a line to hook.log in the plugin data dir
    @param msg {str} - the line
    @return None
    """
    # Data dir from Claude Code or a local fallback
    data_dir = os.environ.get("CLAUDE_PLUGIN_DATA") or str(ROOT / ".jev")
    try:
        # Make the dir and append the line with a timestamp
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(data_dir) / "hook.log", "a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except OSError:
        # Logging never breaks the hook
        pass


def route(prompt: str, cwd: str) -> dict | None:
    """
    route
    Runs jev-route on the prompt as a single subtask
    @param prompt {str} - the agent prompt
    @param cwd {str} - the working dir for repo signals
    @return {dict | None} - the decision or None on any failure
    """
    # One subtask built from the prompt
    payload = {"subtasks": [{"id": "agent", "title": prompt[:80], "description": prompt}]}
    try:
        # Run the router with the payload on stdin
        proc = subprocess.run(
            [sys.executable, str(ROUTER)], input=json.dumps(payload), capture_output=True,
            text=True, timeout=ROUTE_TIMEOUT, cwd=cwd or None, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"route failed: {exc}")
        return None
    # Non zero means the router printed an error
    if proc.returncode != 0:
        log(f"route rc={proc.returncode}: {proc.stderr.strip()[:300]}")
        return None
    try:
        # The first decision is the only one
        return json.loads(proc.stdout)["decisions"][0]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        log(f"route bad output: {exc}")
        return None


def header(d: dict) -> str:
    """
    header
    Formats the decision as the one line routing header the worker parses
    @param d {dict} - the decision
    @return {str} - the header
    """
    return (
        f"JEFF ROUTE tier={d['tier']} ({d['tier_name']}) provider={d['provider']} model={d['model']} "
        f"effort={d['effort']} skill={d['skill']} sandbox={d['sandbox']} risk={d['risk']} "
        f"require_approval={str(d['require_approval']).lower()} confidence={d['confidence']} "
        f"fallback={','.join(d['fallback']) or 'none'} bin={ROOT / 'bin'}"
    )


def main() -> int:
    """
    main
    Reads the hook event, routes the prompt and prints the hook output
    @return {int} - always 0
    """
    # Opt in only, routing every spawn is too much as a default
    if os.environ.get("JEFF_HOOK", "").lower() not in {"on", "1", "true"}:
        return 0

    try:
        # The event from Claude Code on stdin
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    # Only the Agent tool matters
    if event.get("tool_name") != "Agent":
        return 0

    # The tool input and the fields we care about
    tool_input = dict(event.get("tool_input") or {})
    prompt = str(tool_input.get("prompt") or "")
    subagent_type = str(tool_input.get("subagent_type") or "")

    # Skip pinned, already routed or tiny prompts
    if "JEFF:PIN" in prompt or "JEFF ROUTE" in prompt or len(prompt) < MIN_PROMPT_CHARS:
        return 0
    # Skip specialized agents
    if subagent_type not in GENERIC_TYPES or subagent_type == WORKER_AGENT:
        return 0

    # Ask Jev
    decision = route(prompt, str(event.get("cwd") or ""))
    if decision is None:
        return 0

    # The registry for thresholds and tier lookups
    reg = json.loads((ROOT / "lib" / "registry.json").read_text())
    pol = reg["policy"]
    # Codex only when Jev is sure the task is self contained
    codex_sure = decision["signals"]["codex_suitable"] >= pol["confidence_act"]

    # Unsure how hard it is, bump to tier 1 rather than send a cheap model blind
    if "tier" in decision["fallback"] and decision["tier"] < 1:
        decision["tier"] = 1
        decision["tier_name"] = reg["tiers"][1]["name"]
        decision["model"] = reg["tiers"][1][decision["provider"]]["model"]
        decision["effort"] = reg["tiers"][1][decision["provider"]]["effort"]

    # The header and the input we may change
    head = header(decision)
    updated = dict(tool_input)
    note = ""

    # Codex work swaps the subagent and prepends the header
    if decision["provider"] == "codex" and codex_sure and not decision["require_approval"]:
        updated["subagent_type"] = WORKER_AGENT
        updated["prompt"] = f"{head}\n\n{prompt}"
        updated.pop("model", None)
        note = f"Jev rerouted this subagent to Codex ({decision['model']}, {decision['effort']})."
    # Claude work just sets the model
    elif decision["provider"] == "claude" and "tier" not in decision["fallback"]:
        updated["model"] = decision["model"]
        updated["prompt"] = f"{head}\n\n{prompt}"
        note = f"Jev set subagent model to {decision['model']} (tier {decision['tier_name']})."
    # Anything else is left alone
    else:
        note = "Jev routing was low-confidence or needs approval; call left unchanged."

    log(f"{note} :: {head}")

    # The hook output, updatedInput only when something changed
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"{head}. {note}",
        }
    }
    if updated != tool_input:
        output["hookSpecificOutput"]["updatedInput"] = updated
    json.dump(output, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - the hook must never block the tool call
        log(f"unexpected: {exc!r}")
        sys.exit(0)
