from django.test import TestCase

from workflow.rules import evaluate_rule


class RuleEvaluatorTests(TestCase):
    def test_field_present(self):
        passed, reason = evaluate_rule("field_present", {"field": "name"}, {"name": "A"})
        self.assertTrue(passed)
        self.assertEqual(reason, "name is required")

        passed, reason = evaluate_rule("field_present", {"field": "name"}, {"name": ""})
        self.assertFalse(passed)
        self.assertEqual(reason, "name is required")

    def test_field_equals(self):
        passed, reason = evaluate_rule(
            "field_equals", {"field": "priority", "value": "High"}, {"priority": "High"}
        )
        self.assertTrue(passed)
        self.assertEqual(reason, "")

        passed, reason = evaluate_rule(
            "field_equals", {"field": "priority", "value": "High"}, {"priority": "Low"}
        )
        self.assertFalse(passed)
        self.assertEqual(reason, "priority must equal High")

    def test_field_equals_with_requires(self):
        passed, reason = evaluate_rule(
            "field_equals",
            {"field": "priority", "value": "High", "requires": "manager_approval"},
            {"priority": "High", "manager_approval": False},
        )
        self.assertFalse(passed)
        self.assertEqual(reason, "manager_approval is required when priority is High")

        passed, reason = evaluate_rule(
            "field_equals",
            {"field": "priority", "value": "High", "requires": "manager_approval"},
            {"priority": "Low"},
        )
        self.assertTrue(passed)
        self.assertEqual(reason, "")

    def test_field_in(self):
        passed, reason = evaluate_rule(
            "field_in", {"field": "dept", "values": ["HR", "IT"]}, {"dept": "IT"}
        )
        self.assertTrue(passed)
        self.assertEqual(reason, "dept must be one of ['HR', 'IT']")

        passed, reason = evaluate_rule(
            "field_in", {"field": "dept", "values": ["HR", "IT"]}, {"dept": "Sales"}
        )
        self.assertFalse(passed)
        self.assertEqual(reason, "dept must be one of ['HR', 'IT']")

    def test_field_numeric_comparisons(self):
        passed, reason = evaluate_rule("field_gt", {"field": "score", "value": 5}, {"score": 7})
        self.assertTrue(passed)
        self.assertEqual(reason, "")

        passed, reason = evaluate_rule("field_gte", {"field": "score", "value": 5}, {"score": 5})
        self.assertTrue(passed)
        self.assertEqual(reason, "")

        passed, reason = evaluate_rule("field_lt", {"field": "score", "value": 5}, {"score": 5})
        self.assertFalse(passed)
        self.assertEqual(reason, "score must be < 5")

        passed, reason = evaluate_rule("field_lte", {"field": "score", "value": 5}, {"score": 5})
        self.assertTrue(passed)
        self.assertEqual(reason, "")

    def test_unsupported_condition(self):
        passed, reason = evaluate_rule("unknown", {}, {})
        self.assertFalse(passed)
        self.assertEqual(reason, "Unsupported condition type: unknown")
