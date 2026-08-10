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
    instance.set_explorer_visible = Mock()
    return instance


def fake_editor(project_dir):
    instance = object.__new__(app.MainApp)
    instance.root = None
    instance.project_dir = project_dir
    instance.current_file = None
    instance.dirty = False
    instance.editor = Mock()
    instance.status = Mock()
    instance.update_title = Mock()
    instance._confirm_discard = Mock(return_value=True)
    instance.set_project_folder = Mock()
    return instance


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

    def test_opening_utf8_file_updates_the_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "programa.mini"
            path.write_text('print("árbol");', encoding="utf-8")
            instance = fake_editor(root)
            self.assertTrue(instance._open_editor_file(path))
        instance.editor.set.assert_called_once_with('print("árbol");')
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
        instance.editor.set.assert_not_called()
        instance._confirm_discard.assert_not_called()
        showerror.assert_called_once()

    def test_unsaved_changes_can_cancel_opening_from_the_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "otro.mini"
            path.write_text("print(2);", encoding="utf-8")
            instance = fake_editor(Path(directory))
            instance._confirm_discard.return_value = False
            self.assertFalse(instance._open_editor_file(path))
        instance.editor.set.assert_not_called()
        self.assertIsNone(instance.current_file)

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


if __name__ == "__main__":
    unittest.main()
