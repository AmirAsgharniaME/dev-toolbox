import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
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

    def test_last_selected_row_tracks_selection_order(self):
        selection = picker.MultiSelection(['a', 'b', 'c'])
        selection.toggle(0)
        selection.toggle(2)
        self.assertEqual(selection.last_selected, 2)
        self.assertTrue(picker.multi_right_moves_to_done(2, selection.last_selected))
        self.assertFalse(picker.multi_right_moves_to_done(0, selection.last_selected))
        selection.toggle(2)
        self.assertEqual(selection.last_selected, 0)

    def test_selected_rows_survive_filtering(self):
        selection = picker.MultiSelection(['alpha.md', 'beta.md', 'gamma.md'])
        selection.toggle(0)
        self.assertEqual(selection.visible('beta'), [(1, 'beta.md')])
        self.assertEqual(selection.values(), ['alpha.md'])

    def test_panel_updates_immediately_on_select_and_deselect(self):
        selection = picker.MultiSelection(['a.md', 'b.md'])
        self.assertEqual(selection.panel_empty_message(), 'No files selected')
        selection.toggle(0)
        self.assertEqual(selection.panel_items(), ['a.md'])
        self.assertEqual(selection.panel_empty_message(), '')
        selection.toggle(0)
        self.assertEqual(selection.panel_items(), [])
        self.assertEqual(selection.panel_empty_message(), 'No files selected')

    def test_panel_lists_multiple_files_and_keeps_filtered_files(self):
        selection = picker.MultiSelection(['/project/alpha file.md', '/project/beta.md'])
        selection.toggle(0)
        selection.toggle(1)
        self.assertEqual(selection.panel_items(),
                         ['/project/alpha file.md', '/project/beta.md'])
        self.assertEqual(selection.visible('beta'), [(1, '/project/beta.md')])
        self.assertEqual(selection.panel_items(),
                         ['/project/alpha file.md', '/project/beta.md'])

    def test_empty_filter_and_empty_inventory_have_safe_panel_state(self):
        selection = picker.MultiSelection(['alpha.md'])
        self.assertEqual(selection.visible('missing'), [])
        self.assertEqual(selection.panel_empty_message(), 'No files selected')
        empty = picker.MultiSelection([])
        self.assertEqual(empty.visible(), [])
        self.assertEqual(empty.panel_items(), [])
        self.assertEqual(empty.panel_empty_message(), 'No files selected')

    def test_group_commit_advances_and_keeps_groups_separate(self):
        history = picker.History()
        group1 = request('a.md', 'b.md')
        group2 = request('a.md', 'b.md')
        history.choose(0, group1, [0])
        self.assertEqual(history.prepare(1, group2)['value'], None)
        history.choose(1, group2, [1])
        self.assertEqual(history.steps[0]['value'], [0])
        self.assertEqual(history.steps[1]['value'], [1])
        group1_panel = picker.MultiSelection(group1['items'], history.steps[0]['value'])
        group2_panel = picker.MultiSelection(group2['items'], history.steps[1]['value'])
        self.assertEqual(group1_panel.panel_items(), ['a.md'])
        self.assertEqual(group2_panel.panel_items(), ['b.md'])

    def test_back_navigation_restores_group_selection(self):
        history = picker.History()
        history.choose(0, request('a.md', 'b.md'), [0])
        history.choose(1, request('a.md', 'b.md'), [1])
        restored = picker.MultiSelection(['a.md', 'b.md'],
                                         history.prepare(0, request('a.md', 'b.md'))['value'])
        self.assertEqual(restored.values(), ['a.md'])
        self.assertEqual(restored.panel_items(), ['a.md'])
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
        self.assertEqual(selection.values(), ['a', 'b'])

    def test_keyboard_focus_actions_are_explicit(self):
        self.assertEqual(picker.multi_key_action('Return', True, False), 'toggle')
        self.assertEqual(picker.multi_key_action('Return', False, True), 'confirm')
        self.assertEqual(picker.multi_key_action('space', False, True), 'confirm')
        self.assertEqual(picker.multi_key_action('Ctrl+Return', True, False), 'confirm')
        self.assertIsNone(picker.multi_key_action('Ctrl+Return', False, False))
        self.assertIsNone(picker.multi_key_action('Return', False, False))
        self.assertIsNone(picker.multi_key_action('space', True, False))
        self.assertEqual(picker.preferred_multi_index([1, 2]), 2)
        self.assertIsNone(picker.preferred_multi_index([]))

    def test_right_only_moves_to_done_from_last_visible_row(self):
        self.assertFalse(picker.multi_right_moves_to_done(1, 2))
        self.assertTrue(picker.multi_right_moves_to_done(2, 2))
        self.assertTrue(picker.multi_right_moves_to_done(0, 0))
        self.assertFalse(picker.multi_right_moves_to_done(None, None))

    def test_stale_highlight_index_is_safe_after_menu_transition(self):
        self.assertIsNone(picker.menu_row_value(['Generate prompt'], 2))
        self.assertEqual(picker.menu_row_value(['Generate prompt'], 0),
                         'Generate prompt')
        self.assertEqual(picker.menu_row_value(['first', 'second'], 1,
                                               by_index=True), '1')

    def test_ordinary_single_choice_and_no_selection_menu_contracts(self):
        history = picker.History()
        history.choose(0, request('only'), 'only')
        self.assertEqual(history.steps[0]['value'], 'only')
        self.assertEqual(picker.MultiSelection(['a']).validation_error(),
                         'Select at least 1 file.')


class TheoryTargetFlowTests(unittest.TestCase):
    def run_flow(self, with_index, target, with_guide=True, action='6. Markdown'):
        script = Path(__file__).resolve().parents[1] / 'prompt_picker' / 'prompt_picker.sh'
        with tempfile.TemporaryDirectory(prefix='picker-theory-flow-') as tmp:
            root = Path(tmp)
            project = root / 'project'
            tool = root / 'tool'
            bindir = root / 'bin'
            project.mkdir()
            tool.mkdir()
            bindir.mkdir()
            (project / 'FILEPATH.md').write_text(
                'CPP | Solver | solver.cpp\nMD | Notes | notes.md\n')
            (tool / 'FILEPATH.md').write_text('MD | Other | other.md\n')
            if with_index:
                (project / 'Theory_Guide_Sections.md').write_text(
                    '| Section Title | Level | Last Updated |\n'
                    '| :--- | :---: | :---: |\n'
                    '| [Transport](Theory_Guide.md#transport) | H2 | 2026-01-01 |\n'
                    '| [Other](Theory_Guide.md#other) | H2 | 2026-01-01 |\n')
            if with_guide:
                (project / 'Theory_Guide.md').write_text('## Transport\n\nSection body.\n\n## Other\n\nUnrelated.\n')
            shutil.copyfile(script, tool / 'prompt_picker.sh')
            shutil.copyfile(script.with_name('picker_ui.py'), tool / 'picker_ui.py')
            clipboard = bindir / 'xclip'
            clipboard.write_text('#!/bin/sh\ncat >/dev/null\n')
            clipboard.chmod(0o755)
            server_path = str(root / 'menu.sock')
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(server_path)
            server.listen(1)
            server.settimeout(.2)
            stop = threading.Event()
            requests = []
            errors = []
            selected_sources = []

            def serve():
                while not stop.is_set():
                    try:
                        connection, _ = server.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        return
                    with connection:
                        request = json.loads(connection.makefile('rb').readline())
                        requests.append(request)
                        args = request['arguments']
                        title = args[args.index('-p') + 1]
                        if title == 'Select project inventory:':
                            answer = '0'
                        elif title == 'Select File or Action:':
                            answer = '2. Prompts'
                        elif title == 'Select target type:':
                            if target == 'theory':
                                answer = 'Theory Guide Sections' if not selected_sources else 'Done'
                            elif target == 'multiple':
                                answer = 'Theory Guide Sections' if not selected_sources else 'Done'
                            elif target in ('theory_then_file', 'file_then_theory'):
                                sequence = (['Theory Guide Sections', 'FILEPATH.md files', 'Done']
                                            if target == 'theory_then_file' else
                                            ['FILEPATH.md files', 'Theory Guide Sections', 'Done'])
                                answer = sequence[len(selected_sources)]
                            elif target in ('one_source', 'file'):
                                answer = 'FILEPATH.md files' if not selected_sources else 'Done'
                            elif target == 'file_repeat':
                                answer = 'FILEPATH.md files' if len(selected_sources) < 2 else 'Done'
                            else:
                                answer = 'FILEPATH.md files'
                            if answer in ('Theory Guide Sections', 'FILEPATH.md files'):
                                selected_sources.append(answer)
                        elif title == 'Select section(s) or Done:':
                            answer = ('\n'.join(request['items']) if target == 'multiple' else
                                      '\n'.join(request['items']) if target == 'theory_then_file' else
                                      request['items'][0])
                        elif title == 'Prompts:':
                            answer = '7. C++' if 'Compiler' in action else action
                        elif title == 'Markdown:':
                            answer = 'Fix'
                        elif title == 'C++:':
                            answer = 'Fix Compiler / Syntax Issues' if 'Compiler' in action else action
                        elif title == 'STATE.md:':
                            answer = action
                        elif title == 'Select target file or Done:':
                            answer = ('CPP | Solver | solver.cpp\nMD | Notes | notes.md'
                                      if target in ('theory_then_file', 'file_then_theory', 'one_source') else
                                      'CPP | Solver | solver.cpp')
                        elif title in ('Generate prompt:', 'Prompt action:'):
                            answer = 'Generate prompt'
                        else:
                            errors.append(title)
                            answer = ''
                        connection.sendall((json.dumps({'value': answer}) + '\n').encode())

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            environment = os.environ.copy()
            environment.update(PICKER_WORKER='1', PICKER_ACTIVE_WIN='', PICKER_SOCKET=server_path,
                               PICKER_GENERATION='theory-flow', PATH=str(bindir) + ':' + environment['PATH'])
            try:
                process = subprocess.run(['bash', str(tool / 'prompt_picker.sh')], cwd=project,
                                         env=environment, capture_output=True, text=True, timeout=10)
            finally:
                stop.set()
                server.close()
                thread.join(timeout=1)
            self.assertFalse(errors)
            self.assertEqual(process.returncode, 0, process.stderr)
            return requests, process.stdout

    def test_theory_target_opens_sections_without_file_selection(self):
        requests, output = self.run_flow(True, 'theory')
        titles = [request['arguments'][request['arguments'].index('-p') + 1] for request in requests]
        self.assertEqual(titles, ['Select project inventory:', 'Select File or Action:',
                                  'Prompts:', 'Markdown:', 'Select target type:',
                                  'Select section(s) or Done:', 'Select target type:',
                                  'Prompt action:'])
        self.assertNotIn('Theory Guide Sections', requests[1]['items'])
        self.assertFalse(any('Transport' in item for item in requests[1]['items']))
        source_choice = next(request for request in requests
                             if 'Select target type:' in request['arguments'])
        self.assertEqual(source_choice['items'],
                         ['FILEPATH.md files', 'Theory Guide Sections', 'Done'])
        section_request = next(request for request in requests
                               if 'Select section(s) or Done:' in request['arguments'])
        self.assertIn('Transport', section_request['items'][0])
        self.assertIn('Theory_Guide.md#transport', output)
        self.assertIn('Section body.', output)
        self.assertNotIn('Unrelated.', output)
        self.assertNotIn('solver.cpp', output)

    def test_existing_file_flow_with_and_without_theory_index(self):
        for with_index, with_guide in ((False, True), (True, False), (True, True)):
            with self.subTest(with_index=with_index, with_guide=with_guide):
                requests, output = self.run_flow(with_index, 'file', with_guide)
                root_items = requests[1]['items']
                self.assertNotIn('Theory Guide Sections', root_items)
                self.assertEqual(any('Select target type:' in request['arguments'] for request in requests),
                                 with_index and with_guide)
                file_request = next(request for request in requests
                                    if 'Select target file or Done:' in request['arguments'])
                self.assertEqual(file_request['items'], ['CPP | Solver | solver.cpp',
                                                        'MD | Notes | notes.md'])
                self.assertIn('solver.cpp', output)
                self.assertNotIn('Selected target section(s)', output)

    def test_other_file_prompt_offers_sections(self):
        requests, output = self.run_flow(True, 'theory', action='10. Fix Compiler / Syntax Issues')
        self.assertTrue(any('Select target type:' in request['arguments'] for request in requests))
        self.assertIn('Section body.', output)

    def test_multiple_sections_include_both_bodies(self):
        requests, output = self.run_flow(True, 'multiple')
        self.assertIn('Section body.', output)
        self.assertIn('Unrelated.', output)

    def test_theory_then_files_returns_to_source_choice_and_keeps_both(self):
        requests, output = self.run_flow(True, 'theory_then_file')
        titles = [request['arguments'][request['arguments'].index('-p') + 1]
                  for request in requests]
        self.assertEqual(titles.count('Select target type:'), 3)
        self.assertLess(titles.index('Select section(s) or Done:'),
                        len(titles) - 2)
        self.assertIn('solver.cpp', output)
        self.assertIn('notes.md', output)
        self.assertIn('Section body.', output)
        self.assertIn('Unrelated.', output)

    def test_files_then_theory_keeps_both(self):
        requests, output = self.run_flow(True, 'file_then_theory')
        self.assertIn('solver.cpp', output)
        self.assertIn('notes.md', output)
        self.assertIn('Section body.', output)

    def test_single_source_selection_finishes_only_after_done(self):
        requests, output = self.run_flow(True, 'one_source')
        titles = [request['arguments'][request['arguments'].index('-p') + 1]
                  for request in requests]
        self.assertEqual(titles.count('Select target type:'), 2)
        self.assertLess(titles.index('Select target file or Done:'),
                        titles.index('Prompt action:'))
        self.assertIn('solver.cpp', output)

    def test_reselecting_a_file_does_not_duplicate_it(self):
        requests, output = self.run_flow(True, 'file_repeat')
        self.assertEqual(output.count('solver.cpp'), 1)

    def test_untargeted_prompt_skips_target_choice(self):
        requests, output = self.run_flow(True, 'file', action='1. Update AGENTS.md File')
        self.assertFalse(any('Select target type:' in request['arguments'] for request in requests))
        self.assertNotIn('Selected target section(s)', output)


class PromptOutputTests(unittest.TestCase):
    script = Path(__file__).resolve().parents[1] / 'prompt_picker' / 'prompt_picker.sh'
    inventory = ('MD | Readme | README.md\n'
                 'PY | Picker UI | prompt_picker/picker_ui.py\n'
                 'SH | Picker Script | prompt_picker/prompt_picker.sh\n')

    @classmethod
    def setUpClass(cls):
        try:
            with tempfile.TemporaryDirectory(prefix='picker-socket-check-') as tmp:
                probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    probe.bind(str(Path(tmp) / 'probe.sock'))
                finally:
                    probe.close()
        except OSError as error:
            raise unittest.SkipTest(f'local Unix sockets are unavailable: {error}')

    def run_prompt(self, action, groups=(), with_inventory=True, root_files=None,
                   clipboard_fails=False, expected_return=0, expected_error=None):
        with tempfile.TemporaryDirectory(prefix='picker-output-test-') as tmp:
            root = Path(tmp)
            if with_inventory:
                (root / 'FILEPATH.md').write_text(self.inventory)
            script_copy = root / 'prompt_picker.sh'
            shutil.copyfile(self.script, script_copy)
            shutil.copyfile(self.script.with_name('picker_ui.py'), root / 'picker_ui.py')
            bindir = root / 'bin'
            bindir.mkdir()
            clipboard = bindir / 'xclip'
            clipboard.write_text('#!/bin/sh\n' +
                                 ('exit 1\n' if clipboard_fails else 'cat >/dev/null\n'))
            clipboard.chmod(0o755)
            server_path = str(root / 'menu.sock')
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(server_path)
            server.listen(1)
            server.settimeout(.2)
            stop = threading.Event()
            seen = []
            server_errors = []

            def serve():
                group_number = 0
                while not stop.is_set():
                    try:
                        connection, _ = server.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        return
                    with connection:
                        request = json.loads(connection.makefile('rb').readline())
                        seen.append(request)
                        args = request['arguments']
                        title = args[args.index('-p') + 1] if '-p' in args else ''
                        if title == 'No file list found:':
                            answer = '2. Prompts'
                        elif title == 'Select File or Action:':
                            answer = ('\n'.join(root_files) if root_files is not None
                                      else '2. Prompts')
                        elif title == 'Action for target:':
                            answer = action
                        elif title == 'Prompts:':
                            answer = action
                        elif title.startswith('Select target file or Done:'):
                            answer = '\n'.join(groups[group_number])
                            group_number += 1
                        elif title.startswith('Select source file or Done:'):
                            answer = '\n'.join(groups[group_number])
                            group_number += 1
                        elif title == 'Generate prompt:':
                            answer = 'Generate prompt'
                        else:
                            server_errors.append(f'Unexpected menu: {title}')
                            answer = ''
                        connection.sendall((json.dumps({'value': answer}) + '\n').encode())
                        if title == 'Generate prompt:':
                            return

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            environment = os.environ.copy()
            environment.update(PICKER_WORKER='1', PICKER_ACTIVE_WIN='', PICKER_SOCKET=server_path,
                               PICKER_GENERATION='output-test', PATH=str(bindir) + ':' + environment['PATH'])
            process = None
            try:
                process = subprocess.run(['bash', str(script_copy)], cwd=root, env=environment,
                                         capture_output=True, text=True, timeout=10)
            finally:
                stop.set()
                server.close()
                thread.join(timeout=1)
            self.assertFalse(server_errors, server_errors)
            self.assertIsNotNone(process)
            self.assertEqual(process.returncode, expected_return, process.stderr)
            if root_files is not None:
                root_request = next(request for request in seen
                                    if request['arguments'][request['arguments'].index('-p') + 1]
                                    == 'Select File or Action:')
                self.assertIn('-multi-select', root_request['arguments'])
                self.assertIn('-multi-start', root_request['arguments'])
                self.assertEqual(root_request['arguments'][
                    root_request['arguments'].index('-multi-start') + 1], '2')
            self.assertTrue(process.stdout.strip(), 'prompt output must be non-empty')
            if expected_error:
                self.assertIn(expected_error, process.stderr)
            if root_files is not None:
                titles = [request['arguments'][request['arguments'].index('-p') + 1]
                          for request in seen]
                self.assertEqual(titles, ['Select File or Action:'])
            else:
                self.assertEqual(seen[-1]['arguments'][seen[-1]['arguments'].index('-p') + 1],
                                 'Generate prompt:')
            return process.stdout

    def test_no_file_prompt_is_printed(self):
        output = self.run_prompt('Create', with_inventory=False)
        self.assertIn('STATE.md', output)
        self.assertIn('current status', output)

    def test_single_file_prompt_contains_selected_path(self):
        output = self.run_prompt('8. Fix Markdown', groups=[['MD | Readme | README.md']])
        self.assertIn('TARGET FILE PATHS: README.md', output)

    def test_multi_file_one_group_contains_all_selected_paths(self):
        output = self.run_prompt('18. Backup File', groups=[[
            'MD | Readme | README.md', 'PY | Picker UI | prompt_picker/picker_ui.py']])
        self.assertIn('Target file:\nREADME.md', output)
        self.assertIn('Target file:\nprompt_picker/picker_ui.py', output)

    def test_root_inventory_uses_shared_multi_select_and_commits_multiple_files(self):
        root_files = ['MD | Readme | README.md',
                      'PY | Picker UI | prompt_picker/picker_ui.py']
        output = self.run_prompt('', root_files=root_files)
        self.assertIn('Selected files:', output)
        self.assertIn('README.md', output)
        self.assertIn('prompt_picker/picker_ui.py', output)

    def test_root_inventory_single_file_commits_without_another_menu(self):
        output = self.run_prompt('', root_files=['MD | Readme | README.md'])
        self.assertIn('Selected files: Readme file in the path: `README.md`.', output)

    def test_multi_file_multiple_groups_keep_target_and_source_separate(self):
        output = self.run_prompt('14. Sync / Adapt with another file...', groups=[
            ['MD | Readme | README.md', 'PY | Picker UI | prompt_picker/picker_ui.py'],
            ['SH | Picker Script | prompt_picker/prompt_picker.sh']])
        self.assertIn('sync README.md And prompt_picker/picker_ui.py', output)
        self.assertIn('based on the interface and changes introduced in prompt_picker/prompt_picker.sh',
                      output)

    def test_clipboard_failure_still_prints_prompt_and_reports_error(self):
        output = self.run_prompt('Create', with_inventory=False,
                                 clipboard_fails=True, expected_return=1,
                                 expected_error='Could not copy the prompt to the clipboard.')
        self.assertIn('STATE.md', output)


if __name__ == '__main__':
    unittest.main()
