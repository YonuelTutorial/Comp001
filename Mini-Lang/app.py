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

class Assign:
    def __init__(self, nombre, valor):
        self.nombre = nombre
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
                param_tipo = self.match('INT_T')[1]
                param_nombre = self.match('ID')[1]
                self.match('RPAREN')
                body = self.block()
                return FuncDecl(tipo, nombre, param_tipo, param_nombre, body)
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
            self.match('ASSIGN')
            valor = self.expression()
            self.match('SEMI')
            return Assign(nombre, valor)
        raise Exception("Sintaxis inválida")

    def block(self):
        self.match('LBRACE')
        stmts = []
        while self.tokens[self.pos][0] != 'RBRACE':
            stmts.append(self.declaration())
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
    def analyze(self, ast):
        self.env = Environment()
        for node in ast:
            self.visit(node)

    def visit(self, node):
        if isinstance(node, FuncDecl):
            self.env.declare(node.nombre, node.tipo)
            prev = self.env
            self.env = Environment(prev)
            self.env.declare(node.param_nombre, node.param_tipo)
            for stmt in node.body:
                self.visit(stmt)
            self.env = prev
        elif isinstance(node, VarDecl):
            t_val = self.visit(node.valor)
            self.env.declare(node.nombre, node.tipo)
        elif isinstance(node, Assign):
            t_var = self.env.get_type(node.nombre)
            t_val = self.visit(node.valor)
        elif isinstance(node, (IfStmt, WhileStmt)):
            self.visit(node.cond)
            prev = self.env
            self.env = Environment(prev)
            for stmt in node.body:
                self.visit(stmt)
            self.env = prev
        elif isinstance(node, ReturnStmt):
            self.visit(node.expr)
        elif isinstance(node, Print):
            self.visit(node.expr)
        elif isinstance(node, CallExpr):
            self.env.get_type(node.nombre)
            self.visit(node.arg)
            return 'int'
        elif isinstance(node, BinOp):
            t_izq = self.visit(node.izq)
            t_der = self.visit(node.der)
            if node.op in ('+', '-', '*', '/'):
                return 'int'
            elif node.op in ('==', '<', '>'):
                return 'bool'
        elif isinstance(node, Literal):
            return node.tipo
        elif isinstance(node, VarAccess):
            return self.env.get_type(node.nombre)

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
        elif isinstance(node, Assign):
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
        else:
            self.parent.update_var(name, val)

    def get_var(self, name):
        if name in self.vars:
            return self.vars[name]
        return self.parent.get_var(name)

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
        elif isinstance(node, Assign):
            self.env.update_var(node.nombre, self.visit(node.valor))
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

# ==========================================
# INTERFAZ
# ==========================================
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Intérprete Completo: Recursividad y Ámbitos")
        self.root.geometry("700x600")
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Código Fuente:", font=("Arial", 10, "bold")).pack(pady=5)
        self.txt_codigo = tk.Text(self.root, height=15, width=80, font=("Courier", 10))
        self.txt_codigo.pack()
        
        codigo_prueba = (
            "int factorial(int n) {\n"
            "    if (n == 0) {\n"
            "        return 1;\n"
            "    }\n"
            "    return n * factorial(n - 1);\n"
            "}\n\n"
            "int res_fact = factorial(5);\n"
            "print(res_fact);"
        )
        self.txt_codigo.insert(tk.END, codigo_prueba)
        
        tk.Button(self.root, text="Ejecutar", command=self.ejecutar_codigo, bg="lightgray").pack(pady=10)

        tk.Label(self.root, text="Salida (Intérprete):", font=("Arial", 10, "bold")).pack(pady=5)
        self.txt_consola = tk.Text(self.root, height=10, width=80, font=("Courier", 10))
        self.txt_consola.pack()

    def ejecutar_codigo(self):
        codigo = self.txt_codigo.get("1.0", tk.END).strip()
        self.txt_consola.delete("1.0", tk.END)
        
        try:
            tokens = Lexer().tokenize(codigo)
            ast = Parser(tokens).parse()
            SemanticAnalyzer().analyze(ast)
            ast_opt = Optimizer().optimize(ast)
            salida = Interpreter().ejecutar(ast_opt)
            
            self.txt_consola.config(fg="black")
            self.txt_consola.insert(tk.END, salida)
            
        except Exception as e:
            self.txt_consola.config(fg="red")
            self.txt_consola.insert(tk.END, str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()