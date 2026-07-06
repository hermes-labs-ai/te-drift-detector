#!/usr/bin/env python3
"""
Tests for the eval harness: scaffold-corruption strategy generation and the
detector-integration runner. Hermetic (no model, no network).
"""

import unittest

from te_drift.evals.harness import build_conversation, run_all, run_eval
from te_drift.evals.strategies import (
    STRATEGIES,
    BiasDriftStrategy,
    FactInjectionStrategy,
    TermRedefinitionStrategy,
    generate_attack_sequence,
)


class TestFactInjectionStrategy(unittest.TestCase):
    def test_generate_turn(self):
        strategy = FactInjectionStrategy()
        for turn_num in range(3):
            turn = strategy.generate_turn(turn_num)
            self.assertEqual(turn.turn_number, turn_num)
            self.assertTrue(turn.user_message)
            self.assertEqual(turn.technique, "fact_injection")
            self.assertIn("[SCAFFOLD CONTEXT", turn.injected_scaffold)
            self.assertIn("Previously established", turn.injected_scaffold)
            if turn_num > 0:
                self.assertGreater(turn.expected_drift, 0.0)
            self.assertGreaterEqual(turn.detection_risk, 0.0)
            self.assertLessEqual(turn.detection_risk, 1.0)

    def test_false_context_pool_cycles(self):
        strategy = FactInjectionStrategy()
        self.assertTrue(strategy.generate_turn(0).injected_scaffold)
        self.assertTrue(strategy.generate_turn(5).injected_scaffold)


class TestTermRedefinitionStrategy(unittest.TestCase):
    def test_generate_turn(self):
        strategy = TermRedefinitionStrategy()
        for turn_num in range(3):
            turn = strategy.generate_turn(turn_num)
            self.assertEqual(turn.turn_number, turn_num)
            self.assertEqual(turn.technique, "term_redefinition")
            self.assertIn("[TERM REDEFINITION", turn.injected_scaffold)

    def test_term_corruption_present(self):
        self.assertIn("means:", TermRedefinitionStrategy().generate_turn(0).injected_scaffold)


class TestBiasDriftStrategy(unittest.TestCase):
    def test_credulous_drift(self):
        turn = BiasDriftStrategy(direction="credulous").generate_turn(0)
        self.assertEqual(turn.technique, "bias_drift")
        self.assertIn("CREDULOUS", turn.injected_scaffold)

    def test_skeptical_drift(self):
        turn = BiasDriftStrategy(direction="skeptical").generate_turn(0)
        self.assertEqual(turn.technique, "bias_drift")
        self.assertIn("SKEPTICAL", turn.injected_scaffold)

    def test_constraint_cascade(self):
        strategy = BiasDriftStrategy(direction="credulous")
        self.assertNotEqual(
            strategy.generate_turn(0).injected_scaffold,
            strategy.generate_turn(1).injected_scaffold,
        )


class TestAttackSequenceGeneration(unittest.TestCase):
    def test_fact_injection_sequence(self):
        turns = generate_attack_sequence(strategy="fact_injection", num_turns=3)
        self.assertEqual(len(turns), 3)
        for i, turn in enumerate(turns):
            self.assertEqual(turn.turn_number, i)
            self.assertEqual(turn.technique, "fact_injection")

    def test_term_redefinition_sequence(self):
        turns = generate_attack_sequence(strategy="term_redefinition", num_turns=4)
        self.assertEqual(len(turns), 4)
        self.assertTrue(all(t.technique == "term_redefinition" for t in turns))

    def test_bias_drift_sequence(self):
        turns = generate_attack_sequence(strategy="bias_drift", num_turns=3)
        self.assertEqual(len(turns), 3)
        self.assertTrue(all(t.technique == "bias_drift" for t in turns))

    def test_unknown_strategy_raises(self):
        with self.assertRaises(ValueError):
            generate_attack_sequence(strategy="unknown_strategy", num_turns=3)

    def test_expected_drift_monotonic(self):
        turns = generate_attack_sequence(strategy="fact_injection", num_turns=4)
        drifts = [t.expected_drift for t in turns]
        self.assertEqual(drifts, sorted(drifts))


class TestHarnessDetection(unittest.TestCase):
    def test_build_conversation_shape(self):
        convo = build_conversation("fact_injection", 3)
        # 3 baseline turns + 2 per corruption turn
        self.assertEqual(len(convo), 3 + 2 * 3)
        self.assertTrue(all(isinstance(t, tuple) and len(t) == 2 for t in convo))

    def test_run_eval_structure(self):
        result = run_eval("fact_injection", 5)
        for field in ("strategy", "detected", "threat_level", "report", "anomalies_detected"):
            self.assertIn(field, result)
        self.assertEqual(result["strategy"], "fact_injection")

    def test_detector_catches_corruption(self):
        # The whole point of the harness: accumulating scaffold corruption should
        # register as drift the detector flags, across every strategy.
        for strategy in STRATEGIES:
            result = run_eval(strategy, 6)
            self.assertGreater(
                result["max_absolute_drift"], 0.0,
                f"{strategy}: expected measurable drift",
            )
            self.assertTrue(
                result["detected"],
                f"{strategy}: expected the detector to flag corruption",
            )

    def test_run_all_covers_every_strategy(self):
        results = run_all(5)
        self.assertEqual({r["strategy"] for r in results}, set(STRATEGIES))


if __name__ == "__main__":
    unittest.main()
