"""Small independent checks of the HSCC action and vertex quantifiers."""

import unittest
from types import SimpleNamespace

import numpy as np

from core.approx_sim.hscc2027 import (
    Action, Model, fixed_relation_min_error, from_imdp, greatest_relation, interval_vertices,
    minimum_outside_mass, search_min_epsilon,
)


def point(p):
    return Action((1, 2), np.array([[p, 1 - p]]))


def interval(lo, hi):
    return Action((1, 2), np.array([[lo, 1 - lo], [hi, 1 - hi]]))


def model(actions_at_start):
    return Model(
        labels=("normal", "goal", "unsafe"),
        actions=(tuple(actions_at_start),
                 (Action((1,), np.array([[1.0]])),),
                 (Action((2,), np.array([[1.0]])),)),
        initial=0,
    )


class HSCC2027Tests(unittest.TestCase):
    def test_one_concrete_action_must_cover_every_abstract_vertex(self):
        abstract = model([interval(0.2, 0.8)])
        concrete = model([point(0.2), point(0.8)])
        low = greatest_relation(abstract, concrete, 0.3, "cooperative")
        high = greatest_relation(abstract, concrete, 0.6, "cooperative")
        self.assertNotIn((0, 0), low["R"])
        self.assertIn((0, 0), high["R"])
        self.assertEqual(high["R"], {(0, 0), (1, 1), (2, 2)})

    def test_competitive_fixes_concrete_vertex_and_allows_abstract_response(self):
        abstract = model([interval(0.2, 0.8)])
        concrete = model([point(0.2), point(0.8)])
        result = greatest_relation(abstract, concrete, 0, "competitive")
        self.assertTrue(result["initial_pair_present"])

    def test_fine_concrete_uncertainty_is_checked_in_competitive_case(self):
        abstract = model([point(0.2)])
        concrete = model([interval(0.2, 0.8)])
        result = greatest_relation(abstract, concrete, 0.3, "competitive")
        self.assertFalse(result["initial_pair_present"])

    def test_adapter_includes_absorbing_probability_mass(self):
        partition = SimpleNamespace(
            size=1,
            goal={"bools": [False]},
            critical={"bools": [False]},
        )
        imdp = SimpleNamespace(
            absorbing_state=1,
            s_init=0,
            P_full={0: np.array([[[0.7, 0.7]]])},
            S_id={0: np.array([[0]])},
            P_absorbing={0: np.array([[0.3, 0.3]])},
        )
        adapted = from_imdp(imdp, partition)
        self.assertEqual(adapted.actions[0][0].successors, (0, 1))
        self.assertNotIn("vertices", adapted.actions[0][0].__dict__)
        np.testing.assert_allclose(adapted.actions[0][0].vertices, [[0.7, 0.3]])
        self.assertTrue(greatest_relation(adapted, adapted, 0, "cooperative")
                        ["initial_pair_present"])

    def test_incomplete_vertex_enumeration_is_rejected(self):
        with self.assertRaises(ValueError):
            interval_vertices(np.zeros(17), np.ones(17))

    def test_bisection_brackets_hand_computed_cooperative_error(self):
        abstract = model([interval(0.2, 0.8)])
        concrete = model([point(0.2), point(0.8)])
        result = search_min_epsilon(abstract, concrete, "cooperative",
                                    tolerance=1e-3)
        self.assertLess(result["epsilon_lower"], 0.6)
        self.assertGreaterEqual(result["epsilon_upper"], 0.6 - 1e-9)
        self.assertLessEqual(result["epsilon_upper"] - result["epsilon_lower"], 1e-3)
        self.assertIn((0, 0), result["R"])

    def test_refinement_uses_multiple_rounds_after_successor_pair_removal(self):
        labels = ("start", "middle", "goal", "unsafe")
        def deterministic(target):
            return Action((target,), np.array([[1.0]]))
        abstract = Model(labels, tuple((deterministic(t),)
                                       for t in (1, 2, 2, 3)), 0)
        concrete = Model(labels, tuple((deterministic(t),)
                                       for t in (1, 3, 2, 3)), 0)
        for semantics in ("cooperative", "competitive"):
            with self.subTest(semantics=semantics):
                result = greatest_relation(abstract, concrete, 0, semantics)
                self.assertEqual(result["R"], {(2, 2), (3, 3)})
                self.assertGreaterEqual(result["iterations"], 3)

    def test_initial_relation_contains_all_label_matching_pairs(self):
        labels = ("normal", "normal")
        actions = ((Action((0,), np.array([[1.0]])),),
                   (Action((1,), np.array([[1.0]])),))
        one = Model(labels, actions, 0)
        result = greatest_relation(one, one, 0, "cooperative")
        self.assertEqual(result["R"], {(0, 0), (0, 1), (1, 0), (1, 1)})

    def test_coupling_lp_matches_two_point_total_variation_formula(self):
        fixed = Action((0, 1), np.array([[0.2, 0.8]]))
        variable = Action((0, 1), np.array([[0.5, 0.5], [0.8, 0.2]]))
        relation = {(0, 0), (1, 1)}
        self.assertAlmostEqual(minimum_outside_mass(fixed, variable, relation, 1)[0],
                               0.3)
        errors = minimum_outside_mass(fixed, variable, relation, 2)
        np.testing.assert_allclose(errors, [0.3, 0.6], atol=1e-8)

    def test_diagnostic_identifies_initial_pair_removal(self):
        abstract = model([interval(0.2, 0.8)])
        concrete = model([point(0.2), point(0.8)])
        result = greatest_relation(abstract, concrete, 0.3, "cooperative",
                                   diagnose=True)
        self.assertEqual(result["initial_failure"]["M1_action"], 0)
        np.testing.assert_allclose(
            [error for _, error in result["initial_failure"]["M2_action_worst_errors"]],
            [0.6, 0.6], atol=1e-8)

    def test_algorithm2_fixed_relation_error_matches_action_quantifiers(self):
        abstract = model([interval(0.2, 0.8)])
        concrete = model([point(0.2), point(0.8)])
        relation = {(0, 0), (1, 1), (2, 2)}
        cooperative = fixed_relation_min_error(
            abstract, concrete, relation, "cooperative")
        competitive = fixed_relation_min_error(
            abstract, concrete, relation, "competitive")
        self.assertAlmostEqual(cooperative["epsilon_star"], 0.6)
        self.assertEqual(cooperative["worst_pair"], (0, 0))
        self.assertAlmostEqual(competitive["epsilon_star"], 0)
        self.assertEqual(len(cooperative["pair_errors"]), len(relation))
        for semantics, error in (("cooperative", 0.6), ("competitive", 0)):
            self.assertTrue(greatest_relation(abstract, concrete, error, semantics)
                            ["initial_pair_present"])

    def test_algorithm2_rejects_invalid_fixed_relations(self):
        one = model([point(0.2)])
        with self.assertRaisesRegex(ValueError, "initial pair"):
            fixed_relation_min_error(one, one, {(1, 1)}, "cooperative")
        with self.assertRaisesRegex(ValueError, "label mismatch"):
            fixed_relation_min_error(one, one, {(0, 0), (1, 2)}, "cooperative")


if __name__ == "__main__":
    unittest.main()
