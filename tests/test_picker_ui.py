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


if __name__ == '__main__':
    unittest.main()
