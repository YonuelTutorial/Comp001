import tkinter as tk
from tkinter import messagebox
import re

tokens = []
pos = 0
token_actual = None

# Analizador Lexico
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
        raise ValueError(f"Falta '{esperado}', se encontro '{token_actual}'")

# Analizador Sintactico y Semantico
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
            raise ValueError("Division por cero")
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
            raise ValueError(f"Sintaxis invalida en: '{token_actual}'")

# Interfaz Grafica
def iniciar_analisis():
    global tokens, pos
    expr = entrada_texto.get()
    
    if not expr:
        messagebox.showwarning("Advertencia", "Ingrese una expresion.")
        return

    try:
        tokens = tokenizar(expr)
        pos = 0
        advance()
        
        resultado = E()
        
        if token_actual in ('.', '\0'):
            messagebox.showinfo("Exito", f"Analisis correcto.\nResultado: {resultado}")
        else:
            raise ValueError(f"Simbolo no reconocido al final: '{token_actual}'")
            
    except Exception as error:
        messagebox.showerror("Error", str(error))

ventana = tk.Tk()
ventana.title("Analizador y Evaluador Sintactico")
ventana.geometry("350x150")
ventana.resizable(False, False)

tk.Label(ventana, text="Expresion:").pack(pady=10)

entrada_texto = tk.Entry(ventana, width=40)
entrada_texto.pack(pady=5)

btn_analizar = tk.Button(ventana, text="Evaluar", command=iniciar_analisis, width=15)
btn_analizar.pack(pady=10)

ventana.mainloop()