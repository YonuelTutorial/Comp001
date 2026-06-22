import tkinter as tk
import re

# Análisis Semántico
class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = {}
        self.errores = []

    def analizar(self, codigo):
        self.tabla_simbolos.clear()
        self.errores.clear()
        lineas = codigo.split('\n')

        for num, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if not linea: continue

            if linea.startswith(('int ', 'string ')):
                self.procesar_declaracion(linea, num)
            elif '=' in linea:
                self.procesar_asignacion(linea, num)
            else:
                self.errores.append(f"Línea {num}: Sintaxis no soportada -> {linea}")

        return self.errores

    def procesar_declaracion(self, linea, num):
        partes = linea.replace(';', '').split()
        if len(partes) >= 2:
            tipo, var = partes[0], partes[1]
            if var in self.tabla_simbolos:
                self.errores.append(f"Línea {num}: Variable '{var}' ya declarada.")
            else:
                self.tabla_simbolos[var] = tipo

    def procesar_asignacion(self, linea, num):
        partes = linea.replace(';', '').split('=')
        if len(partes) == 2:
            var = partes[0].strip()
            valor = partes[1].strip()

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

    def obtener_tipo_valor(self, valor):
        if re.match(r'^\d+$', valor):
            return 'int'
        elif re.match(r'^".*"$', valor):
            return 'string'
        elif re.match(r'^[a-zA-Z_]\w*$', valor):
            return 'variable'
        return 'desconocido'


# Interfaz Gráfica
class Ventana:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Semántico")
        self.root.geometry("600x450")
        self.analizador = AnalizadorSemantico()
        self.crear_widgets()

    def crear_widgets(self):
        tk.Label(self.root, text="Código Fuente:", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.txt_codigo = tk.Text(self.root, height=12, width=70, font=("Courier", 10))
        self.txt_codigo.pack()
        
        codigo_prueba = "int x;\nx = 10;\nstring msj;\nmsj = 5;\ny = 20;"
        self.txt_codigo.insert(tk.END, codigo_prueba)

        tk.Button(self.root, text="Ejecutar Análisis", command=self.ejecutar_analisis, bg="lightgray").pack(pady=10)

        tk.Label(self.root, text="Consola de Salida:", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.txt_consola = tk.Text(self.root, height=8, width=70, fg="red", font=("Courier", 10))
        self.txt_consola.pack()

    def ejecutar_analisis(self):
        codigo = self.txt_codigo.get("1.0", tk.END)
        errores = self.analizador.analizar(codigo)

        self.txt_consola.delete("1.0", tk.END)
        
        if errores:
            self.txt_consola.config(fg="red")
            for error in errores:
                self.txt_consola.insert(tk.END, error + "\n")
        else:
            self.txt_consola.config(fg="green")
            self.txt_consola.insert(tk.END, "Compilación exitosa: 0 errores semánticos.")

if __name__ == "__main__":
    root = tk.Tk()
    app = Ventana(root)
    root.mainloop()