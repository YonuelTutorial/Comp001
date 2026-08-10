import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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
        for command in (
            "open_file", "save_file", "run_code", "compile_assembly",
            "compile_javascript", "start_debug", "find_text",
        ):
            self.assertTrue(callable(getattr(app.MainApp, command)))

    def test_javascript_panel_is_configured(self):
        self.assertIn("JavaScript", app.MainApp.PANEL_NAMES)

    def test_compile_menu_contains_both_targets(self):
        menus = []

        class FakeMenu:
            def __init__(self, *_args, **_kwargs):
                self.commands = []
                self.cascades = []
                menus.append(self)

            def add_command(self, **options):
                self.commands.append(options)

            def add_separator(self):
                return None

            def add_cascade(self, **options):
                self.cascades.append(options)

        fake = object.__new__(app.MainApp)
        fake.root = Mock()
        with patch("app.tk.Menu", FakeMenu):
            fake._menu()
        self.assertEqual([item["label"] for item in menus[0].cascades], [
            "Archivo", "Compilar", "Editar",
        ])
        self.assertEqual([item["label"] for item in menus[2].commands], [
            "Compilar a pseudoensamblador...", "Compilar a JavaScript...",
        ])

    @staticmethod
    def _fake_app(source, current_file=None):
        fake = object.__new__(app.MainApp)
        fake.root = None
        fake.current_file = current_file
        fake.editor = Mock()
        fake.editor.get.return_value = source
        fake.status = Mock()
        fake.last_result = None
        fake._show_result = Mock()
        fake._set_panel = Mock()
        fake._show_error = Mock()
        return fake

    def test_compile_assembly_writes_the_optimized_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "ejemplo.mini"
            path = Path(directory) / "ejemplo.asm"
            fake = self._fake_app("print(2 + 3);", source_path)
            with patch("app.filedialog.asksaveasfilename", return_value=str(path)) as dialog:
                self.assertTrue(fake.compile_assembly())
            exported = path.read_text(encoding="utf-8")
        self.assertEqual(exported, fake.last_result.assembly)
        self.assertIn("PRINT", exported)
        fake._show_error.assert_not_called()
        fake.status.set.assert_called_once_with(f"Compilado a Pseudoensamblador: {path}")
        options = dialog.call_args.kwargs
        self.assertEqual(options["initialfile"], "ejemplo.asm")
        self.assertIn(("Binario simulado", "*.bin"), options["filetypes"])

    def test_compile_javascript_writes_an_executable_script(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "programa.js"
            fake = self._fake_app('print("JavaScript");')
            with patch("app.filedialog.asksaveasfilename", return_value=str(path)):
                self.assertTrue(fake.compile_javascript())
            exported = path.read_text(encoding="utf-8")
        self.assertEqual(exported, fake.last_result.javascript)
        self.assertTrue(exported.startswith('"use strict";'))
        self.assertIn("__ml_print", exported)
        fake.status.set.assert_called_once_with(f"Compilado a JavaScript: {path}")

    @unittest.skipUnless(shutil.which("node"), "Node.js no está disponible")
    def test_exported_javascript_runs_with_node(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "programa.js"
            fake = self._fake_app('print("Compilado");')
            with patch("app.filedialog.asksaveasfilename", return_value=str(path)):
                self.assertTrue(fake.compile_javascript())
            completed = subprocess.run(
                ["node", str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "Compilado")

    def test_cancelled_compilation_does_not_change_the_result(self):
        fake = self._fake_app("print(1);")
        with patch("app.filedialog.asksaveasfilename", return_value=""):
            self.assertFalse(fake.compile_assembly())
        self.assertIsNone(fake.last_result)
        fake._show_result.assert_not_called()
        fake.status.set.assert_not_called()

    def test_compile_error_does_not_open_the_save_dialog(self):
        fake = self._fake_app("int valor = ;")
        with patch("app.filedialog.asksaveasfilename") as dialog:
            self.assertFalse(fake.compile_assembly())
        dialog.assert_not_called()
        fake._show_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
