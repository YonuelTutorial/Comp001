import tkinter as tk
from tkinter import messagebox
import re

# --- Variables Globales ---
tokens = []
pos = 0
token_actual = None

# --- Analizador Lexico ---
def tokenizar(expresion):
    patron = re.compile(r'\s*(?:(\d+\.?\d*)|([+\-*/().]))\s*')
    return [match.group(1) or match.group(2) for match in patron.finditer(expresion)]

def advance():
    global pos, token_actual
    if pos < len(tokens):
        token_actual = tokens[pos]
        pos += 1
    else:
        token_actual = '\0'

def match(esperado):
    if token_actual == esperado:
        advance()
    else:
        raise ValueError(f"Se esperaba '{esperado}', se encontró '{token_actual}'")

# --- Reglas de Produccion y Evaluacion ---
def E():
    val = T()
    return E_prima(val)

def E_prima(heredado):
    if token_actual == '+':
        match('+')
        val = T()
        return E_prima(heredado + val)
    elif token_actual == '-':
        match('-')
        val = T()
        return E_prima(heredado - val)
    return heredado

def T():
    val = F()
    return T_prima(val)

def T_prima(heredado):
    if token_actual == '*':
        match('*')
        val = F()
        return T_prima(heredado * val)
    elif token_actual == '/':
        match('/')
        val = F()
        if val == 0:
            raise ValueError("Error Semántico: División por cero")
        return T_prima(heredado / val)
    return heredado

def F():
    if token_actual == '(':
        match('(')
        val = E()
        match(')')
        return val
    else:
        try:
            val = float(token_actual)
            advance()
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Sintaxis inválida cerca de: '{token_actual}'")

# --- Interfaz Grafica ---
def iniciar_analisis():
    global tokens, pos
    expr = entrada_texto.get()
    
    if not expr:
        messagebox.showwarning("Advertencia", "Ingrese una expresión.")
        return

    try:
        tokens = tokenizar(expr)
        pos = 0
        advance()
        
        resultado = E()
        
        if token_actual == '.':
            messagebox.showinfo("Éxito", f"Análisis correcto.\nResultado: {resultado}")
        else:
            raise ValueError(f"Falta fin de cadena (.), se encontró: '{token_actual}'")
            
    except Exception as error:
        messagebox.showerror("Error", str(error))

ventana = tk.Tk()
ventana.title("Analizador y Evaluador Sintáctico")
ventana.geometry("350x150")
ventana.resizable(False, False)

tk.Label(ventana, text="Expresión (ej. 10.5 * (2 + 3) .):").pack(pady=10)

entrada_texto = tk.Entry(ventana, width=40)
entrada_texto.pack(pady=5)

btn_analizar = tk.Button(ventana, text="Evaluar", command=iniciar_analisis, width=15)
btn_analizar.pack(pady=10)

ventana.mainloop()