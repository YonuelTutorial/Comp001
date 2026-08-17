import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import app
from minilang import Compiler


class GuiHelpersTests(unittest.TestCase):
    def test_empty_initial_source_compiles(self):
        self.assertEqual(app.DEMO_SOURCE.strip(), "")
        result = Compiler(max_steps=1_000_000).compile_and_run(app.DEMO_SOURCE)
        self.assertEqual(result.output, "")

    def test_self_test(self):
        self.assertEqual(app.run_self_test(), 0)

    def test_editor_keywords(self):
        for keyword in ("for", "float", "import", "string"):
            self.assertIn(keyword, app.CodeEditor.KEYWORDS)

    def test_main_app_commands_exist(self):
        for command in (
            "open_file", "save_file", "run_code", "build_code", "compile_assembly",
            "compile_javascript", "compile_web_game", "open_folder", "toggle_explorer",
            "start_debug", "find_text", "show_compiling", "close_current_tab",
            "create_explorer_file", "rename_explorer_file", "remove_explorer_file",
        ):
            self.assertTrue(callable(getattr(app.MainApp, command)))

    def test_javascript_panel_is_configured(self):
        self.assertIn("JavaScript", app.MainApp.PANEL_NAMES)

    def test_title_includes_version_and_author_data(self):
        fake = object.__new__(app.MainApp)
        fake.root = Mock()
        fake.current_file = None
        fake.dirty = False

        fake.update_title()

        fake.root.title.assert_called_once_with(
            "Sin título — Mini-Lang v4.6 — Yonuel Peña — 2190790 — 17/08/2026"
        )

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
        fake.show_compiling = Mock()
        with patch("app.tk.Menu", FakeMenu):
            fake._menu()
        self.assertEqual([item["label"] for item in menus[0].cascades], [
            "Archivo", "Compilar", "Editar", "Ver",
        ])
        self.assertIn("Abrir carpeta...", [item["label"] for item in menus[1].commands])
        close_tab = next(item for item in menus[1].commands if item["label"] == "Cerrar pestaña")
        self.assertEqual(close_tab["accelerator"], "Ctrl+W")
        self.assertEqual([item["label"] for item in menus[2].commands], [
            "Compilar", "Compilar a pseudoensamblador...", "Compilar a JavaScript...",
            "Compilar juego web (.html)...",
        ])
        self.assertEqual(menus[2].commands[0]["accelerator"], "F7")
        bindings = {call.args[0]: call.args[1] for call in fake.root.bind.call_args_list}
        self.assertIn("<F5>", bindings)
        self.assertIn("<F7>", bindings)
        self.assertIn("<Control-w>", bindings)
        fake.run_code = Mock()
        fake.build_code = Mock()
        fake.compile_assembly = Mock()
        fake.compile_javascript = Mock()
        fake.compile_web_game = Mock()
        bindings["<F5>"](None)
        bindings["<F7>"](None)
        fake.run_code.assert_called_once_with()
        fake.build_code.assert_not_called()
        fake.show_compiling.assert_called_once_with(fake.build_code)

        fake.show_compiling.reset_mock()
        for item in menus[2].commands:
            item["command"]()
        self.assertEqual(fake.show_compiling.call_args_list, [
            call(fake.build_code),
            call(fake.compile_assembly),
            call(fake.compile_javascript),
            call(fake.compile_web_game),
        ])

    def test_compiling_dialog_uses_configured_delay_without_showing_the_number(self):
        fake = object.__new__(app.MainApp)
        fake.root = Mock()
        fake.compilation_dialog = None
        action = Mock()
        dialog = Mock()
        dialog.winfo_exists.return_value = True
        content = Mock()
        label = Mock()
        progress = Mock()

        with (
            patch("app.tk.Toplevel", return_value=dialog),
            patch("app.ttk.Frame", return_value=content),
            patch("app.ttk.Label", return_value=label) as label_factory,
            patch("app.ttk.Progressbar", return_value=progress),
        ):
            self.assertTrue(fake.show_compiling(action))

        self.assertEqual(label_factory.call_args.kwargs["text"], "Compilando...")
        self.assertNotIn("3", label_factory.call_args.kwargs["text"])
        progress.start.assert_called_once_with(12)
        delay, finish = fake.root.after.call_args.args
        self.assertEqual(delay, app.MainApp.COMPILATION_WAIT_MS)
        action.assert_not_called()

        finish()
        progress.stop.assert_called_once_with()
        dialog.grab_release.assert_called_once_with()
        dialog.destroy.assert_called_once_with()
        fake.root.after_idle.assert_called_once_with(action)

    def test_compiling_dialog_does_not_open_twice(self):
        fake = object.__new__(app.MainApp)
        fake.root = Mock()
        fake.compilation_dialog = Mock()
        fake.compilation_dialog.winfo_exists.return_value = True

        with patch("app.tk.Toplevel") as toplevel:
            self.assertFalse(fake.show_compiling(Mock()))

        toplevel.assert_not_called()
        fake.compilation_dialog.lift.assert_called_once_with()
        fake.compilation_dialog.focus_force.assert_called_once_with()

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
