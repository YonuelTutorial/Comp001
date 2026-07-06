import tkinter as tk
import re

# ==========================================
# FASE 1: LÉXICO
# ==========================================
TOKEN_REGEX = [
    ('PRINT', r'print'),
    ('INT_T', r'int'),
    ('STR_T', r'string'),
    ('ID', r'[a-zA-Z_]\w*'),
    ('NUM', r'\d+'),
    ('STR_VAL', r'".*?"'),
    ('ASSIGN', r'='),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('SEMI', r';'),
    ('SKIP', r'[ \t\n]+'),
    ('MISMATCH', r'.')
]

class Lexer:
    def tokenize(self, code):
        tokens = []
        line_num = 1
        for mo in re.finditer('|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in TOKEN_REGEX), code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP':
                line_num += value.count('\n')
                continue
            elif kind == 'MISMATCH':
                raise Exception(f"Línea {line_num}: Error Léxico '{value}'")
            tokens.append((kind, value, line_num))
        return tokens

# ==========================================
# AST NODOS
# ==========================================
class VarDecl:
    def __init__(self, tipo, nombre, valor, linea):
        self.tipo = tipo
        self.nombre = nombre
        self.valor = valor
        self.linea = linea

class Assign:
    def __init__(self, nombre, valor, linea):
        self.nombre = nombre
        self.valor = valor
        self.linea = linea

class Print:
    def __init__(self, expr, linea):
        self.expr = expr
        self.linea = linea

# ==========================================
# FASE 2: SINTÁCTICO
# ==========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        ast = []
        while self.pos < len(self.tokens):
            ast.append(self.statement())
        return ast

    def match(self, expected_kind):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == expected_kind:
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        linea = self.tokens[self.pos][2] if self.pos < len(self.tokens) else 'EOF'
        raise Exception(f"Línea {linea}: Error Sintáctico. Se esperaba {expected_kind}.")

    def statement(self):
        kind = self.tokens[self.pos][0]
        if kind in ('INT_T', 'STR_T'):
            return self.var_decl()
        elif kind == 'ID':
            return self.assign()
        elif kind == 'PRINT':
            return self.print_stmt()
        else:
            raise Exception(f"Línea {self.tokens[self.pos][2]}: Instrucción no válida.")

    def var_decl(self):
        tipo = self.match(self.tokens[self.pos][0])[1]
        nombre = self.match('ID')[1]
        linea = self.tokens[self.pos-1][2]
        valor = None
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'ASSIGN':
            self.match('ASSIGN')
            val_token = self.tokens[self.pos]
            valor = (val_token[0], val_token[1])
            self.pos += 1
        self.match('SEMI')
        return VarDecl(tipo, nombre, valor, linea)

    def assign(self):
        nombre = self.match('ID')[1]
        linea = self.tokens[self.pos-1][2]
        self.match('ASSIGN')
        val_token = self.tokens[self.pos]
        valor = (val_token[0], val_token[1])
        self.pos += 1
        self.match('SEMI')
        return Assign(nombre, valor, linea)

    def print_stmt(self):
        self.match('PRINT')
        linea = self.tokens[self.pos-1][2]
        self.match('LPAREN')
        val_token = self.tokens[self.pos]
        expr = (val_token[0], val_token[1])
        self.pos += 1
        self.match('RPAREN')
        self.match('SEMI')
        return Print(expr, linea)

# ==========================================
# FASE 3: SEMÁNTICO
# ==========================================
class SemanticAnalyzer:
    def __init__(self):
        self.symtab = {}

    def analyze(self, ast):
        self.symtab.clear()
        for node in ast:
            if isinstance(node, VarDecl):
                if node.nombre in self.symtab:
                    raise Exception(f"Línea {node.linea}: Variable '{node.nombre}' ya declarada.")
                self.symtab[node.nombre] = node.tipo
                if node.valor:
                    self.check_type(node.nombre, node.valor, node.linea)
            elif isinstance(node, Assign):
                if node.nombre not in self.symtab:
                    raise Exception(f"Línea {node.linea}: Variable '{node.nombre}' no declarada.")
                self.check_type(node.nombre, node.valor, node.linea)
            elif isinstance(node, Print):
                if node.expr[0] == 'ID' and node.expr[1] not in self.symtab:
                    raise Exception(f"Línea {node.linea}: Variable '{node.expr[1]}' no declarada.")

    def check_type(self, var_name, valor, linea):
        esperado = self.symtab[var_name]
        tipo_val = valor[0]
        if tipo_val == 'ID':
            tipo_val = self.symtab[valor[1]]
            tipo_val = 'NUM' if tipo_val == 'int' else 'STR_VAL'
        if esperado == 'int' and tipo_val != 'NUM':
            raise Exception(f"Línea {linea}: Tipos incompatibles (int).")
        if esperado == 'string' and tipo_val != 'STR_VAL':
            raise Exception(f"Línea {linea}: Tipos incompatibles (string).")

# ==========================================
# FASE 4: OPTIMIZADOR (Propagación de Constantes)
# ==========================================
class Optimizer:
    def optimize(self, ast):
        constantes = {}
        for node in ast:
            if isinstance(node, VarDecl) and node.valor:
                if node.valor[0] in ('NUM', 'STR_VAL'):
                    constantes[node.nombre] = node.valor
                elif node.valor[0] == 'ID' and node.valor[1] in constantes:
                    node.valor = constantes[node.valor[1]]
                    constantes[node.nombre] = node.valor

            elif isinstance(node, Assign):
                if node.valor[0] in ('NUM', 'STR_VAL'):
                    constantes[node.nombre] = node.valor
                elif node.valor[0] == 'ID' and node.valor[1] in constantes:
                    node.valor = constantes[node.valor[1]]
                    constantes[node.nombre] = node.valor
                else:
                    if node.nombre in constantes:
                        del constantes[node.nombre]

            elif isinstance(node, Print):
                if node.expr[0] == 'ID' and node.expr[1] in constantes:
                    node.expr = constantes[node.expr[1]]
        return ast

# ==========================================
# FASE 5: GENERADOR JS
# ==========================================
class JSGenerator:
    def generate(self, ast):
        js_code = []
        for node in ast:
            if isinstance(node, VarDecl):
                if node.valor:
                    js_code.append(f"let {node.nombre} = {node.valor[1]};")
                else:
                    js_code.append(f"let {node.nombre};")
            elif isinstance(node, Assign):
                js_code.append(f"{node.nombre} = {node.valor[1]};")
            elif isinstance(node, Print):
                js_code.append(f"console.log({node.expr[1]});")
        return '\n'.join(js_code)

# ==========================================
# INTERFAZ GRÁFICA
# ==========================================
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador: Léxico -> Sintáctico -> Semántico -> Optimizador -> JS")
        self.root.geometry("650x550")
        
        self.lexer = Lexer()
        self.semantic = SemanticAnalyzer()
        self.optimizer = Optimizer()
        self.generator = JSGenerator()
        
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Código Fuente:", font=("Arial", 10, "bold")).pack(pady=5)
        self.txt_codigo = tk.Text(self.root, height=10, width=75, font=("Courier", 10))
        self.txt_codigo.pack()
        
        codigo_prueba = "int a = 100;\nint b = a;\nprint(b);\n\nstring c = \"Hola\";\nstring d = c;\nprint(d);"
        self.txt_codigo.insert(tk.END, codigo_prueba)

        tk.Button(self.root, text="Compilar y Optimizar", command=self.compilar_codigo, bg="lightgray").pack(pady=10)

        tk.Label(self.root, text="Consola (Salida JS Optimizada):", font=("Arial", 10, "bold")).pack(pady=5)
        self.txt_consola = tk.Text(self.root, height=12, width=75, font=("Courier", 10))
        self.txt_consola.pack()

    def compilar_codigo(self):
        codigo = self.txt_codigo.get("1.0", tk.END).strip()
        self.txt_consola.delete("1.0", tk.END)
        
        try:
            tokens = self.lexer.tokenize(codigo)
            parser = Parser(tokens)
            ast = parser.parse()
            self.semantic.analyze(ast)
            ast_optimizado = self.optimizer.optimize(ast)
            js_output = self.generator.generate(ast_optimizado)
            
            self.txt_consola.config(fg="blue")
            self.txt_consola.insert(tk.END, "// --- COMPILACIÓN Y OPTIMIZACIÓN EXITOSA ---\n")
            self.txt_consola.insert(tk.END, js_output)
            
        except Exception as e:
            self.txt_consola.config(fg="red")
            self.txt_consola.insert(tk.END, str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()