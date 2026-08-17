#INF-920-001 COMPILADORES
#Yonuel Peña 2190790

import json
import re
import stat
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from minilang import *


APP_VERSION = "4.5"
APP_AUTHOR = "Yonuel Peña"
APP_STUDENT_ID = "2190790"
APP_DATE = "17/08/2026"


DEMO_SOURCE = """"""


class CodeEditor(ttk.Frame):
    KEYWORDS = (
        "int", "float", "bool", "string", "void", "if", "else", "while", "for",
        "return", "break", "continue", "true", "false", "print", "import",
    )

    def __init__(self, parent, on_change, on_cursor):
        super().__init__(parent)
        self.on_change = on_change
        self.on_cursor = on_cursor
        self.font_size = 11
        self.gutter = tk.Text(
            self, width=5, padx=4, takefocus=False, border=0, state=tk.DISABLED,
            background="#20252b", foreground="#8b949e", font=("Consolas", self.font_size),
        )
        self.text = tk.Text(
            self, undo=True, wrap=tk.NONE, font=("Consolas", self.font_size),
            background="#0d1117", foreground="#e6edf3", insertbackground="white",
            selectbackground="#264f78",
        )
        self.scroll_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._scroll_y)
        self.scroll_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.scroll_y.grid(row=0, column=2, sticky="ns")
        self.scroll_x.grid(row=1, column=1, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.text.configure(yscrollcommand=self._text_scrolled, xscrollcommand=self.scroll_x.set)
        self.text.bind("<<Modified>>", self._modified)
        self.text.bind("<KeyRelease>", self._cursor)
        self.text.bind("<ButtonRelease-1>", self._cursor)
        self.text.bind("<MouseWheel>", lambda event: self.after_idle(self.refresh))
        self.text.tag_configure("keyword", foreground="#ff7b72")
        self.text.tag_configure("string", foreground="#a5d6ff")
        self.text.tag_configure("number", foreground="#79c0ff")
        self.text.tag_configure("comment", foreground="#8b949e")
        self.text.tag_configure("debug_line", background="#3d3a18")
        self.refresh()

    def get(self):
        return self.text.get("1.0", "end-1c")

    def set(self, value):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", value)
        self.text.edit_modified(False)
        self.refresh()

    def set_font_size(self, size):
        self.font_size = max(8, min(24, size))
        font = ("Consolas", self.font_size)
        self.text.configure(font=font)
        self.gutter.configure(font=font)
        self.refresh()

    def show_debug_line(self, line):
        self.text.tag_remove("debug_line", "1.0", tk.END)
        if line:
            start = f"{line}.0"
            end = f"{line}.end"
            self.text.tag_add("debug_line", start, end)
            self.text.see(start)

    def refresh(self):
        count = int(self.text.index("end-1c").split(".")[0])
        numbers = "\n".join(str(number) for number in range(1, count + 1))
        self.gutter.configure(state=tk.NORMAL)
        self.gutter.delete("1.0", tk.END)
        self.gutter.insert("1.0", numbers)
        self.gutter.configure(state=tk.DISABLED)
        self._highlight()

    def _highlight(self):
        source = self.get()
        for tag in ("keyword", "string", "number", "comment"):
            self.text.tag_remove(tag, "1.0", tk.END)
        patterns = [
            ("keyword", rf"\b(?:{'|'.join(self.KEYWORDS)})\b"),
            ("number", r"\b\d+(?:\.\d+)?\b"),
            ("string", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
            ("comment", r"//[^\n]*"),
        ]
        for tag, pattern in patterns:
            for match in re.finditer(pattern, source):
                self.text.tag_add(tag, f"1.0+{match.start()}c", f"1.0+{match.end()}c")

    def _modified(self, _event=None):
        if self.text.edit_modified():
            self.on_change()
            self.text.edit_modified(False)
            self.refresh()

    def _cursor(self, _event=None):
        line, column = self.text.index(tk.INSERT).split(".")
        self.on_cursor(int(line), int(column) + 1)

    def _scroll_y(self, *args):
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _text_scrolled(self, first, last):
        self.scroll_y.set(first, last)
        self.gutter.yview_moveto(first)


class MainApp:
    COMPILATION_WAIT_MS = 1_000
    EXPLORER_IGNORED = frozenset({".git", "__pycache__", ".pytest_cache"})
    PANEL_NAMES = (
        "Salida", "Errores", "Tokens", "AST", "Símbolos", "Pseudoensamblador",
        "JavaScript", "Depuración", "Entrada",
    )

    def __init__(self, root):
        self.root = root
        self.current_file = None
        self.project_dir = None
        self.dirty = False
        self.input_values = []
        self.last_result = None
        self.debugger = None
        self.compilation_dialog = None
        self.status = tk.StringVar(value="Línea 1, columna 1")
        self.project_name = tk.StringVar(value="Sin carpeta abierta")
        self.explorer_paths = {}
        self.explorer_loaded = set()
        self.explorer_visible = True
        self.root.geometry("1100x820")
        self.root.minsize(850, 650)
        icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "minilang.ico"
        if icon.is_file():
            self.root.iconbitmap(default=str(icon))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.setup_ui()
        self.editor.set(DEMO_SOURCE)
        self.update_title()

    def setup_ui(self):
        self._menu()
        toolbar = ttk.Frame(self.root, padding=(6, 4))
        toolbar.pack(fill=tk.X)
        for text, command in (
            ("Ejecutar F5", self.run_code),
            ("Compilar F7", lambda: self.show_compiling(self.build_code)),
            ("Depurar", self.start_debug),
            ("Paso", self.debug_step),
            ("Continuar", self.debug_continue),
            ("Punto", self.add_breakpoint),
            ("Copiar", self.copy_panel),
            ("Limpiar", self.clear_panel),
        ):
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=2)

        self.workspace = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.workspace.pack(fill=tk.BOTH, expand=True, padx=6)
        self.main_panes = ttk.PanedWindow(self.workspace, orient=tk.VERTICAL)
        self.workspace.add(self.main_panes, weight=4)
        self.editor = CodeEditor(self.main_panes, self.mark_dirty, self.update_cursor)
        self.main_panes.add(self.editor, weight=3)

        self.notebook = ttk.Notebook(self.main_panes)
        self.main_panes.add(self.notebook, weight=2)
        self.panels = {}
        self.panel_frames = {}
        for name in self.PANEL_NAMES:
            frame = ttk.Frame(self.notebook)
            text = self._text_area(frame)
            self.notebook.add(frame, text=name)
            self.panels[name] = text
            self.panel_frames[name] = frame
        self.panels["Entrada"].insert("1.0", "")
        self._setup_explorer()
        self.workspace.add(self.explorer_frame, weight=1)
        ttk.Label(self.root, textvariable=self.status, anchor=tk.W).pack(fill=tk.X, padx=8, pady=3)

    def _menu(self):
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Nuevo", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Abrir", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Abrir carpeta...", command=self.open_folder)
        file_menu.add_command(label="Guardar", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Guardar como", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.close)
        menu.add_cascade(label="Archivo", menu=file_menu)

        compile_menu = tk.Menu(menu, tearoff=False)
        compile_menu.add_command(
            label="Compilar", accelerator="F7",
            command=lambda: self.show_compiling(self.build_code),
        )
        compile_menu.add_separator()
        compile_menu.add_command(
            label="Compilar a pseudoensamblador...",
            command=lambda: self.show_compiling(self.compile_assembly),
        )
        compile_menu.add_command(
            label="Compilar a JavaScript...",
            command=lambda: self.show_compiling(self.compile_javascript),
        )
        compile_menu.add_command(
            label="Compilar juego web (.html)...",
            command=lambda: self.show_compiling(self.compile_web_game),
        )
        menu.add_cascade(label="Compilar", menu=compile_menu)

        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Buscar", accelerator="Ctrl+F", command=self.find_text)
        edit_menu.add_command(label="Reemplazar", accelerator="Ctrl+H", command=self.replace_text)
        edit_menu.add_separator()
        edit_menu.add_command(label="Aumentar fuente", accelerator="Ctrl++", command=self.increase_font)
        edit_menu.add_command(label="Reducir fuente", accelerator="Ctrl+-", command=self.decrease_font)
        menu.add_cascade(label="Editar", menu=edit_menu)

        view_menu = tk.Menu(menu, tearoff=False)
        view_menu.add_command(label="Mostrar/Ocultar explorador", command=self.toggle_explorer)
        menu.add_cascade(label="Ver", menu=view_menu)
        self.root.configure(menu=menu)
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda event: self.save_as())
        self.root.bind("<Control-f>", lambda event: self.find_text())
        self.root.bind("<Control-h>", lambda event: self.replace_text())
        self.root.bind("<Control-plus>", lambda event: self.increase_font())
        self.root.bind("<Control-minus>", lambda event: self.decrease_font())
        self.root.bind("<F5>", lambda event: self.run_code())
        self.root.bind("<F7>", lambda event: self.show_compiling(self.build_code))

    def show_compiling(self, action):
        active = self.compilation_dialog
        if active is not None:
            try:
                if active.winfo_exists():
                    active.lift()
                    active.focus_force()
                    return False
            except tk.TclError:
                pass
            self.compilation_dialog = None

        dialog = tk.Toplevel(self.root)
        self.compilation_dialog = dialog
        dialog.title("Compilando")
        dialog.geometry("320x105")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        content = ttk.Frame(dialog, padding=18)
        content.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            content, text="Compilando...", font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 14))
        progress = ttk.Progressbar(content, mode="indeterminate", length=270)
        progress.pack(fill=tk.X)
        progress.start(12)

        dialog.grab_set()
        dialog.focus_set()
        self.root.after(
            self.COMPILATION_WAIT_MS,
            lambda: self._finish_compiling(dialog, progress, action),
        )
        return True

    def _finish_compiling(self, dialog, progress, action):
        if self.compilation_dialog is not dialog:
            return
        try:
            progress.stop()
            if dialog.winfo_exists():
                dialog.grab_release()
                dialog.destroy()
        except tk.TclError:
            pass
        finally:
            self.compilation_dialog = None
        try:
            self.root.after_idle(action)
        except tk.TclError:
            return

    @staticmethod
    def _text_area(parent):
        text = tk.Text(parent, wrap=tk.NONE, font=("Consolas", 10))
        vertical = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text.yview)
        horizontal = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=text.xview)
        text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        text.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        return text

    def _setup_explorer(self):
        self.explorer_frame = ttk.Frame(self.workspace, padding=(6, 4))
        header = ttk.Frame(self.explorer_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(header, text="EXPLORADOR").pack(side=tk.LEFT)
        ttk.Button(header, text="Carpeta...", command=self.open_folder).pack(side=tk.RIGHT, padx=2)
        ttk.Button(header, text="Ocultar", command=self.toggle_explorer).pack(side=tk.RIGHT)
        ttk.Label(
            self.explorer_frame, textvariable=self.project_name, anchor=tk.W
        ).grid(row=1, column=0, sticky="ew", pady=(0, 4))

        tree_frame = ttk.Frame(self.explorer_frame)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        self.explorer = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self.explorer.column("#0", width=240, minwidth=160, stretch=True)
        vertical = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.explorer.yview)
        horizontal = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.explorer.xview)
        self.explorer.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.explorer.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.explorer_frame.rowconfigure(2, weight=1)
        self.explorer_frame.columnconfigure(0, weight=1)
        self.explorer.bind("<<TreeviewOpen>>", self._on_explorer_open)
        self.explorer.bind("<Double-1>", self._activate_explorer_item)
        self.explorer.bind("<Return>", self._activate_explorer_item)
        self.explorer.insert("", tk.END, text="Abre una carpeta para explorar", tags=("placeholder",))

    def open_folder(self):
        initial = self.project_dir or (self.current_file.parent if self.current_file else Path.cwd())
        path = filedialog.askdirectory(parent=self.root, initialdir=str(initial), mustexist=True)
        if not path:
            return False
        try:
            self.set_project_folder(path)
            return True
        except OSError as error:
            messagebox.showerror("Abrir carpeta", str(error), parent=self.root)
            return False

    def set_project_folder(self, path):
        folder = Path(path).resolve()
        if not folder.is_dir():
            raise OSError(f"La carpeta no existe: {folder}")
        self.project_dir = folder
        self.project_name.set(folder.name or str(folder))
        self.refresh_explorer()
        self.set_explorer_visible(True)
        self.status.set(f"Proyecto abierto: {folder}")

    def refresh_explorer(self):
        self.explorer.delete(*self.explorer.get_children(""))
        self.explorer_paths.clear()
        self.explorer_loaded.clear()
        if self.project_dir is None:
            self.explorer.insert(
                "", tk.END, text="Abre una carpeta para explorar", tags=("placeholder",)
            )
            return
        root_item = self.explorer.insert(
            "", tk.END, text=self.project_dir.name or str(self.project_dir), open=True
        )
        self.explorer_paths[root_item] = self.project_dir
        self._load_explorer_node(root_item)

    @classmethod
    def project_entries(cls, folder):
        entries = []
        for entry in Path(folder).iterdir():
            if entry.name in cls.EXPLORER_IGNORED or cls._is_reparse_point(entry):
                continue
            try:
                directory = entry.is_dir()
            except OSError:
                directory = False
            entries.append((directory, entry))
        entries.sort(key=lambda item: (not item[0], item[1].name.casefold(), item[1].name))
        return [entry for _directory, entry in entries]

    @staticmethod
    def _is_reparse_point(path):
        try:
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
            flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            return path.is_symlink() or bool(attributes & flag)
        except OSError:
            return True

    def _load_explorer_node(self, item):
        if item in self.explorer_loaded:
            return
        folder = self.explorer_paths.get(item)
        if folder is None or not folder.is_dir():
            return
        for child in self.explorer.get_children(item):
            self.explorer.delete(child)
        try:
            entries = self.project_entries(folder)
        except OSError as error:
            self.explorer.insert(item, tk.END, text="[No se pudo leer la carpeta]")
            self.status.set(f"No se pudo explorar {folder}: {error}")
            self.explorer_loaded.add(item)
            return
        for entry in entries:
            child = self.explorer.insert(item, tk.END, text=entry.name)
            self.explorer_paths[child] = entry
            try:
                directory = entry.is_dir()
            except OSError:
                directory = False
            if directory:
                self.explorer.insert(child, tk.END, text="")
        self.explorer_loaded.add(item)

    def _on_explorer_open(self, _event=None):
        item = self.explorer.focus()
        if item:
            self.root.after_idle(lambda selected=item: self._load_explorer_node(selected))

    def _activate_explorer_item(self, event: tk.Event | None = None):
        item = ""
        if event is not None and getattr(event, "num", None) == 1:
            item = self.explorer.identify_row(event.y)
        item = item or self.explorer.focus()
        path = self.explorer_paths.get(item)
        if path is None:
            return "break"
        self.explorer.selection_set(item)
        self.explorer.focus(item)
        if path.is_dir():
            opened = not bool(self.explorer.item(item, "open"))
            self.explorer.item(item, open=opened)
            if opened:
                self._load_explorer_node(item)
            return "break"
        self._open_editor_file(path)
        return "break"

    def toggle_explorer(self):
        self.set_explorer_visible(not self.explorer_visible)

    def set_explorer_visible(self, visible):
        pane_names = {str(pane) for pane in self.workspace.panes()}
        present = str(self.explorer_frame) in pane_names
        if visible and not present:
            self.workspace.add(self.explorer_frame, weight=1)
        elif not visible and present:
            self.workspace.forget(self.explorer_frame)
        self.explorer_visible = visible

    def run_code(self):
        self._prepare_inputs()
        try:
            compiler = Compiler(max_steps=1_000_000, max_call_depth=500, input_provider=self._provide_input)
            self.last_result = compiler.compile_and_run(self.editor.get(), self.current_file)
            self._show_result(self.last_result)
            self._set_panel("Errores", "")
            self.notebook.select(self.panels["Salida"].master)
            self.status.set("Ejecución completada")
            return True
        except Exception as error:
            self._show_error(error)
            self.status.set("Ejecución fallida")
            return False

    def build_code(self):
        try:
            self.last_result = Compiler(
                max_steps=1_000_000, max_call_depth=500
            ).compile(self.editor.get(), self.current_file)
            self._show_result(self.last_result)
            self._set_panel("Errores", "")
            self.notebook.select(self.panels["Pseudoensamblador"].master)
            self.status.set("Compilación completada")
            return True
        except Exception as error:
            self._show_error(error)
            self.status.set("Compilación fallida")
            return False

    def compile_assembly(self):
        return self._export_compilation(
            label="Pseudoensamblador",
            attribute="assembly",
            extension=".asm",
            filetypes=(
                ("Pseudoensamblador", "*.asm"),
                ("Texto", "*.txt"),
                ("Binario simulado", "*.bin"),
                ("Todos", "*.*"),
            ),
        )

    def compile_javascript(self):
        return self._export_compilation(
            label="JavaScript",
            attribute="javascript",
            extension=".js",
            filetypes=(("JavaScript", "*.js"), ("Texto", "*.txt"), ("Todos", "*.*")),
        )

    def compile_web_game(self):
        return self._export_compilation(
            label="Juego web",
            attribute="game_html",
            extension=".html",
            filetypes=(("Página web", "*.html"), ("Todos", "*.*")),
            compiler_method="compile_game",
        )

    def _export_compilation(
        self, label, attribute, extension, filetypes, compiler_method="compile"
    ):
        try:
            compiler = Compiler(max_steps=1_000_000, max_call_depth=500)
            result = getattr(compiler, compiler_method)(self.editor.get(), self.current_file)
            source_name = Path(self.current_file).stem if self.current_file else "programa"
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title=f"Compilar a {label}",
                defaultextension=extension,
                initialfile=f"{source_name}{extension}",
                filetypes=filetypes,
            )
            if not path:
                return False
            Path(path).write_text(getattr(result, attribute), encoding="utf-8")
            self.last_result = result
            self._show_result(result)
            self._set_panel("Errores", "")
            self.status.set(f"Compilado a {label}: {path}")
            return True
        except Exception as error:
            self._show_error(error)
            return False

    def start_debug(self):
        self._prepare_inputs()
        try:
            compiler = Compiler(max_steps=1_000_000, max_call_depth=500, input_provider=self._provide_input)
            self.last_result = compiler.compile(self.editor.get(), self.current_file)
            self.debugger = Debugger(
                self.last_result.bytecode, 1_000_000, 500, self._provide_input
            )
            self._show_result(self.last_result)
            self._show_debug(self.debugger.snapshot())
        except Exception as error:
            self._show_error(error)

    def debug_step(self):
        if self.debugger is None:
            self.start_debug()
            return
        try:
            self.debugger.step()
            self._show_debug(self.debugger.snapshot())
        except Exception as error:
            self._show_error(error)

    def debug_continue(self):
        if self.debugger is None:
            self.start_debug()
            return
        try:
            self._show_debug(self.debugger.continue_run())
        except Exception as error:
            self._show_error(error)

    def add_breakpoint(self):
        if self.debugger is None:
            self.start_debug()
        if self.debugger is None:
            return
        line = simpledialog.askinteger("Punto de interrupción", "Número de línea:", parent=self.root)
        if line:
            self.debugger.add_breakpoint(line)
            self.status.set(f"Punto de interrupción en línea {line}")

    def _show_result(self, result):
        self._set_panel("Salida", result.output)
        token_text = "\n".join(
            f"{token.line}:{token.column}  {token.kind:<14} {token.value!r}" for token in result.tokens
        )
        self._set_panel("Tokens", token_text)
        self._set_panel("AST", format_ast(result.ast))
        self._set_panel("Símbolos", json.dumps(result.symbols, ensure_ascii=False, indent=2))
        bytecode = (
            "ANTES DE OPTIMIZAR\n\n"
            + result.unoptimized_assembly
            + "\n\nDESPUÉS DE OPTIMIZAR\n\n"
            + result.assembly
        )
        self._set_panel("Pseudoensamblador", bytecode)
        self._set_panel("JavaScript", result.javascript)

    def _show_debug(self, state):
        self._set_panel("Salida", "\n".join(state["output"]))
        self._set_panel("Depuración", json.dumps(state, ensure_ascii=False, indent=2, default=str))
        self.editor.show_debug_line(state.get("line"))
        self.notebook.select(self.panels["Depuración"].master)

    def _show_error(self, error):
        text = str(error) if isinstance(error, MiniLangError) else f"Error interno: {error}"
        self._set_panel("Errores", text)
        self.notebook.select(self.panels["Errores"].master)

    def _set_panel(self, name, value):
        panel = self.panels[name]
        panel.delete("1.0", tk.END)
        panel.insert("1.0", value)

    def current_panel(self):
        selected = self.notebook.select()
        for name, frame in self.panel_frames.items():
            if str(frame) == selected:
                return name, self.panels[name]
        return None, None

    def copy_panel(self):
        _, panel = self.current_panel()
        if panel is not None:
            self.root.clipboard_clear()
            self.root.clipboard_append(panel.get("1.0", "end-1c"))

    def clear_panel(self):
        name, panel = self.current_panel()
        if panel is not None and name != "Entrada":
            panel.delete("1.0", tk.END)

    def _prepare_inputs(self):
        self.input_values = self.panels["Entrada"].get("1.0", "end-1c").splitlines()

    def _provide_input(self, prompt):
        if not self.input_values:
            raise MiniLangRuntimeError(f"faltan datos de entrada para {prompt.strip()}")
        return self.input_values.pop(0)

    def new_file(self):
        if not self._confirm_discard():
            return
        self.current_file = None
        self.editor.set("")
        self.dirty = False
        self.update_title()

    def open_file(self):
        path = filedialog.askopenfilename(
            parent=self.root, filetypes=(("Mini-Lang", "*.mini *.txt"), ("Todos", "*.*"))
        )
        if not path:
            return False
        return self._open_editor_file(path)

    def _open_editor_file(self, path):
        path = Path(path).resolve()
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeError:
            messagebox.showerror(
                "Abrir", f"El archivo no contiene texto UTF-8: {path}", parent=self.root
            )
            return False
        except OSError as error:
            messagebox.showerror("Abrir", str(error), parent=self.root)
            return False
        if not self._confirm_discard():
            return False
        self.editor.set(source)
        self.current_file = path
        self.dirty = False
        self.update_title()
        if self.project_dir is None:
            self.set_project_folder(path.parent)
        self.status.set(f"Archivo abierto: {path}")
        return True

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        try:
            self.current_file.write_text(self.editor.get(), encoding="utf-8")
            self.dirty = False
            self.update_title()
            return True
        except OSError as error:
            messagebox.showerror("Guardar", str(error), parent=self.root)
            return False

    def save_as(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".mini",
            filetypes=(("Mini-Lang", "*.mini"), ("Texto", "*.txt"), ("Todos", "*.*")),
        )
        if not path:
            return False
        self.current_file = Path(path)
        saved = self.save_file()
        if saved:
            if self.project_dir is None:
                self.set_project_folder(self.current_file.parent)
            elif self._path_in_project(self.current_file):
                self.refresh_explorer()
        return saved

    def _path_in_project(self, path):
        if self.project_dir is None:
            return False
        try:
            Path(path).resolve().relative_to(self.project_dir)
            return True
        except ValueError:
            return False

    def find_text(self):
        query = simpledialog.askstring("Buscar", "Texto:", parent=self.root)
        if not query:
            return
        start = self.editor.text.index(tk.INSERT)
        found = self.editor.text.search(query, start, stopindex=tk.END, nocase=False)
        if not found:
            found = self.editor.text.search(query, "1.0", stopindex=start, nocase=False)
        if found:
            end = f"{found}+{len(query)}c"
            self.editor.text.tag_remove(tk.SEL, "1.0", tk.END)
            self.editor.text.tag_add(tk.SEL, found, end)
            self.editor.text.mark_set(tk.INSERT, end)
            self.editor.text.see(found)

    def replace_text(self):
        query = simpledialog.askstring("Reemplazar", "Buscar:", parent=self.root)
        if query is None:
            return
        replacement = simpledialog.askstring("Reemplazar", "Reemplazar con:", parent=self.root)
        if replacement is None:
            return
        self.editor.set(self.editor.get().replace(query, replacement))
        self.mark_dirty()

    def increase_font(self):
        self.editor.set_font_size(self.editor.font_size + 1)

    def decrease_font(self):
        self.editor.set_font_size(self.editor.font_size - 1)

    def mark_dirty(self):
        self.dirty = True
        self.update_title()

    def update_cursor(self, line, column):
        self.status.set(f"Línea {line}, columna {column}")

    def update_title(self):
        name = self.current_file.name if self.current_file else "Sin título"
        marker = "*" if self.dirty else ""
        self.root.title(
            f"{marker}{name} — Mini-Lang v{APP_VERSION} — "
            f"{APP_AUTHOR} — {APP_STUDENT_ID} — {APP_DATE}"
        )

    def _confirm_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Cambios", "¿Guardar los cambios?", parent=self.root)
        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def close(self):
        if self._confirm_discard():
            self.root.destroy()


def run_self_test():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    source = (base / "test_advanced.txt").read_text(encoding="utf-8")
    result = Compiler(max_steps=1_000_000).compile_and_run(source)
    return 0 if result.output.splitlines()[-1] == "8" else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(run_self_test())
    else:
        root = tk.Tk()
        MainApp(root)
        root.mainloop()
