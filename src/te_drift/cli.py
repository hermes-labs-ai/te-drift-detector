"""Unified CLI for te-drift-detector.

Subcommands:
  detect    Analyze a canned conversation (poisoning / persona / constraint / normal).
  session   Analyze a session JSONL file.
  eval      Run the scaffold-corruption eval harness through the detector.

Examples:
  te-drift detect --attack-type poisoning
  te-drift session --session-jsonl path/to/session.jsonl --mode sliding-window
  te-drift eval --strategy all --turns 5
"""

import sys

from . import __version__


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] in ("-V", "--version"):
        print(f"te-drift-detector {__version__}")
        return 0

    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("Run 'te-drift <subcommand> --help' for subcommand options.")
        return 0

    sub, rest = argv[0], argv[1:]

    if sub == "detect":
        from .detector import main as detect_main

        return detect_main(rest)
    if sub == "session":
        from .jsonl_adapter import main as session_main

        return session_main(rest)
    if sub == "eval":
        from .evals.harness import main as eval_main

        return eval_main(rest)

    print(f"te-drift: unknown subcommand '{sub}'", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
