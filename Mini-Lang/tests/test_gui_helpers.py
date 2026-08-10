import unittest

import app
from minilang import Compiler


class GuiHelpersTests(unittest.TestCase):
    def test_demo_compiles(self):
        result = Compiler(max_steps=1_000_000).compile_and_run(app.DEMO_SOURCE)
        self.assertEqual(result.output, "Lista ordenada:\n1\n3\n5\n8\n9")

    def test_self_test(self):
        self.assertEqual(app.run_self_test(), 0)

    def test_editor_keywords(self):
        for keyword in ("for", "float", "import", "string"):
            self.assertIn(keyword, app.CodeEditor.KEYWORDS)

    def test_main_app_commands_exist(self):
        for command in ("open_file", "save_file", "run_code", "start_debug", "find_text"):
            self.assertTrue(callable(getattr(app.MainApp, command)))


if __name__ == "__main__":
    unittest.main()
