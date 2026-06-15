import tkinter as tk
from tkinter import scrolledtext
import subprocess

# Ejecución del binario
def run_lexer():
    codigo = text_input.get("1.0", tk.END)
    
    result = subprocess.run(
        ["./lexer.exe"], 
        input=codigo, 
        capture_output=True, 
        text=True
    )
    
    text_output.delete("1.0", tk.END)
    text_output.insert(tk.END, result.stdout)

# Interfaz Gráfica
root = tk.Tk()
root.title("Analizador Léxico")

text_input = scrolledtext.ScrolledText(root, width=40, height=20)
text_input.pack(side=tk.LEFT, padx=10, pady=10)

text_output = scrolledtext.ScrolledText(root, width=40, height=20)
text_output.pack(side=tk.RIGHT, padx=10, pady=10)

btn_run = tk.Button(root, text="Analizar", command=run_lexer)
btn_run.pack(pady=20)

root.mainloop()