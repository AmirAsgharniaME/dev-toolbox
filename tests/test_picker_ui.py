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

    def test_multi_selection_toggles_checked_rows(self):
        selection = picker.MultiSelection(['a.md', 'b.md'])
        self.assertEqual(selection.values(), [])
        self.assertTrue(selection.display(0).startswith('□'))
        selection.toggle(1)
        self.assertEqual(selection.values(), ['b.md'])
        self.assertTrue(selection.display(1).startswith('✓'))
        selection.toggle(1)
        self.assertEqual(selection.values(), [])
        self.assertTrue(selection.display(1).startswith('□'))

    def test_selected_rows_survive_filtering(self):
        selection = picker.MultiSelection(['alpha.md', 'beta.md', 'gamma.md'])
        selection.toggle(0)
        self.assertEqual(selection.visible('beta'), [(1, 'beta.md')])
        self.assertEqual(selection.values(), ['alpha.md'])

    def test_group_commit_advances_and_keeps_groups_separate(self):
        history = picker.History()
        group1 = request('a.md', 'b.md')
        group2 = request('a.md', 'b.md')
        history.choose(0, group1, [0])
        self.assertEqual(history.prepare(1, group2)['value'], None)
        history.choose(1, group2, [1])
        self.assertEqual(history.steps[0]['value'], [0])
        self.assertEqual(history.steps[1]['value'], [1])

    def test_back_navigation_restores_group_selection(self):
        history = picker.History()
        history.choose(0, request('a.md', 'b.md'), [0])
        history.choose(1, request('a.md', 'b.md'), [1])
        restored = picker.MultiSelection(['a.md', 'b.md'],
                                         history.prepare(0, request('a.md', 'b.md'))['value'])
        self.assertEqual(restored.values(), ['a.md'])
        self.assertEqual(picker.menu_reply_value(request('a.md', 'b.md'), [0]), 'a.md')

    def test_final_group_values_remain_available_for_summary(self):
        groups = [('target', ['a.md', 'b.md']), ('source', ['c.md'])]
        summary = '; '.join(f'{name}: {", ".join(files)}' for name, files in groups)
        self.assertEqual(summary, 'target: a.md, b.md; source: c.md')

    def test_minimum_and_maximum_counts_are_validated(self):
        selection = picker.MultiSelection(['a', 'b'], minimum=1, maximum=1)
        self.assertEqual(selection.validation_error(), 'Select at least 1 file.')
        selection.toggle(0)
        self.assertIsNone(selection.validation_error())
        selection.toggle(1)
        self.assertEqual(selection.validation_error(), 'Select no more than 1 file.')

    def test_ordinary_single_choice_and_no_selection_menu_contracts(self):
        history = picker.History()
        history.choose(0, request('only'), 'only')
        self.assertEqual(history.steps[0]['value'], 'only')
        self.assertEqual(picker.MultiSelection(['a']).validation_error(),
                         'Select at least 1 file.')


if __name__ == '__main__':
    unittest.main()
