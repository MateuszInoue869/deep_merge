"""Tests for deep_merge.core.

Every test here corresponds to an explicit behaviour in the implementation.
We do not test anything the code does not claim to do.
"""

import unittest

from deep_merge import MergeConfig, deep_merge


class TestDeepMerge(unittest.TestCase):
    def test_overlay_adds_new_key(self):
        result = deep_merge({"a": 1}, {"b": 2})
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_overlay_overrides_scalar(self):
        result = deep_merge({"a": 1}, {"a": 2})
        self.assertEqual(result, {"a": 2})

    def test_nested_mappings_recurse(self):
        result = deep_merge(
            {"a": {"b": 1, "c": 2}},
            {"a": {"c": 3, "d": 4}},
        )
        self.assertEqual(result, {"a": {"b": 1, "c": 3, "d": 4}})

    def test_lists_replace_by_default(self):
        result = deep_merge({"a": [1, 2]}, {"a": [3, 4]})
        self.assertEqual(result, {"a": [3, 4]})

    def test_lists_concatenate_when_configured(self):
        result = deep_merge(
            {"a": [1, 2]},
            {"a": [3, 4]},
            MergeConfig(list_strategy="concatenate"),
        )
        self.assertEqual(result, {"a": [1, 2, 3, 4]})

    def test_none_overlay_does_not_erase_base(self):
        result = deep_merge({"a": 1}, {"a": None})
        self.assertEqual(result, {"a": 1})

    def test_none_base_uses_overlay(self):
        result = deep_merge({"a": None}, {"a": 1})
        self.assertEqual(result, {"a": 1})

    def test_both_none_stays_none(self):
        result = deep_merge({"a": None}, {"a": None})
        self.assertIsNone(result["a"])

    def test_none_overlay_preserves_nested_mapping_in_base(self):
        result = deep_merge({"a": {"b": 1}}, {"a": None})
        self.assertEqual(result, {"a": {"b": 1}})

    def test_type_mismatch_right_wins(self):
        result = deep_merge({"a": [1, 2]}, {"a": "text"})
        self.assertEqual(result, {"a": "text"})

    def test_type_mismatch_scalar_to_list(self):
        result = deep_merge({"a": 1}, {"a": [1, 2]})
        self.assertEqual(result, {"a": [1, 2]})

    def test_base_not_mutated(self):
        base = {"a": {"b": 1}}
        overlay = {"a": {"c": 2}}
        result = deep_merge(base, overlay)
        self.assertEqual(result, {"a": {"b": 1, "c": 2}})
        # base should be untouched
        self.assertEqual(base, {"a": {"b": 1}})

    def test_overlay_not_mutated(self):
        base = {"a": 1}
        overlay = {"b": {"c": 2}}
        result = deep_merge(base, overlay)
        self.assertEqual(result, {"a": 1, "b": {"c": 2}})
        self.assertEqual(overlay, {"b": {"c": 2}})
        # Mutating result should not bleed into overlay
        result["b"]["c"] = 99
        self.assertEqual(overlay, {"b": {"c": 2}})

    def test_result_does_not_alias_overlay_list(self):
        overlay = {"a": [1, 2]}
        result = deep_merge({}, overlay)
        result["a"].append(3)
        self.assertEqual(overlay["a"], [1, 2])

    def test_concatenate_does_not_alias_input_lists(self):
        base = {"a": [1, 2]}
        overlay = {"a": [3, 4]}
        result = deep_merge(
            base, overlay, MergeConfig(list_strategy="concatenate")
        )
        result["a"].append(5)
        self.assertEqual(base["a"], [1, 2])
        self.assertEqual(overlay["a"], [3, 4])

    def test_invalid_list_strategy_raises(self):
        with self.assertRaises(ValueError):
            deep_merge({}, {}, MergeConfig(list_strategy="bogus"))

    def test_empty_overlay_returns_copy_of_base(self):
        base = {"a": 1}
        result = deep_merge(base, {})
        self.assertEqual(result, base)
        self.assertIsNot(result, base)

    def test_empty_base_returns_overlay_data(self):
        overlay = {"a": {"b": 1}}
        result = deep_merge({}, overlay)
        self.assertEqual(result, overlay)

    def test_deeply_nested_merge(self):
        base = {"a": {"b": {"c": 1, "d": 2}}}
        overlay = {"a": {"b": {"d": 3, "e": 4}}}
        result = deep_merge(base, overlay)
        self.assertEqual(result, {"a": {"b": {"c": 1, "d": 3, "e": 4}}})

    def test_concatenate_preserves_order(self):
        result = deep_merge(
            {"a": ["x", "y"]},
            {"a": ["z"]},
            MergeConfig(list_strategy="concatenate"),
        )
        self.assertEqual(result["a"], ["x", "y", "z"])


if __name__ == "__main__":
    unittest.main()
