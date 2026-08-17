import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import app


class FakeText:
    def __init__(self):
        self.focus_calls = 0

    def focus_set(self):
        self.focus_calls += 1


class FakeEditor:
    counter = 0

    def __init__(self, _parent, on_change, on_cursor):
        type(self).counter += 1
        self.widget_name = f"editor-{type(self).counter}"
        self.on_change = on_change
        self.on_cursor = on_cursor
        self.font_size = 11
        self.text = FakeText()
        self.source = ""
        self.destroyed = False

    def __str__(self):
        return self.widget_name

    def set(self, source):
        self.source = source

    def get(self):
        return self.source

    def set_font_size(self, size):
        self.font_size = size

    def destroy(self):
        self.destroyed = True


class FakeNotebook:
    def __init__(self):
        self.documents = []
        self.selected = ""
        self.labels = {}

    def add(self, editor, **_options):
        self.documents.append(str(editor))

    def select(self, editor=None):
        if editor is not None:
            self.selected = str(editor)
        return self.selected

    def tab(self, editor, **options):
        if "text" in options:
            self.labels[str(editor)] = options["text"]
        return {"text": self.labels.get(str(editor), "")}

    def forget(self, editor):
        key = str(editor)
        self.documents.remove(key)
        if self.selected == key:
            self.selected = self.documents[0] if self.documents else ""


def fake_tab_app():
    instance = object.__new__(app.MainApp)
    instance.root = Mock()
    instance.status = Mock()
    instance.project_dir = None
    instance.editor_tabs = {}
    instance.editor_notebook = FakeNotebook()
    instance.untitled_counter = 0
    instance.editor = None
    instance.current_file = None
    instance.dirty = False
    return instance


class EditorTabsTests(unittest.TestCase):
    def setUp(self):
        FakeEditor.counter = 0

    def test_each_tab_keeps_its_own_source_path_and_dirty_state(self):
        instance = fake_tab_app()
        with patch("app.CodeEditor", FakeEditor):
            first = instance._create_editor_tab("print(1);")
            instance.mark_dirty()
            second = instance._create_editor_tab("print(2);")

        self.assertTrue(first.dirty)
        self.assertFalse(second.dirty)
        self.assertEqual(first.editor.get(), "print(1);")
        self.assertEqual(second.editor.get(), "print(2);")
        self.assertEqual(instance.editor_notebook.labels[str(first.editor)], "*Sin título")
        self.assertEqual(instance.editor_notebook.labels[str(second.editor)], "Sin título 2")

        instance.editor_notebook.select(first.editor)
        instance._on_editor_tab_changed()
        self.assertIs(instance.editor, first.editor)
        self.assertTrue(instance.dirty)

    def test_opening_a_path_twice_reuses_the_existing_tab(self):
        instance = fake_tab_app()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "programa.mini"
            path.write_text("print(1);", encoding="utf-8")
            instance.project_dir = root
            with patch("app.CodeEditor", FakeEditor):
                self.assertTrue(instance._open_editor_file(path))
                first = instance._active_document()
                self.assertTrue(instance._open_editor_file(path))

        self.assertEqual(len(instance.editor_tabs), 1)
        self.assertIs(instance._active_document(), first)
        self.assertEqual(instance.status.set.call_args.args[0], f"Archivo ya abierto: {path.resolve()}")

    def test_ctrl_w_equivalent_can_cancel_or_discard_a_dirty_tab(self):
        instance = fake_tab_app()
        with patch("app.CodeEditor", FakeEditor):
            document = instance._create_editor_tab("print(1);")
            instance.mark_dirty()
            with patch("app.messagebox.askyesnocancel", return_value=None):
                self.assertFalse(instance.close_current_tab())
            self.assertIn(str(document.editor), instance.editor_tabs)

            with patch("app.messagebox.askyesnocancel", return_value=False):
                self.assertTrue(instance.close_current_tab())

        self.assertTrue(document.editor.destroyed)
        self.assertEqual(len(instance.editor_tabs), 1)
        self.assertIsNone(instance._active_document().path)

    def test_save_as_does_not_overwrite_a_file_open_in_another_tab(self):
        instance = fake_tab_app()
        instance.refresh_explorer = Mock()
        instance.set_project_folder = Mock()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_path = root / "uno.mini"
            second_path = root / "dos.mini"
            first_path.write_text("uno", encoding="utf-8")
            second_path.write_text("dos", encoding="utf-8")
            instance.project_dir = root
            with patch("app.CodeEditor", FakeEditor):
                first = instance._create_editor_tab("uno", path=first_path)
                instance._create_editor_tab("dos", path=second_path)
            with (
                patch("app.filedialog.asksaveasfilename", return_value=str(first_path)),
                patch("app.messagebox.showerror") as showerror,
            ):
                self.assertFalse(instance.save_as())
            self.assertEqual(first_path.read_text(encoding="utf-8"), "uno")
            self.assertIsNot(instance._active_document(), first)
            showerror.assert_called_once()

    def test_closing_the_ide_checks_each_dirty_tab_and_honors_cancel(self):
        instance = fake_tab_app()
        with patch("app.CodeEditor", FakeEditor):
            first = instance._create_editor_tab("uno")
            instance.mark_dirty()
            second = instance._create_editor_tab("dos")
            instance.mark_dirty()
        with patch("app.messagebox.askyesnocancel", side_effect=(False, None)) as confirm:
            self.assertFalse(instance.close())

        self.assertEqual(confirm.call_count, 2)
        self.assertIs(instance._active_document(), second)
        self.assertTrue(first.dirty)
        instance.root.destroy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
