import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'prompt_picker' / 'picker_ui.py'
spec = importlib.util.spec_from_file_location('picker_ui', path)
picker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(picker)


def request(*items):
    return {'arguments': ['-dmenu'], 'items': list(items)}


class PickerHistoryTests(unittest.TestCase):
    def test_changing_inventory_discards_dependent_stages(self):
        history = picker.History()
        inventories = request('alpha', 'beta')
        history.choose(0, inventories, 'alpha')
        history.choose(1, request('alpha.md'), 'alpha.md')
        history.prepare(2, request('action'))
        history.choose(0, inventories, 'beta')
        self.assertEqual(len(history.steps), 1)
        self.assertEqual(history.steps[0]['value'], 'beta')
        self.assertIsNone(history.prepare(1, request('beta.md'))['value'])

    def test_unchanged_choice_keeps_forward_history(self):
        history = picker.History()
        inventories = request('alpha', 'beta')
        history.choose(0, inventories, 'beta')
        history.choose(1, request('beta.md'), 'beta.md')
        history.prepare(2, request('action'))
        history.choose(0, inventories, 'beta')
        self.assertEqual(len(history.steps), 3)
        self.assertIsNone(history.steps[2]['value'])

    def test_changed_menu_invalidates_its_descendants(self):
        history = picker.History()
        history.choose(0, request('first'), 'first')
        history.choose(1, request('old'), 'old')
        history.prepare(2, request('action'))
        history.prepare(1, request('new'))
        self.assertEqual(len(history.steps), 2)
        self.assertIsNone(history.steps[1]['value'])

    def test_fuzzy_filter_matches_subsequences(self):
        self.assertTrue(picker.matches_filter('Create New Branch', 'cnb', fuzzy=True))
        self.assertFalse(picker.matches_filter('Create New Branch', 'cnb'))

    def test_filter_is_case_insensitive_and_keeps_order(self):
        items = ['Beta FILE', 'alpha', 'beta other']
        self.assertEqual([item for item in items if picker.matches_filter(item, 'BeTa')],
                         ['Beta FILE', 'beta other'])

    def test_navigation_wraps_up_from_first_item(self):
        self.assertEqual(picker.wrapped_index(0, 3, -1), 2)

    def test_navigation_wraps_down_from_last_item(self):
        self.assertEqual(picker.wrapped_index(2, 3, 1), 0)

    def test_navigation_wraps_only_visible_filtered_items(self):
        visible = [item for item in ['alpha', 'beta', 'echo', 'delta']
                   if picker.matches_filter(item, 'a')]
        self.assertEqual(visible, ['alpha', 'beta', 'delta'])
        self.assertEqual(picker.wrapped_index(0, len(visible), -1), 2)
        self.assertEqual(picker.wrapped_index(len(visible) - 1, len(visible), 1), 0)

        filtered = [item for item in ['alpha', 'beta', 'gamma', 'delta']
                    if picker.matches_filter(item, 'mm')]
        self.assertEqual(filtered, ['gamma'])
        self.assertEqual(picker.wrapped_index(0, len(filtered), -1), 0)

    def test_empty_navigation_is_safe(self):
        self.assertIsNone(picker.wrapped_index(0, 0, -1))
        self.assertIsNone(picker.wrapped_index(0, 0, 1))

    def test_navigation_is_shared_across_menu_stages(self):
        for count in (2, 4):
            self.assertEqual(picker.wrapped_index(0, count, -1), count - 1)
            self.assertEqual(picker.wrapped_index(count - 1, count, 1), 0)


if __name__ == '__main__':
    unittest.main()
