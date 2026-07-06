#!/usr/bin/env python3
"""
JSONL adapter: run te-drift-detector on Claude Code (or similar) session JSONLs.

Extracts user + assistant turns in chronological order, computes a
StateFingerprint per turn, and runs DriftAnalyzer with a turn-1 baseline.

Usage:
  python -m te_drift.jsonl_adapter --session-jsonl PATH [--output PATH] [--baseline-turns N]
  python -m te_drift.jsonl_adapter --session-jsonl PATH --mode sliding-window --window-size 10

Modes:
  cumulative     (default) Embed all turns [0..N] per step — quadratic cost,
                 highest fidelity. Not viable at SessionEnd on long sessions.
  sliding-window Embed only the last K turns per step — constant cost O(K)
                 per step, suitable for a SessionEnd hook on long sessions.
"""

import argparse
import json
import sys
import time

from .drift_analyzer import DriftAnalyzer
from .state_fingerprint import StateFingerprint


def _extract_text(message: dict) -> str:
    """Extract plain text from a session message field."""
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
        return " ".join(parts).strip()
    return ""


def load_turns(jsonl_path: str) -> list[tuple[str, str, str]]:
    """Parse JSONL into (role, text, timestamp) for user/assistant turns only.

    Turns are returned in file order (chronological). Turns with empty text are
    skipped. Malformed JSON lines are skipped rather than raising.
    """
    turns = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            rtype = record.get("type")
            if rtype not in ("user", "assistant"):
                continue
            msg = record.get("message", {})
            if not isinstance(msg, dict):
                continue
            text = _extract_text(msg)
            if not text:
                continue
            role = msg.get("role", rtype)
            ts = record.get("timestamp", "")
            turns.append((role, text, ts))
    return turns


def run_drift_analysis(
    turns: list[tuple[str, str, str]],
    baseline_n: int = 1,
    mode: str = "cumulative",
    window_size: int = 10,
) -> dict:
    """Run DriftAnalyzer over turns.

    Baseline fingerprint = concatenation of the first ``baseline_n`` turn texts.
    Returns a summary_report dict augmented with per-turn timestamps and roles.

    Args:
        turns:       List of (role, text, timestamp) tuples.
        baseline_n:  Number of turns to use as baseline context.
        mode:        "cumulative" (default) or "sliding-window".
        window_size: In sliding-window mode, number of turns per fingerprint window.
    """
    if not turns:
        return {"error": "no turns found"}

    baseline_text = "\n".join(
        f"[{role.upper()}] {text}" for role, text, _ in turns[:baseline_n]
    )
    baseline_fp = StateFingerprint(baseline_text, role=turns[0][0])
    analyzer = DriftAnalyzer(baseline_fp)

    timestamps = []
    for i, (role, _text, ts) in enumerate(turns[baseline_n:], start=1):
        abs_idx = baseline_n + i  # exclusive upper bound into turns

        if mode == "sliding-window":
            window_start = max(0, abs_idx - window_size)
            context_lines = [
                f"[{r.upper()}] {t}" for r, t, _ in turns[window_start:abs_idx]
            ]
        else:
            context_lines = [f"[{r.upper()}] {t}" for r, t, _ in turns[:abs_idx]]

        context = "\n".join(context_lines)
        fp = StateFingerprint(context, role=role)
        analyzer.analyze_turn(fp)
        timestamps.append(ts)

    report = analyzer.summary_report()
    report["mode"] = mode
    if mode == "sliding-window":
        report["window_size"] = window_size

    for idx, reading in enumerate(report.get("readings", [])):
        reading["timestamp"] = timestamps[idx] if idx < len(timestamps) else ""
        reading["role"] = turns[baseline_n + idx][0] if (baseline_n + idx) < len(turns) else ""

    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="TE Drift Detector - session JSONL adapter"
    )
    parser.add_argument(
        "--session-jsonl", required=True, help="Path to a session .jsonl file"
    )
    parser.add_argument("--output", help="Write JSON results to this file (default: stdout)")
    parser.add_argument(
        "--baseline-turns",
        type=int,
        default=1,
        help="Number of turns to use as baseline (default: 1)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=0,
        help="Cap analysis at N turns (0 = all, useful for large sessions)",
    )
    parser.add_argument(
        "--mode",
        choices=["cumulative", "sliding-window"],
        default="cumulative",
        help=(
            "Embedding strategy. 'cumulative' (default): embed all turns [0..N] per step "
            "(highest fidelity, quadratic cost). 'sliding-window': embed only the last "
            "--window-size turns per step (constant cost, suitable for SessionEnd hooks)."
        ),
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=10,
        help="Turns per sliding window (only used with --mode sliding-window, default: 10)",
    )
    args = parser.parse_args(argv)

    t0 = time.time()
    print(f"Loading turns from {args.session_jsonl} ...", file=sys.stderr)
    turns = load_turns(args.session_jsonl)
    print(f"Loaded {len(turns)} user/assistant turns.", file=sys.stderr)

    if args.max_turns and args.max_turns < len(turns):
        turns = turns[: args.max_turns]
        print(f"Capped at {args.max_turns} turns.", file=sys.stderr)

    mode_label = args.mode
    if args.mode == "sliding-window":
        mode_label = f"sliding-window(k={args.window_size})"
    print(
        f"Running drift analysis (baseline={args.baseline_turns} turn(s), mode={mode_label}) ...",
        file=sys.stderr,
    )
    report = run_drift_analysis(
        turns,
        baseline_n=args.baseline_turns,
        mode=args.mode,
        window_size=args.window_size,
    )
    elapsed = time.time() - t0
    report["wall_time_s"] = round(elapsed, 2)
    report["session_jsonl"] = args.session_jsonl
    report["total_turns_loaded"] = len(turns)

    output = json.dumps(report, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results saved to {args.output}", file=sys.stderr)
    else:
        print(output)

    threat = report.get("threat_level", "?")
    anomalies = report.get("anomalies_detected", 0)
    analyzed = report.get("total_turns", 0)
    print(
        f"\nSummary: {analyzed} turns analyzed | {anomalies} anomalies | "
        f"threat={threat} | {elapsed:.1f}s",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
