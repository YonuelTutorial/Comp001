import tkinter as tk
from tkinter import ttk

# Compatibilidad
from minilang import *


DEMO_SOURCE = """// Ordenamiento burbuja
int lista[5];
lista[0] = 8;
lista[1] = 3;
lista[2] = 5;
lista[3] = 1;
lista[4] = 9;

int temp = 0;
bool orden = false;
int i = 0;

while (orden == false) {
    orden = true;
    i = 0;
    while (i < 4) {
        if (lista[i] > lista[i + 1]) {
            temp = lista[i];
            lista[i] = lista[i + 1];
            lista[i + 1] = temp;
            orden = false;
        }
        i = i + 1;
    }
}

print("Lista ordenada:");
i = 0;
while (i < 5) {
    print(lista[i]);
    i = i + 1;
}
"""


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini-Lang v4.0")
        self.root.geometry("850x760")
        self.setup_ui()

    def setup_ui(self):
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Código fuente:").pack(anchor=tk.W)
        self.txt_codigo = self._text_area(container, height=18)
        self.txt_codigo.insert(tk.END, DEMO_SOURCE)

        ttk.Button(container, text="Compilar y ejecutar", command=self.ejecutar_codigo).pack(pady=7)

        ttk.Label(container, text="Salida:").pack(anchor=tk.W)
        self.txt_consola = self._text_area(container, height=7)

        ttk.Label(container, text="Código destino:").pack(anchor=tk.W, pady=(7, 0))
        self.txt_asm = self._text_area(container, height=14)

    @staticmethod
    def _text_area(parent, height):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        text = tk.Text(frame, height=height, wrap=tk.NONE, font=("Consolas", 10))
        vertical = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        horizontal = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text.xview)
        text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        text.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return text

    def ejecutar_codigo(self):
        source = self.txt_codigo.get("1.0", tk.END).strip()
        self.txt_consola.delete("1.0", tk.END)
        self.txt_asm.delete("1.0", tk.END)
        self.root.update_idletasks()

        try:
            result = Compiler(max_steps=100_000, max_call_depth=500).compile_and_run(source)
            self.txt_consola.configure(fg="black")
            self.txt_consola.insert(tk.END, result.output)
            self.txt_asm.configure(fg="blue")
            self.txt_asm.insert(tk.END, result.assembly)
        except MiniLangError as error:
            self.txt_consola.configure(fg="red")
            self.txt_consola.insert(tk.END, str(error))
        except Exception as error:
            self.txt_consola.configure(fg="red")
            self.txt_consola.insert(tk.END, f"Error interno del compilador: {error}")


if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
