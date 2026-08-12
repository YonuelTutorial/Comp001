import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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
            "open_file", "save_file", "run_code", "build_code", "compile_assembly",
            "compile_javascript", "compile_web_game", "open_folder", "toggle_explorer",
            "start_debug", "find_text",
        ):
            self.assertTrue(callable(getattr(app.MainApp, command)))

    def test_javascript_panel_is_configured(self):
        self.assertIn("JavaScript", app.MainApp.PANEL_NAMES)

    def test_compile_menu_contains_all_targets(self):
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
            "Archivo", "Compilar", "Editar", "Ver",
        ])
        self.assertIn("Abrir carpeta...", [item["label"] for item in menus[1].commands])
        self.assertEqual([item["label"] for item in menus[2].commands], [
            "Compilar", "Compilar a pseudoensamblador...", "Compilar a JavaScript...",
            "Compilar juego web (.html)...",
        ])
        self.assertEqual(menus[2].commands[0]["accelerator"], "F7")
        bindings = {call.args[0]: call.args[1] for call in fake.root.bind.call_args_list}
        self.assertIn("<F5>", bindings)
        self.assertIn("<F7>", bindings)
        fake.run_code = Mock()
        fake.build_code = Mock()
        bindings["<F5>"](None)
        bindings["<F7>"](None)
        fake.run_code.assert_called_once_with()
        fake.build_code.assert_called_once_with()

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
        fake.notebook = Mock()
        fake.panels = {
            "Pseudoensamblador": SimpleNamespace(master=object()),
            "Salida": SimpleNamespace(master=object()),
        }
        return fake

    def test_f7_builds_without_execution_or_input(self):
        fake = self._fake_app("print(inputInt());")
        with patch.object(app.Compiler, "compile_and_run") as compile_and_run:
            self.assertTrue(fake.build_code())
        compile_and_run.assert_not_called()
        self.assertEqual(fake.last_result.output, "")
        fake._show_result.assert_called_once_with(fake.last_result)
        fake._set_panel.assert_called_once_with("Errores", "")
        fake.notebook.select.assert_called_once_with(fake.panels["Pseudoensamblador"].master)
        fake.status.set.assert_called_once_with("Compilación completada")

    def test_f7_reports_compilation_errors(self):
        fake = self._fake_app("int valor = ;")
        self.assertFalse(fake.build_code())
        self.assertIsNone(fake.last_result)
        fake._show_result.assert_not_called()
        fake._show_error.assert_called_once()
        fake.status.set.assert_called_once_with("Compilación fallida")

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

    def test_compile_web_game_writes_a_self_contained_html(self):
        source = """
        void iniciar(){gameInit(320, 200);}
        void actualizar(float delta){}
        void dibujar(){gameClear("black");}
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "juego.html"
            fake = self._fake_app(source)
            with patch("app.filedialog.asksaveasfilename", return_value=str(path)) as dialog:
                self.assertTrue(fake.compile_web_game())
            exported = path.read_text(encoding="utf-8")
        self.assertEqual(exported, fake.last_result.game_html)
        self.assertIn('<canvas id="minilang-canvas"', exported)
        self.assertIn("requestAnimationFrame", exported)
        fake.status.set.assert_called_once_with(f"Compilado a Juego web: {path}")
        self.assertEqual(dialog.call_args.kwargs["initialfile"], "programa.html")

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
