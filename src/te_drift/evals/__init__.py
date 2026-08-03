"""Synthetic demo/self-check fixtures for te-drift-detector.

The generators create deterministic text without a live model. Running the
fixtures through the package is a wiring self-check, not efficacy evidence. The
default lexical path stays in-process; TE_DRIFT_EMBED=1 can make an optional
configured network call, and endpoint failure silently falls back to lexical
set overlap.
"""

from .harness import build_conversation, run_all, run_eval
from .strategies import (
    STRATEGIES,
    BiasDriftStrategy,
    FactInjectionStrategy,
    ScaffoldTurn,
    TermRedefinitionStrategy,
    generate_attack_sequence,
)

__all__ = [
    "STRATEGIES",
    "ScaffoldTurn",
    "FactInjectionStrategy",
    "TermRedefinitionStrategy",
    "BiasDriftStrategy",
    "generate_attack_sequence",
    "build_conversation",
    "run_eval",
    "run_all",
]
