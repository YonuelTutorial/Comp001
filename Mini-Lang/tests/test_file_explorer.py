import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import app


class FakeTree:
    def __init__(self):
        self.nodes = {}
        self.children = {"": []}
        self.counter = 0
        self.focused = ""
        self.selected = ""

    def insert(self, parent, _index, **options):
        self.counter += 1
        item = f"item-{self.counter}"
        self.nodes[item] = {"parent": parent, **options}
        self.children.setdefault(parent, []).append(item)
        self.children[item] = []
        return item

    def get_children(self, item=""):
        return tuple(self.children.get(item, ()))

    def delete(self, *items):
        for item in items:
            self._delete_one(item)

    def _delete_one(self, item):
        for child in tuple(self.children.get(item, ())):
            self._delete_one(child)
        parent = self.nodes.get(item, {}).get("parent")
        if parent in self.children and item in self.children[parent]:
            self.children[parent].remove(item)
        self.children.pop(item, None)
        self.nodes.pop(item, None)

    def item(self, item, option=None, **options):
        if options:
            self.nodes[item].update(options)
        if option is not None:
            return self.nodes[item].get(option, False)
        return self.nodes[item]

    def focus(self, item=None):
        if item is not None:
            self.focused = item
        return self.focused

    def selection_set(self, item):
        self.selected = item

    def identify_row(self, _y):
        return self.focused


def fake_explorer():
    instance = object.__new__(app.MainApp)
    instance.root = Mock()
    instance.project_dir = None
    instance.project_name = Mock()
    instance.status = Mock()
    instance.explorer = FakeTree()
    instance.explorer_paths = {}
    instance.explorer_loaded = set()
    instance.editor_tabs = {}
    instance.editor_notebook = Mock()
    instance.set_explorer_visible = Mock()
    return instance


def fake_editor(project_dir):
    instance = object.__new__(app.MainApp)
    instance.root = None
    instance.project_dir = project_dir
    instance.current_file = None
    instance.dirty = False
    instance.editor = Mock()
    instance.editor_tabs = {}
    instance.editor_notebook = Mock()
    instance.status = Mock()
    instance.update_title = Mock()
    instance._confirm_discard = Mock(return_value=True)
    instance.set_project_folder = Mock()
    instance.created_documents = []

    def create_tab(source="", path=None, dirty=False, select=True):
        editor = Mock()
        document = app.EditorDocument(
            editor=editor,
            path=Path(path).resolve() if path is not None else None,
            dirty=dirty,
            untitled_name="Sin título",
        )
        instance.created_documents.append(document)
        instance.editor_tabs[str(editor)] = document
        if select:
            instance.editor = editor
            instance.current_file = document.path
            instance.dirty = document.dirty
        return document

    instance._create_editor_tab = Mock(side_effect=create_tab)
    return instance


def focus_explorer_entry(instance, name):
    root_item = instance.explorer.get_children("")[0]
    candidates = (root_item, *instance.explorer.get_children(root_item))
    for item in candidates:
        if instance.explorer.item(item).get("text") == name:
            instance.explorer.focus(item)
            return item
    raise AssertionError(f"No se encontró {name} en el explorador")


class FileExplorerTests(unittest.TestCase):
    def test_project_entries_put_directories_first_and_hide_internal_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "zeta").mkdir()
            (root / "Alpha").mkdir()
            (root / ".git").mkdir()
            (root / "__pycache__").mkdir()
            (root / "b.mini").write_text("print(2);", encoding="utf-8")
            (root / "A.mini").write_text("print(1);", encoding="utf-8")
            names = [entry.name for entry in app.MainApp.project_entries(root)]
        self.assertEqual(names, ["Alpha", "zeta", "A.mini", "b.mini"])

    def test_project_entries_do_not_include_reparse_points(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "normal.mini").write_text("print(1);", encoding="utf-8")
            (root / "enlace").mkdir()
            original = app.MainApp._is_reparse_point
            with patch.object(
                app.MainApp,
                "_is_reparse_point",
                side_effect=lambda path: path.name == "enlace" or original(path),
            ):
                names = [entry.name for entry in app.MainApp.project_entries(root)]
        self.assertEqual(names, ["normal.mini"])

    def test_setting_project_loads_only_the_first_level(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "src"
            nested.mkdir()
            (nested / "interno.mini").write_text("print(1);", encoding="utf-8")
            (root / "principal.mini").write_text("print(2);", encoding="utf-8")
            instance = fake_explorer()
            instance.set_project_folder(root)
            root_item = instance.explorer.get_children("")[0]
            first_level = instance.explorer.get_children(root_item)
            labels = [instance.explorer.item(item)["text"] for item in first_level]
            folder_item = first_level[0]
            self.assertEqual(labels, ["src", "principal.mini"])
            self.assertNotIn(folder_item, instance.explorer_loaded)
            self.assertEqual(len(instance.explorer.get_children(folder_item)), 1)
            instance._load_explorer_node(folder_item)
            nested_labels = [
                instance.explorer.item(item)["text"]
                for item in instance.explorer.get_children(folder_item)
            ]
        self.assertEqual(nested_labels, ["interno.mini"])
        instance.set_explorer_visible.assert_called_once_with(True)

    def test_opening_utf8_file_creates_an_editor_tab(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "programa.mini"
            path.write_text('print("árbol");', encoding="utf-8")
            instance = fake_editor(root)
            self.assertTrue(instance._open_editor_file(path))
        instance._create_editor_tab.assert_called_once_with(
            'print("árbol");', path=path.resolve()
        )
        self.assertEqual(instance.current_file, path.resolve())
        self.assertFalse(instance.dirty)
        instance.set_project_folder.assert_not_called()

    def test_first_opened_file_adopts_its_parent_as_project(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "programa.mini"
            path.write_text("print(1);", encoding="utf-8")
            instance = fake_editor(None)
            self.assertTrue(instance._open_editor_file(path))
        instance.set_project_folder.assert_called_once_with(path.resolve().parent)

    def test_non_utf8_file_does_not_replace_the_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binario.bin"
            path.write_bytes(b"\xff\xfe\x00")
            instance = fake_editor(Path(directory))
            with patch("app.messagebox.showerror") as showerror:
                self.assertFalse(instance._open_editor_file(path))
        instance._create_editor_tab.assert_not_called()
        instance._confirm_discard.assert_not_called()
        showerror.assert_called_once()

    def test_unsaved_changes_do_not_block_opening_another_tab(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "otro.mini"
            path.write_text("print(2);", encoding="utf-8")
            instance = fake_editor(Path(directory))
            previous_editor = instance.editor
            instance.dirty = True
            instance._confirm_discard.return_value = False
            self.assertTrue(instance._open_editor_file(path))
        self.assertIsNot(instance.editor, previous_editor)
        instance._create_editor_tab.assert_called_once()
        instance._confirm_discard.assert_not_called()

    def test_opening_the_same_path_selects_the_existing_tab(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "programa.mini"
            path.write_text("print(1);", encoding="utf-8")
            instance = fake_editor(Path(directory))
            self.assertTrue(instance._open_editor_file(path))
            document = instance.created_documents[0]
            instance._select_document = Mock()
            instance._create_editor_tab.reset_mock()
            self.assertTrue(instance._open_editor_file(path))
        instance._create_editor_tab.assert_not_called()
        instance._select_document.assert_called_once_with(document)

    def test_activation_opens_the_selected_file(self):
        instance = fake_explorer()
        path = Path("programa.mini")
        item = instance.explorer.insert("", "end", text=path.name)
        instance.explorer_paths[item] = path
        instance.explorer.focus(item)
        instance._open_editor_file = Mock(return_value=True)
        event = SimpleNamespace(y=10)
        self.assertEqual(instance._activate_explorer_item(event), "break")
        instance._open_editor_file.assert_called_once_with(path)

    def test_create_file_uses_the_selected_folder_and_opens_a_tab(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            instance = fake_explorer()
            instance.set_project_folder(root)
            focus_explorer_entry(instance, "src")
            instance._open_editor_file = Mock(return_value=True)
            with patch("app.simpledialog.askstring", return_value="nuevo.mini"):
                self.assertTrue(instance.create_explorer_file())
            created = root / "src" / "nuevo.mini"
            self.assertTrue(created.is_file())
            self.assertEqual(created.read_text(encoding="utf-8"), "")
            opened = instance._open_editor_file.call_args.args[0]
            self.assertEqual(opened.resolve(), created.resolve())

    def test_create_file_rejects_an_existing_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "programa.mini"
            path.write_text("original", encoding="utf-8")
            instance = fake_explorer()
            instance.set_project_folder(root)
            focus_explorer_entry(instance, root.name)
            with (
                patch("app.simpledialog.askstring", return_value=path.name),
                patch("app.messagebox.showerror") as showerror,
            ):
                self.assertFalse(instance.create_explorer_file())
            self.assertEqual(path.read_text(encoding="utf-8"), "original")
            showerror.assert_called_once()

    def test_rename_file_updates_an_open_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "antes.mini"
            source.write_text("print(1);", encoding="utf-8")
            instance = fake_explorer()
            instance.set_project_folder(root)
            focus_explorer_entry(instance, source.name)
            document = app.EditorDocument(Mock(), source.resolve(), False, "Sin título")
            instance.editor_tabs[str(document.editor)] = document
            instance._update_tab_label = Mock()
            instance._active_document = Mock(return_value=document)
            instance._set_active_document = Mock()
            with patch("app.simpledialog.askstring", return_value="despues.mini"):
                self.assertTrue(instance.rename_explorer_file())
            destination = root / "despues.mini"
            self.assertFalse(source.exists())
            self.assertTrue(destination.is_file())
            self.assertEqual(document.path, destination.resolve())
            instance._update_tab_label.assert_called_once_with(document)
            instance._set_active_document.assert_called_once_with(document)

    def test_remove_file_moves_it_to_the_recoverable_trash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "retirar.mini"
            source.write_text("recuperable", encoding="utf-8")
            trash = root / ".minilang-trash"
            trash.mkdir()
            previous = trash / source.name
            previous.write_text("anterior", encoding="utf-8")
            instance = fake_explorer()
            instance.set_project_folder(root)
            focus_explorer_entry(instance, source.name)
            with patch("app.messagebox.askyesno", return_value=True):
                self.assertTrue(instance.remove_explorer_file())
            recovered = trash / "retirar.1.mini"
            self.assertFalse(source.exists())
            self.assertEqual(recovered.read_text(encoding="utf-8"), "recuperable")
            self.assertEqual(previous.read_text(encoding="utf-8"), "anterior")
            names = [entry.name for entry in app.MainApp.project_entries(root)]
            self.assertNotIn(".minilang-trash", names)

    def test_remove_file_rejects_an_open_dirty_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cambios.mini"
            source.write_text("print(1);", encoding="utf-8")
            instance = fake_explorer()
            instance.set_project_folder(root)
            focus_explorer_entry(instance, source.name)
            document = app.EditorDocument(Mock(), source.resolve(), True, "Sin título")
            instance.editor_tabs[str(document.editor)] = document
            with (
                patch("app.messagebox.showwarning") as showwarning,
                patch("app.messagebox.askyesno") as askyesno,
            ):
                self.assertFalse(instance.remove_explorer_file())
            self.assertTrue(source.is_file())
            showwarning.assert_called_once()
            askyesno.assert_not_called()

    def test_file_operations_reject_folders_and_paths_outside_the_project(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            root = Path(directory)
            instance = fake_explorer()
            instance.set_project_folder(root)
            focus_explorer_entry(instance, root.name)
            with patch("app.messagebox.showwarning") as showwarning:
                self.assertFalse(instance.rename_explorer_file())
            showwarning.assert_called_once()

            outside = Path(other) / "fuera.mini"
            outside.write_text("print(9);", encoding="utf-8")
            item = instance.explorer.insert("", "end", text=outside.name)
            instance.explorer_paths[item] = outside
            instance.explorer.focus(item)
            with patch("app.messagebox.showwarning") as showwarning:
                self.assertFalse(instance.remove_explorer_file())
            self.assertTrue(outside.is_file())
            showwarning.assert_called_once()

    def test_windows_reserved_names_are_rejected(self):
        for name in (
            "CON", "nul.txt", "COM1.mini", "bad?.mini", "../fuera.mini",
            ".minilang-trash",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                app.MainApp._validate_explorer_leaf_name(name)


if __name__ == "__main__":
    unittest.main()
