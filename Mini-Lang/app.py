import tkinter as tk
import re

# ==========================================
# LÉXICO
# ==========================================
TOKEN_REGEX = [
    ('PRINT', r'print'),
    ('INT_T', r'int'),
    ('BOOL_T', r'bool'),
    ('IF', r'if'),
    ('WHILE', r'while'),
    ('RETURN', r'return'),
    ('TRUE', r'true'),
    ('FALSE', r'false'),
    ('EQ', r'=='),
    ('ASSIGN', r'='),
    ('LT', r'<'),
    ('GT', r'>'),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('STAR', r'\*'),
    ('COMMENT', r'//.*'),
    ('SLASH', r'/'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('COMMA', r','),
    ('SEMI', r';'),
    ('ID', r'[a-zA-Z_]\w*'),
    ('NUM', r'\d+'),
    ('SKIP', r'[ \t\n]+'),
    ('MISMATCH', r'.')
]

class Lexer:
    def tokenize(self, code):
        tokens = []
        for mo in re.finditer('|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in TOKEN_REGEX), code):
            kind = mo.lastgroup
            value = mo.group()
            if kind in ('SKIP', 'COMMENT'):
                continue
            elif kind == 'MISMATCH':
                raise Exception(f"Token no reconocido: {value}")
            tokens.append((kind, value))
        return tokens

# ==========================================
# AST
# ==========================================
class FuncDecl:
    def __init__(self, tipo, nombre, param_tipo, param_nombre, body):
        self.tipo = tipo
        self.nombre = nombre
        self.param_tipo = param_tipo
        self.param_nombre = param_nombre
        self.body = body

class VarDecl:
    def __init__(self, tipo, nombre, valor):
        self.tipo = tipo
        self.nombre = nombre
        self.valor = valor

class ArrayDecl:
    def __init__(self, tipo, nombre, size):
        self.tipo = tipo
        self.nombre = nombre
        self.size = size

class Assign:
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor

class ArrayAssign:
    def __init__(self, nombre, index, valor):
        self.nombre = nombre
        self.index = index
        self.valor = valor

class IfStmt:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class WhileStmt:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class ReturnStmt:
    def __init__(self, expr):
        self.expr = expr

class Print:
    def __init__(self, expr):
        self.expr = expr

class CallExpr:
    def __init__(self, nombre, arg):
        self.nombre = nombre
        self.arg = arg

class BinOp:
    def __init__(self, izq, op, der):
        self.izq = izq
        self.op = op
        self.der = der

class Literal:
    def __init__(self, val, tipo):
        self.val = val
        self.tipo = tipo

class VarAccess:
    def __init__(self, nombre):
        self.nombre = nombre

class ArrayAccess:
    def __init__(self, nombre, index):
        self.nombre = nombre
        self.index = index

# ==========================================
# SINTÁCTICO
# ==========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def match(self, expected):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == expected:
            tok = self.tokens[self.pos]
            self.pos += 1
            return tok
        raise Exception(f"Error sintáctico, se esperaba: {expected}")

    def parse(self):
        ast = []
        while self.pos < len(self.tokens):
            ast.append(self.declaration())
        return ast

    def declaration(self):
        if self.tokens[self.pos][0] in ('INT_T', 'BOOL_T'):
            tipo = self.match(self.tokens[self.pos][0])[1]
            nombre = self.match('ID')[1]
            
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'LPAREN':
                self.match('LPAREN')
                if self.tokens[self.pos][0] not in ('INT_T', 'BOOL_T'):
                    raise Exception("Error sintáctico, se esperaba un tipo de parámetro")
                param_tipo = self.match(self.tokens[self.pos][0])[1]
                param_nombre = self.match('ID')[1]
                self.match('RPAREN')
                body = self.block()
                return FuncDecl(tipo, nombre, param_tipo, param_nombre, body)
            elif self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'LBRACKET':
                self.match('LBRACKET')
                size = int(self.match('NUM')[1])
                self.match('RBRACKET')
                self.match('SEMI')
                return ArrayDecl(tipo, nombre, size)
            else:
                self.match('ASSIGN')
                valor = self.expression()
                self.match('SEMI')
                return VarDecl(tipo, nombre, valor)
        return self.statement()

    def statement(self):
        tok = self.tokens[self.pos][0]
        if tok == 'PRINT':
            self.match('PRINT')
            self.match('LPAREN')
            expr = self.expression()
            self.match('RPAREN')
            self.match('SEMI')
            return Print(expr)
        elif tok == 'IF':
            self.match('IF')
            self.match('LPAREN')
            cond = self.expression()
            self.match('RPAREN')
            body = self.block()
            return IfStmt(cond, body)
        elif tok == 'WHILE':
            self.match('WHILE')
            self.match('LPAREN')
            cond = self.expression()
            self.match('RPAREN')
            body = self.block()
            return WhileStmt(cond, body)
        elif tok == 'RETURN':
            self.match('RETURN')
            expr = self.expression()
            self.match('SEMI')
            return ReturnStmt(expr)
        elif tok == 'ID':
            nombre = self.match('ID')[1]
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'LBRACKET':
                self.match('LBRACKET')
                index = self.expression()
                self.match('RBRACKET')
                self.match('ASSIGN')
                valor = self.expression()
                self.match('SEMI')
                return ArrayAssign(nombre, index, valor)
            else:
                self.match('ASSIGN')
                valor = self.expression()
                self.match('SEMI')
                return Assign(nombre, valor)
        raise Exception("Sintaxis inválida")

    def block(self):
        self.match('LBRACE')
        stmts = []
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] != 'RBRACE':
            stmts.append(self.declaration())
        if self.pos >= len(self.tokens):
            raise Exception("Error sintáctico: falta '}'")
        self.match('RBRACE')
        return stmts

    def expression(self):
        return self.relational()

    def relational(self):
        izq = self.term()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] in ('EQ', 'LT', 'GT'):
            op = self.match(self.tokens[self.pos][0])[1]
            der = self.term()
            izq = BinOp(izq, op, der)
        return izq

    def term(self):
        izq = self.factor()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] in ('PLUS', 'MINUS'):
            op = self.match(self.tokens[self.pos][0])[1]
            der = self.factor()
            izq = BinOp(izq, op, der)
        return izq

    def factor(self):
        izq = self.primary()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] in ('STAR', 'SLASH'):
            op = self.match(self.tokens[self.pos][0])[1]
            der = self.primary()
            izq = BinOp(izq, op, der)
        return izq

    def primary(self):
        tok = self.tokens[self.pos]
        if tok[0] == 'NUM':
            self.match('NUM')
            return Literal(int(tok[1]), 'int')
        elif tok[0] == 'TRUE':
            self.match('TRUE')
            return Literal(True, 'bool')
        elif tok[0] == 'FALSE':
            self.match('FALSE')
            return Literal(False, 'bool')
        elif tok[0] == 'ID':
            nombre = self.match('ID')[1]
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'LPAREN':
                self.match('LPAREN')
                arg = self.expression()
                self.match('RPAREN')
                return CallExpr(nombre, arg)
            elif self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'LBRACKET':
                self.match('LBRACKET')
                index = self.expression()
                self.match('RBRACKET')
                return ArrayAccess(nombre, index)
            return VarAccess(nombre)
        elif tok[0] == 'LPAREN':
            self.match('LPAREN')
            expr = self.expression()
            self.match('RPAREN')
            return expr
        raise Exception("Expresión esperada")

# ==========================================
# SEMÁNTICO
# ==========================================
class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def declare(self, name, tipo):
        if name in self.vars:
            raise Exception(f"'{name}' ya declarada")
        self.vars[name] = tipo

    def get_type(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get_type(name)
        raise Exception(f"'{name}' no declarada")

class SemanticAnalyzer:
    def __init__(self):
        self.funcs = {}
        self.current_return_type = None

    def analyze(self, ast):
        self.env = Environment()
        self.funcs.clear()
        self.current_return_type = None
        for node in ast:
            self.visit(node)

    def type_of(self, node):
        if isinstance(node, Literal):
            return node.tipo
        if isinstance(node, VarAccess):
            return self.env.get_type(node.nombre)
        if isinstance(node, ArrayAccess):
            t_var = self.env.get_type(node.nombre)
            t_idx = self.type_of(node.index)
            if t_idx != 'int':
                raise Exception("Indice requiere int")
            if not t_var.endswith('_array'):
                raise Exception(f"'{node.nombre}' no es un arreglo")
            return t_var.replace('_array', '')
        if isinstance(node, BinOp):
            t_izq = self.type_of(node.izq)
            t_der = self.type_of(node.der)
            if node.op in ('+', '-', '*', '/'):
                if t_izq != 'int' or t_der != 'int':
                    raise Exception("Operación aritmética requiere enteros")
                return 'int'
            if node.op in ('<', '>'):
                if t_izq != 'int' or t_der != 'int':
                    raise Exception("Comparación relacional requiere enteros")
                return 'bool'
            if node.op == '==':
                if t_izq != t_der:
                    raise Exception("Comparación de igualdad entre tipos incompatibles")
                return 'bool'
        if isinstance(node, CallExpr):
            return self.visit(node)
        raise Exception(f"No se puede inferir el tipo de {type(node).__name__}")

    def visit(self, node):
        if isinstance(node, FuncDecl):
            if node.nombre in self.funcs:
                raise Exception(f"Función '{node.nombre}' ya declarada")
            self.funcs[node.nombre] = node
            prev = self.env
            self.env = Environment(prev)
            self.env.declare(node.param_nombre, node.param_tipo)
            prev_return = self.current_return_type
            self.current_return_type = node.tipo
            for stmt in node.body:
                self.visit(stmt)
            self.current_return_type = prev_return
            self.env = prev
        elif isinstance(node, VarDecl):
            t_val = self.type_of(node.valor)
            if t_val != node.tipo:
                raise Exception(f"No se puede asignar '{t_val}' a '{node.nombre}' de tipo '{node.tipo}'")
            self.env.declare(node.nombre, node.tipo)
        elif isinstance(node, ArrayDecl):
            self.env.declare(node.nombre, f"{node.tipo}_array")
        elif isinstance(node, Assign):
            t_var = self.env.get_type(node.nombre)
            t_val = self.type_of(node.valor)
            if t_var.endswith('_array'):
                raise Exception(f"'{node.nombre}' es un arreglo y no puede asignarse directamente")
            if t_var != t_val:
                raise Exception(f"No se puede asignar '{t_val}' a '{node.nombre}' de tipo '{t_var}'")
        elif isinstance(node, ArrayAssign):
            t_var = self.env.get_type(node.nombre)
            t_idx = self.type_of(node.index)
            t_val = self.type_of(node.valor)
            if t_idx != 'int':
                raise Exception("Indice requiere int")
            if not t_var.endswith('_array'):
                raise Exception(f"'{node.nombre}' no es un arreglo")
            if t_var.replace('_array', '') != t_val:
                raise Exception(f"No se puede asignar '{t_val}' a elementos de '{node.nombre}'")
        elif isinstance(node, (IfStmt, WhileStmt)):
            if self.type_of(node.cond) != 'bool':
                raise Exception("La condición debe ser booleana")
            prev = self.env
            self.env = Environment(prev)
            for stmt in node.body:
                self.visit(stmt)
            self.env = prev
        elif isinstance(node, ReturnStmt):
            t_ret = self.type_of(node.expr)
            if self.current_return_type is not None and t_ret != self.current_return_type:
                raise Exception(f"Return incompatible: se esperaba '{self.current_return_type}' y se obtuvo '{t_ret}'")
        elif isinstance(node, Print):
            self.type_of(node.expr)
        elif isinstance(node, CallExpr):
            if node.nombre not in self.funcs:
                raise Exception(f"Función '{node.nombre}' no declarada")
            func = self.funcs[node.nombre]
            t_arg = self.type_of(node.arg)
            if t_arg != func.param_tipo:
                raise Exception(f"Argumento incompatible en llamada a '{node.nombre}'")
            return func.tipo
        elif isinstance(node, BinOp):
            return self.type_of(node)
        elif isinstance(node, Literal):
            return node.tipo
        elif isinstance(node, VarAccess):
            return self.env.get_type(node.nombre)
        elif isinstance(node, ArrayAccess):
            return self.type_of(node)
        return None

# ==========================================
# OPTIMIZADOR
# ==========================================
class Optimizer:
    def optimize(self, ast):
        return [self.visit(n) for n in ast]

    def visit(self, node):
        if isinstance(node, FuncDecl):
            node.body = [self.visit(s) for s in node.body]
        elif isinstance(node, VarDecl):
            node.valor = self.visit(node.valor)
        elif isinstance(node, ArrayDecl):
            pass
        elif isinstance(node, Assign):
            node.valor = self.visit(node.valor)
        elif isinstance(node, ArrayAssign):
            node.index = self.visit(node.index)
            node.valor = self.visit(node.valor)
        elif isinstance(node, (IfStmt, WhileStmt)):
            node.cond = self.visit(node.cond)
            node.body = [self.visit(s) for s in node.body]
        elif isinstance(node, ReturnStmt):
            node.expr = self.visit(node.expr)
        elif isinstance(node, Print):
            node.expr = self.visit(node.expr)
        elif isinstance(node, CallExpr):
            node.arg = self.visit(node.arg)
        elif isinstance(node, ArrayAccess):
            node.index = self.visit(node.index)
        elif isinstance(node, BinOp):
            node.izq = self.visit(node.izq)
            node.der = self.visit(node.der)
            if isinstance(node.izq, Literal) and isinstance(node.der, Literal):
                vi = node.izq.val
                vd = node.der.val
                if node.op == '+': res = vi + vd
                elif node.op == '-': res = vi - vd
                elif node.op == '*': res = vi * vd
                elif node.op == '/': res = vi // vd
                elif node.op == '==': res = vi == vd
                elif node.op == '<': res = vi < vd
                elif node.op == '>': res = vi > vd
                t = 'int' if type(res) is int else 'bool'
                return Literal(res, t)
        return node

# ==========================================
# GENERADOR DE CÓDIGO
# ==========================================
class CodeGenerator:
    def __init__(self):
        self.inst = []
        self.temp_c = 0
        self.label_c = 0

    def get_label(self):
        self.label_c += 1
        return f"L{self.label_c}"

    def get_temp(self):
        self.temp_c += 1
        return f"t{self.temp_c}"

    def generate(self, ast):
        self.inst = []
        for nodo in ast:
            self.visit(nodo)
        return '\n'.join(self.inst)

    def visit(self, nodo):
        clase = type(nodo).__name__
        metodo = getattr(self, f'visit_{clase}', self.visit_default)
        return metodo(nodo)

    def visit_default(self, nodo):
        raise Exception(f"Nodo no soportado en generación: {type(nodo).__name__}")

    def visit_FuncDecl(self, nodo):
        self.inst.append(f"{nodo.nombre}:")
        self.inst.append(f"POP {nodo.param_nombre}")
        for stmt in nodo.body:
            self.visit(stmt)
        self.inst.append("RET")

    def visit_VarDecl(self, nodo):
        val = self.visit(nodo.valor)
        self.inst.append(f"MOV {nodo.nombre}, {val}")

    def visit_ArrayDecl(self, nodo):
        self.inst.append(f"ALLOC_ARR {nodo.nombre}, {nodo.size}")

    def visit_Assign(self, nodo):
        val = self.visit(nodo.valor)
        self.inst.append(f"MOV {nodo.nombre}, {val}")

    def visit_ArrayAssign(self, nodo):
        idx = self.visit(nodo.index)
        val = self.visit(nodo.valor)
        self.inst.append(f"STORE_ARR {nodo.nombre}[{idx}], {val}")

    def visit_IfStmt(self, nodo):
        cond = self.visit(nodo.cond)
        l_fin = self.get_label()
        self.inst.append(f"JMP_FALSE {cond}, {l_fin}")
        for stmt in nodo.body:
            self.visit(stmt)
        self.inst.append(f"{l_fin}:")

    def visit_WhileStmt(self, nodo):
        l_inicio = self.get_label()
        l_fin = self.get_label()
        self.inst.append(f"{l_inicio}:")
        cond = self.visit(nodo.cond)
        self.inst.append(f"JMP_FALSE {cond}, {l_fin}")
        for stmt in nodo.body:
            self.visit(stmt)
        self.inst.append(f"JMP {l_inicio}")
        self.inst.append(f"{l_fin}:")

    def visit_ReturnStmt(self, nodo):
        val = self.visit(nodo.expr)
        self.inst.append(f"PUSH {val}")
        self.inst.append("RET")

    def visit_Print(self, nodo):
        val = self.visit(nodo.expr)
        self.inst.append(f"PRINT {val}")

    def visit_CallExpr(self, nodo):
        arg = self.visit(nodo.arg)
        self.inst.append(f"PUSH {arg}")
        self.inst.append(f"CALL {nodo.nombre}")
        temp = self.get_temp()
        self.inst.append(f"POP {temp}")
        return temp

    def visit_BinOp(self, nodo):
        izq = self.visit(nodo.izq)
        der = self.visit(nodo.der)
        temp = self.get_temp()
        op_map = {
            '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV',
            '==': 'CMP_EQ', '<': 'CMP_LT', '>': 'CMP_GT'
        }
        self.inst.append(f"MOV {temp}, {izq}")
        self.inst.append(f"{op_map[nodo.op]} {temp}, {der}")
        return temp

    def visit_Literal(self, nodo):
        if nodo.tipo == 'bool':
            return "1" if nodo.val else "0"
        return str(nodo.val)

    def visit_VarAccess(self, nodo):
        return nodo.nombre

    def visit_ArrayAccess(self, nodo):
        idx = self.visit(nodo.index)
        temp = self.get_temp()
        self.inst.append(f"LOAD_ARR {temp}, {nodo.nombre}[{idx}]")
        return temp

# ==========================================
# INTÉRPRETE
# ==========================================
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class InterpEnv:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def set_var(self, name, val):
        self.vars[name] = val

    def update_var(self, name, val):
        if name in self.vars:
            self.vars[name] = val
        elif self.parent:
            self.parent.update_var(name, val)
        else:
            raise Exception(f"'{name}' no declarada")

    def get_var(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get_var(name)
        raise Exception(f"'{name}' no declarada")

class Interpreter:
    def ejecutar(self, ast):
        self.salida = []
        self.env = InterpEnv()
        for node in ast:
            self.visit(node)
        return '\n'.join(self.salida)

    def visit(self, node):
        if isinstance(node, FuncDecl):
            self.env.set_var(node.nombre, node)
        elif isinstance(node, VarDecl):
            self.env.set_var(node.nombre, self.visit(node.valor))
        elif isinstance(node, ArrayDecl):
            val = [0] * node.size if node.tipo == 'int' else [False] * node.size
            self.env.set_var(node.nombre, val)
        elif isinstance(node, Assign):
            self.env.update_var(node.nombre, self.visit(node.valor))
        elif isinstance(node, ArrayAssign):
            arr = self.env.get_var(node.nombre)
            idx = self.visit(node.index)
            arr[idx] = self.visit(node.valor)
        elif isinstance(node, IfStmt):
            if self.visit(node.cond):
                prev = self.env
                self.env = InterpEnv(prev)
                for s in node.body: self.visit(s)
                self.env = prev
        elif isinstance(node, WhileStmt):
            while self.visit(node.cond):
                prev = self.env
                self.env = InterpEnv(prev)
                for s in node.body: self.visit(s)
                self.env = prev
        elif isinstance(node, ReturnStmt):
            raise ReturnException(self.visit(node.expr))
        elif isinstance(node, Print):
            self.salida.append(str(self.visit(node.expr)))
        elif isinstance(node, CallExpr):
            func = self.env.get_var(node.nombre)
            arg_val = self.visit(node.arg)
            prev = self.env
            self.env = InterpEnv(prev)
            self.env.set_var(func.param_nombre, arg_val)
            try:
                for s in func.body:
                    self.visit(s)
            except ReturnException as ret:
                self.env = prev
                return ret.value
            self.env = prev
        elif isinstance(node, BinOp):
            i = self.visit(node.izq)
            d = self.visit(node.der)
            if node.op == '+': return i + d
            if node.op == '-': return i - d
            if node.op == '*': return i * d
            if node.op == '/': return i // d
            if node.op == '==': return i == d
            if node.op == '<': return i < d
            if node.op == '>': return i > d
        elif isinstance(node, Literal):
            return node.val
        elif isinstance(node, VarAccess):
            return self.env.get_var(node.nombre)
        elif isinstance(node, ArrayAccess):
            arr = self.env.get_var(node.nombre)
            idx = self.visit(node.index)
            return arr[idx]

# ==========================================
# INTERFAZ
# ==========================================
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador v3.4")
        self.root.geometry("750x700")
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Código Fuente:", font=("Arial", 10, "bold")).pack(pady=2)
        self.txt_codigo = tk.Text(self.root, height=14, width=85, font=("Courier", 10))
        self.txt_codigo.pack()
        
        codigo_prueba = (
            "int lista[5];\n"
            "lista[0] = 8;\n"
            "lista[1] = 3;\n"
            "lista[2] = 5;\n"
            "lista[3] = 1;\n"
            "lista[4] = 9;\n\n"
            "int temp = 0;\n"
            "bool orden = false;\n"
            "int i = 0;\n\n"
            "while (orden == false) {\n"
            "    orden = true;\n"
            "    i = 0;\n"
            "    while (i < 4) {\n"
            "        if (lista[i] > lista[i + 1]) {\n"
            "            temp = lista[i];\n"
            "            lista[i] = lista[i + 1];\n"
            "            lista[i + 1] = temp;\n"
            "            orden = false;\n"
            "        }\n"
            "        i = i + 1;\n"
            "    }\n"
            "}\n\n"
            "i = 0;\n"
            "while (i < 5) {\n"
            "    print(lista[i]);\n"
            "    i = i + 1;\n"
            "}"
        )
        self.txt_codigo.insert(tk.END, codigo_prueba)
        
        tk.Button(self.root, text="Compilar y Ejecutar", command=self.ejecutar_codigo, bg="lightgray").pack(pady=5)

        tk.Label(self.root, text="Salida (Intérprete):", font=("Arial", 10, "bold")).pack(pady=2)
        self.txt_consola = tk.Text(self.root, height=5, width=85, font=("Courier", 10))
        self.txt_consola.pack()

        tk.Label(self.root, text="Código Destino (Ensamblador):", font=("Arial", 10, "bold")).pack(pady=2)
        self.txt_asm = tk.Text(self.root, height=12, width=85, font=("Courier", 10))
        self.txt_asm.pack()

    def ejecutar_codigo(self):
        codigo = self.txt_codigo.get("1.0", tk.END).strip()
        self.txt_consola.delete("1.0", tk.END)
        self.txt_asm.delete("1.0", tk.END)
        
        try:
            tokens = Lexer().tokenize(codigo)
            ast = Parser(tokens).parse()
            
            SemanticAnalyzer().analyze(ast)
            ast_opt = Optimizer().optimize(ast)
            
            salida = Interpreter().ejecutar(ast_opt)
            ensamblador = CodeGenerator().generate(ast_opt)
            
            self.txt_consola.config(fg="black")
            self.txt_consola.insert(tk.END, salida)
            
            self.txt_asm.config(fg="blue")
            self.txt_asm.insert(tk.END, ensamblador)
            
        except Exception as e:
            self.txt_consola.config(fg="red")
            self.txt_consola.insert(tk.END, str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()