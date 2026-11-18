"""Opt-in X11 tests. These focus and send keys to a real desktop window."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
XDO = shutil.which('xdotool')
GUI_TESTS = bool(os.environ.get('PICKER_GUI_TESTS') and os.environ.get('DISPLAY') and XDO)


@unittest.skipUnless(GUI_TESTS, 'set PICKER_GUI_TESTS=1 on an X11 desktop')
class PickerGuiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='picker-test-')
        self.root = Path(self.tmp.name)
        self.original_cwd = os.getcwd()
        os.chdir(self.root)
        self.children = []
        for name in ('alpha', 'beta'):
            project = self.root / name
            project.mkdir()
            (project / 'FILEPATH.md').write_text(
                f'MD | {name.title()} Entry | {name}.md\n'
                f'PY | {name.title()} Script | {name}.py\n')
            self.children.append(subprocess.Popen(['sleep', '60'], cwd=project))
        bindir = self.root / 'bin'
        bindir.mkdir()
        (bindir / 'xdotool').write_text(
            '#!/bin/bash\ncase "$1" in getactivewindow) echo 42;; '
            'getwindowpid) echo "$TEST_PARENT";; *) exit 1;; esac\n')
        (bindir / 'xclip').write_text(
            '#!/bin/bash\nif [[ " $* " == *" -o "* ]]; then echo test; else cat >/dev/null; fi\n')
        for file in bindir.iterdir():
            file.chmod(0o755)
        self.log_path = self.root / 'log'
        self.log = self.log_path.open('w+')
        env = os.environ.copy()
        env.update(PATH=str(bindir) + ':' + env['PATH'], TEST_PARENT=str(os.getpid()), PICKER_DEBUG='1')
        self.app = subprocess.Popen(['bash', str(ROOT / 'prompt_picker/prompt_picker.sh')],
                                    cwd=self.root, env=env, stdout=subprocess.PIPE,
                                    stderr=self.log, text=True)
        self.win = None
        self.addCleanup(self.cleanup_picker)
        for _ in range(160):
            found = self.xdo('search', '--onlyvisible', '--pid', str(self.app.pid), '--name', '^Prompt Picker$')
            if found.stdout.strip():
                self.win = found.stdout.splitlines()[-1]
                break
            time.sleep(.05)
        self.assertIsNotNone(self.win, 'picker window not found: ' + self.log_path.read_text())
        self.xdo('windowactivate', '--sync', self.win)
        self.wait_menu('MENU 0 Select project inventory:', 1)

    def cleanup_picker(self):
        if self.app.poll() is None:
            if self.win:
                self.xdo('windowactivate', '--sync', self.win)
                self.xdo('key', 'Escape')
            try:
                self.app.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.app.terminate()
                self.app.wait(timeout=3)
        for child in self.children:
            child.terminate()
            child.wait()
        self.log.close()
        os.chdir(self.original_cwd)
        self.tmp.cleanup()

    def xdo(self, *args):
        return subprocess.run([XDO, *args], capture_output=True, text=True, timeout=5)

    def keys(self, *keys):
        for key in keys:
            self.assertEqual(self.xdo('key', key).returncode, 0)
            time.sleep(.15)

    def type_text(self, value):
        self.assertEqual(self.xdo('type', '--clearmodifiers', '--', value).returncode, 0)
        time.sleep(.15)

    def wait_menu(self, text, count):
        for _ in range(120):
            if self.log_path.read_text().count(text) >= count:
                return
            time.sleep(.05)
        self.fail('menu did not appear: ' + text + '\n' + self.log_path.read_text())

    def test_back_change_inventory_forward_and_confirm(self):
        self.keys('Left', 'Down', 'Up', 'Right')
        self.wait_menu('MENU 1 Select File or Action:', 1)
        self.type_text('alpha entry')
        self.keys('Return')
        self.wait_menu('MENU 2 Action for target:', 1)
        self.keys('Left')
        self.wait_menu('MENU 1 Select File or Action:', 2)
        self.keys('Left')
        self.wait_menu('MENU 0 Select project inventory:', 2)
        self.type_text('bta')
        self.keys('ctrl+b', 'ctrl+b')
        self.type_text('e')
        self.keys('Return')
        self.wait_menu('MENU 1 Select File or Action:', 3)
        self.type_text('beta entry')
        self.keys('Return')
        self.wait_menu('MENU 2 Action for target:', 2)
        self.keys('Left')
        self.wait_menu('MENU 1 Select File or Action:', 4)
        self.keys('Right')
        self.wait_menu('MENU 2 Action for target:', 3)
        self.keys('Right')
        self.wait_menu('MENU 3 Generate prompt:', 1)
        self.keys('Right')
        self.assertIsNone(self.app.poll(), 'Right must not generate the prompt')
        self.keys('Return')
        output, _ = self.app.communicate(timeout=8)
        self.assertIn('beta.md', output)
        self.assertNotIn('alpha.md', output)

    def test_escape_cancels_without_output(self):
        self.keys('Escape')
        output, _ = self.app.communicate(timeout=5)
        self.assertEqual(output, '')

    def test_multi_file_done_is_keyboard_reachable_and_activatable(self):
        self.keys('Left', 'Down', 'Up', 'Right')
        self.wait_menu('MENU 1 Select File or Action:', 1)
        self.type_text('Main Project Prompts')
        self.keys('Return')
        self.wait_menu('MENU 2 Main Project Prompts:', 1)
        self.type_text('Fix Markdown')
        self.keys('Return')
        self.wait_menu('MENU 3 Select target file or Done:', 1)

        # Select the last visible row, then use the physical Right Arrow to
        # reveal/focus Done. Right alone must not commit the group.
        self.keys('Down', 'Return', 'Right')
        self.assertIsNone(self.app.poll(), 'Right must not commit the group')
        self.keys('Return')
        self.wait_menu('MENU 4 Generate prompt:', 1)
        self.assertIsNone(self.app.poll(), 'group confirmation must not generate the prompt')

        # Back restores the selected row and puts keyboard focus on the list.
        self.keys('Left')
        self.wait_menu('MENU 3 Select target file or Done:', 2)
        self.keys('ctrl+Return')
        self.wait_menu('MENU 4 Generate prompt:', 2)
        self.keys('Return')
        output, _ = self.app.communicate(timeout=8)
        self.assertIn('alpha.py', output)
        self.assertNotIn('alpha.md', output)

    def test_root_inventory_multi_select_done_is_keyboard_reachable(self):
        self.keys('Left', 'Down', 'Up', 'Right')
        self.wait_menu('MENU 1 Select File or Action:', 1)

        # The two action rows precede inventory rows. Toggle two files, then
        # highlight the last selected file so Right reveals and focuses Done.
        self.keys('Down', 'Down', 'Return', 'Down', 'Return', 'Right')
        self.assertIsNone(self.app.poll(), 'Right must not commit the root group')
        self.keys('Return')
        output, _ = self.app.communicate(timeout=8)
        self.assertIn('alpha.md', output)
        self.assertIn('alpha.py', output)
        self.assertNotIn('Action for target:', self.log_path.read_text())

    def test_root_inventory_single_file_done_finishes_without_another_menu(self):
        self.keys('Left', 'Down', 'Up', 'Right')
        self.wait_menu('MENU 1 Select File or Action:', 1)
        self.keys('Down', 'Down', 'Return', 'Right')
        self.assertIsNone(self.app.poll(), 'Right must reveal Done without committing')
        self.keys('Return')
        output, _ = self.app.communicate(timeout=8)
        self.assertIn('alpha.md', output)
        log = self.log_path.read_text()
        self.assertNotIn('Action for target:', log)
        self.assertNotIn('MENU 2', log)

    def test_window_manager_close_cancels_without_output(self):
        if not shutil.which('wmctrl'):
            self.skipTest('wmctrl is unavailable')
        subprocess.run(['wmctrl', '-ic', hex(int(self.win))], check=True)
        output, _ = self.app.communicate(timeout=5)
        self.assertEqual(output, '')


if __name__ == '__main__':
    unittest.main()
