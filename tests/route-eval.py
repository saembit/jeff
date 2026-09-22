#!/usr/bin/env python3
"""
route-eval
Runs bin/jev-route over tests/tasks.json and scores it against the expected values

Usage: tests/route-eval.py [--tasks FILE] [--save]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# The plugin root and the router
ROOT = Path(__file__).resolve().parent.parent
ROUTER = ROOT / "bin" / "jev-route"
# The columns that get scored
KEYS = ("tier", "tier_pm1", "provider", "writes", "risk")


def main() -> int:
    """
    main
    Routes the tasks file, prints a row per task and the accuracy per column
    @return {int} - exit code
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default=str(ROOT / "tests" / "tasks.json"))
    parser.add_argument("--save", action="store_true", help="write raw output to tests/out/")
    args = parser.parse_args()

    # The tasks file with the expectations in it
    payload = json.loads(Path(args.tasks).read_text())
    # Run the router on it
    proc = subprocess.run(
        [sys.executable, str(ROUTER)], input=json.dumps(payload), capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    result = json.loads(proc.stdout)

    # Save the raw output when asked
    if args.save:
        out_dir = ROOT / "tests" / "out"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "route-eval.json").write_text(json.dumps(result, indent=2))

    # Expectations by id and the hit and total counters
    expect = {s["id"]: s for s in payload["subtasks"]}
    hits = dict.fromkeys(KEYS, 0)
    counts = dict.fromkeys(KEYS, 0)

    # Header row
    print(f"{'id':5} {'tier':>4} {'exp':>3} {'prov':6} {'exp':6} {'skill':15} {'sbx':15} {'par':8} {'risk':4} {'conf':5} fallback")

    # One row per decision
    for d in result["decisions"]:
        e = expect[d["id"]]
        # Marks are upper case for a hit and lower case for a miss
        marks = []

        # Tier exact and within one
        et = e.get("expect_tier")
        if et is not None:
            counts["tier"] += 1
            counts["tier_pm1"] += 1
            hits["tier"] += d["tier"] == et
            hits["tier_pm1"] += abs(d["tier"] - et) <= 1
            marks.append("T" if d["tier"] == et else "t")

        # Provider
        ep = e.get("expect_provider")
        if ep is not None:
            counts["provider"] += 1
            hits["provider"] += d["provider"] == ep
            marks.append("P" if d["provider"] == ep else "p")

        # Writes, judged from the sandbox
        ew = e.get("expect_writes")
        if ew is not None:
            counts["writes"] += 1
            got = d["sandbox"] == "workspace-write"
            hits["writes"] += got == ew
            marks.append("W" if got == ew else "w")

        # Risk
        er = e.get("expect_risk")
        if er is not None:
            counts["risk"] += 1
            hits["risk"] += d["risk"] == er
            marks.append("R" if d["risk"] == er else "r")

        print(
            f"{d['id']:5} {d['tier']:>4} {et if et is not None else '-':>3} {d['provider']:6} {ep or '-':6} "
            f"{d['skill']:15} {d['sandbox']:15} {d['parallel_group']:8} {d['risk']:4} {d['confidence']:5} "
            f"{','.join(d['fallback']) or '-'}  {''.join(marks)}"
        )

    # Accuracy per column
    print()
    for key in KEYS:
        if counts[key]:
            print(f"{key:9} {hits[key]}/{counts[key]}  {100 * hits[key] / counts[key]:.0f}%")

    # Token usage across batches
    usage = [b.get("usage") for b in result["raw"].values() if b.get("usage")]
    if usage:
        print(f"jev input tokens: {sum(u['input_tokens'] for u in usage)} across {len(usage)} batch(es)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
