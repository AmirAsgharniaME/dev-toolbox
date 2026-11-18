import pathlib
import re
import subprocess
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "prompt_picker" / "prompt_picker.sh"


class GitRemoveActionTests(unittest.TestCase):
    def test_remove_uses_current_grouped_picker_api_and_preserves_git_prompt(self):
        source = SCRIPT.read_text()
        match = re.search(
            r"show_remove_prompt\(\) \{(?P<body>.*?)\n\}", source, re.S
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn('select_prompt_target_files "remove"', body)
        self.assertIn('target_paths=$(select_prompt_target_files "remove") || return 0', body)
        self.assertIn('SELECTION_SUMMARY="remove (Group 1 of 1): $target_paths"', body)
        self.assertIn("git rm", body)
        self.assertIn('copy_and_paste_prompt "$REMOVE_MESSAGE"', body)
        self.assertNotIn('rofi -dmenu', body)
        self.assertNotIn('selected_count', body)

    def test_remove_passes_payload_and_stops_cleanly_on_selection_failure(self):
        source = SCRIPT.read_text()
        body = re.search(r"show_remove_prompt\(\) \{(?P<body>.*?)\n\}", source, re.S).group("body")
        script = f'''\
select_prompt_target_files() {{ printf '%s' "$SELECTION"; return "${{SELECT_STATUS:-0}}"; }}
copy_and_paste_prompt() {{ printf 'PROMPT=%s\\nSUMMARY=%s\\n' "$1" "$SELECTION_SUMMARY"; }}
show_remove_prompt() {{{body}
}}
show_remove_prompt
'''
        success = subprocess.run(
            ["bash"], input=script, text=True, capture_output=True,
            env={"SELECTION": "src/a.cpp And src/b.cpp"}, check=True,
        )
        self.assertIn("PROMPT=Safely remove the following files", success.stdout)
        self.assertIn("git rm", success.stdout)
        self.assertIn("SUMMARY=remove (Group 1 of 1): src/a.cpp And src/b.cpp", success.stdout)

        failure = subprocess.run(
            ["bash"], input=script, text=True, capture_output=True,
            env={"SELECTION": "", "SELECT_STATUS": "1"}, check=True,
        )
        self.assertEqual(failure.stdout, "")


if __name__ == "__main__":
    unittest.main()
