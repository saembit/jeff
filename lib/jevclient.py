"""
jevclient
Small client for the TypeSafe System One api, stdlib only so there is nothing to install
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Path to the registry that holds tiers, thresholds and skill text
REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"
# Dotenv file the key can be read from when the env var isn't set
ENV_FILE = Path.home() / ".config" / "typesafe" / "env"
# Entry name used when falling back to pass
PASS_ENTRY = "typesafe/api-key"
# Status codes that are worth retrying
RETRYABLE = {429, 529, 502, 503}
# How many times to try a request before giving up
MAX_ATTEMPTS = 4


class JevError(RuntimeError):
    """
    JevError
    Raised for config, network or api problems so callers can catch one thing
    """


def load_registry() -> dict[str, Any]:
    """
    load_registry
    Reads registry.json and returns it as a dict
    @return {dict} - the parsed registry
    """
    try:
        # Read and parse the registry file
        return json.loads(REGISTRY_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        # Wrap the error so the caller gets one error type
        raise JevError(f"cannot read registry {REGISTRY_PATH}: {exc}") from exc


def _key_from_env_file() -> str | None:
    """
    _key_from_env_file
    Pulls the api key out of the dotenv file if it exists
    @return {str | None} - the key or None
    """
    try:
        # Read the whole env file
        text = ENV_FILE.read_text()
    except OSError:
        # No file, nothing to return
        return None
    # Look for the export line and grab the value
    match = re.search(r"TYPESAFE_API_KEY=['\"]?([^'\"\s]+)", text)
    return match.group(1) if match else None


def _key_from_pass() -> str | None:
    """
    _key_from_pass
    Asks pass for the key as a last resort
    @return {str | None} - the key or None
    """
    try:
        # Run pass show and capture the output
        out = subprocess.run(
            ["pass", "show", PASS_ENTRY],
            capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        # pass isn't installed or hung
        return None
    # Non zero means the entry doesn't exist
    if out.returncode != 0:
        return None
    # The key is the first line of output
    first = out.stdout.strip().splitlines()
    return first[0].strip() if first else None


def resolve_api_key() -> str:
    """
    resolve_api_key
    Finds the api key from the env var, the dotenv file or pass in that order
    @return {str} - the api key
    """
    # Try each source in order
    key = os.environ.get("TYPESAFE_API_KEY") or _key_from_env_file() or _key_from_pass()
    # Give up with a message that says where to put it
    if not key:
        raise JevError(
            "no TypeSafe API key: set TYPESAFE_API_KEY, write ~/.config/typesafe/env, "
            f"or `pass insert {PASS_ENTRY}`"
        )
    return key


def ask(state: Any, questions: dict[str, dict[str, Any]], *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    ask
    Sends one System One request and returns the parsed body
    @param state {Any} - the state the questions are asked about
    @param questions {dict} - the typed questions keyed by id
    @param registry = None {dict | None} - a loaded registry to reuse
    @return {dict} - the api response
    """
    # Load the registry if the caller didn't pass one
    reg = registry or load_registry()
    # The jev section has the endpoint, model and timeout
    cfg = reg["jev"]
    # Build the request body
    body = json.dumps({"state": state, "model": cfg["model"], "questions": questions}).encode()
    # Build the request with the bearer token
    req = urllib.request.Request(
        cfg["endpoint"],
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {resolve_api_key()}",
            "Content-Type": "application/json",
        },
    )
    # Starting delay for backoff in seconds
    delay = 1.0

    # Try the request up to MAX_ATTEMPTS times
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # Send the request and parse the json body
            with urllib.request.urlopen(req, timeout=cfg["timeout_seconds"]) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            # Keep a bit of the error body for the message
            detail = exc.read().decode(errors="replace")[:500]
            # Retry rate limits and overloads with backoff
            if exc.code in RETRYABLE and attempt < MAX_ATTEMPTS:
                _log(f"jev http {exc.code}, retry {attempt}/{MAX_ATTEMPTS} in {delay:.0f}s")
                time.sleep(delay)
                delay *= 2
                continue
            # Anything else is a real error
            raise JevError(f"jev http {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            # Network problems get the same backoff
            if attempt < MAX_ATTEMPTS:
                _log(f"jev network error {exc.reason}, retry {attempt}/{MAX_ATTEMPTS}")
                time.sleep(delay)
                delay *= 2
                continue
            raise JevError(f"jev unreachable: {exc.reason}") from exc

    # Only reached if every attempt was retried
    raise JevError("jev: exhausted retries")


def argmax_level(answer: dict[str, Any]) -> tuple[int, float]:
    """
    argmax_level
    Picks the most likely level out of a Score answer
    @param answer {dict} - a score answer from the api
    @return {tuple} - the level index and its probability
    """
    # The probabilities map level index to probability
    probs = answer.get("probabilities") or {}
    # No probabilities means level 0 with no confidence
    if not probs:
        return 0, 0.0
    # Take the level with the highest probability
    level, prob = max(probs.items(), key=lambda kv: kv[1])
    return int(level), float(prob)


def _log(msg: str) -> None:
    """
    _log
    Prints a message to stderr so stdout stays clean json
    @param msg {str} - the message
    @return None
    """
    print(f"[jev] {msg}", file=sys.stderr)
