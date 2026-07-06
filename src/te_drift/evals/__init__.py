"""Eval harness for te-drift-detector.

Scaffold-corruption strategy generators plus a runner that feeds their output
through the detector to check that gradual, turn-by-turn-clean corruption is
caught. Dry-run by construction: no model calls, no network.
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
