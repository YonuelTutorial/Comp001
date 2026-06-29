import tkinter as tk
import re

# Analizador Semántico y Traductor
class CompiladorMini:
    def __init__(self):
        self.tabla_simbolos = {}
        self.errores = []
        self.codigo_js = []

    def compilar(self, codigo):
        self.tabla_simbolos.clear()
        self.errores.clear()
        self.codigo_js.clear()
        
        lineas = codigo.split('\n')
        
        for num, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if not linea: continue
            
            if linea.startswith('print(') and linea.endswith(');'):
                self.procesar_print(linea, num)
            elif linea.startswith(('int ', 'string ')):
                self.procesar_declaracion(linea, num)
            elif '=' in linea:
                self.procesar_asignacion(linea, num)
            else:
                self.errores.append(f"Línea {num}: Sintaxis no reconocida -> {linea}")

        if self.errores:
            return False, self.errores
        return True, '\n'.join(self.codigo_js)

    def procesar_print(self, linea, num):
        var = linea[6:-2].strip()
        if var.startswith('"') and var.endswith('"'):
            self.codigo_js.append(f"console.log({var});")
        elif var in self.tabla_simbolos:
            self.codigo_js.append(f"console.log({var});")
        else:
            self.errores.append(f"Línea {num}: Variable '{var}' no declarada.")

    def procesar_declaracion(self, linea, num):
        match = re.match(r'^(int|string)\s+([a-zA-Z_]\w*)\s*(?:=\s*(.+))?;$', linea)
        if not match:
            self.errores.append(f"Línea {num}: Error de sintaxis en declaración.")
            return

        tipo, var, valor = match.groups()

        if var in self.tabla_simbolos:
            self.errores.append(f"Línea {num}: Variable '{var}' ya declarada.")
            return

        self.tabla_simbolos[var] = tipo

        if valor:
            tipo_valor = self.obtener_tipo_valor(valor)
            if tipo_valor != 'desconocido' and tipo != tipo_valor:
                self.errores.append(f"Línea {num}: Tipo incompatible. Se esperaba {tipo}.")
            else:
                self.codigo_js.append(f"let {var} = {valor};")
        else:
            self.codigo_js.append(f"let {var};")

    def procesar_asignacion(self, linea, num):
        match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+);$', linea)
        if not match:
            self.errores.append(f"Línea {num}: Error de sintaxis en asignación.")
            return

        var, valor = match.groups()

        if var not in self.tabla_simbolos:
            self.errores.append(f"Línea {num}: Variable '{var}' no declarada.")
            return

        tipo_var = self.tabla_simbolos[var]
        tipo_valor = self.obtener_tipo_valor(valor)

        if tipo_valor == 'variable':
            if valor not in self.tabla_simbolos:
                self.errores.append(f"Línea {num}: Variable '{valor}' no declarada.")
                return
            tipo_valor = self.tabla_simbolos[valor]

        if tipo_var != tipo_valor and tipo_valor != 'desconocido':
            self.errores.append(f"Línea {num}: Incompatibilidad. No se puede asignar '{tipo_valor}' a '{var}' (tipo {tipo_var}).")
        else:
            self.codigo_js.append(f"{var} = {valor};")

    def obtener_tipo_valor(self, valor):
        if re.match(r'^\d+$', valor):
            return 'int'
        elif re.match(r'^".*"$', valor):
            return 'string'
        elif re.match(r'^[a-zA-Z_]\w*$', valor):
            return 'variable'
        return 'desconocido'

# Interfaz Gráfica
class VentanaCompilador:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador: Análisis Semántico + Traductor a JS")
        self.root.geometry("650x550")
        self.compilador = CompiladorMini()
        self.crear_widgets()

    def crear_widgets(self):
        tk.Label(self.root, text="Código Fuente (Mini-Lang):", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.txt_codigo = tk.Text(self.root, height=10, width=75, font=("Courier", 10))
        self.txt_codigo.pack()
        
        codigo_prueba = "int x = 10;\nstring msj = \"Hola Mundo\";\nprint(msj);\nx = 50;\nprint(x);"
        self.txt_codigo.insert(tk.END, codigo_prueba)

        tk.Button(self.root, text="Analizar y Traducir", command=self.ejecutar, bg="lightgray").pack(pady=10)

        tk.Label(self.root, text="Consola de Salida (Errores / Código JS):", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.txt_consola = tk.Text(self.root, height=12, width=75, font=("Courier", 10))
        self.txt_consola.pack()

    def ejecutar(self):
        codigo = self.txt_codigo.get("1.0", tk.END)
        exito, resultado = self.compilador.compilar(codigo)

        self.txt_consola.delete("1.0", tk.END)
        
        if exito:
            self.txt_consola.config(fg="blue")
            self.txt_consola.insert(tk.END, "// --- TRADUCCIÓN A JAVASCRIPT EXITOSA ---\n\n")
            self.txt_consola.insert(tk.END, resultado)
        else:
            self.txt_consola.config(fg="red")
            self.txt_consola.insert(tk.END, "// --- ERRORES SEMÁNTICOS / SINTÁCTICOS ---\n\n")
            for error in resultado:
                self.txt_consola.insert(tk.END, error + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaCompilador(root)
    root.mainloop()