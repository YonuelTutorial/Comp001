

import tkinter as tk
import re

TOKEN_REGEX = [
    ('IF', r'if\b'),
    ('ELSE', r'else\b'),
    ('WHILE', r'while\b'),

    ('PRINT', r'print\b'),

    ('INT_T', r'int\b'),
    ('STR_T', r'string\b'),
    ('BOOL_T', r'bool\b'),

    ('TRUE', r'true\b'),
    ('FALSE', r'false\b'),

    ('EQ', r'=='),
    ('NE', r'!='),
    ('GE', r'>='),
    ('LE', r'<='),
    ('GT', r'>'),
    ('LT', r'<'),

    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('MUL', r'\*'),
    ('DIV', r'/'),
    ('MOD', r'%'),

    ('ASSIGN', r'='),

    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),

    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),

    ('SEMI', r';'),

    ('NUM', r'\d+'),
    ('STR_VAL', r'"[^"]*"'),

    ('ID', r'[a-zA-Z_]\w*'),

    ('SKIP', r'[ \t\n]+'),
    ('MISMATCH', r'.')
]


class Lexer:

    def tokenize(self, code):
        tokens = []
        line_num = 1
        regex = '|'.join(
            f'(?P<{name}>{pattern})'
            for name, pattern in TOKEN_REGEX
        )

        for mo in re.finditer(regex, code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP':
                line_num += value.count('\n')
                continue
            if kind == 'MISMATCH':
                raise Exception(
                    f"Línea {line_num}: Error Léxico '{value}'"
                )
            tokens.append(
                (kind, value, line_num)
            )
        return tokens
    
class Literal:

    def __init__(self, value, tipo):
        self.value = value
        self.tipo = tipo


class Variable:

    def __init__(self, nombre):
        self.nombre = nombre


class BinaryOp:

    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class If:

    def __init__(self, condicion, cuerpo, sino):

        self.condicion = condicion
        self.cuerpo = cuerpo
        self.sino = sino


class While:

    def __init__(self, condicion, cuerpo):

        self.condicion = condicion
        self.cuerpo = cuerpo


class Print:

    def __init__(self, expresion):

        self.expresion = expresion

class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):

        if self.pos < len(self.tokens):
            return self.tokens[self.pos]

        return None

    def match(self, expected):

        token = self.current()

        if token and token[0] == expected:
            self.pos += 1
            return token

        raise Exception(
            f"Se esperaba {expected}"
        )

    def parse(self):

        ast = []

        while self.current():
            ast.append(
                self.statement()
            )

        return ast

    def statement(self):

        token = self.current()

        if token[0] in (
            'INT_T',
            'STR_T',
            'BOOL_T'
        ):
            return self.var_decl()

        if token[0] == 'ID':
            return self.assignment()

        if token[0] == 'PRINT':
            return self.print_stmt()

        if token[0] == 'IF':
            return self.if_stmt()

        if token[0] == 'WHILE':
            return self.while_stmt()

        raise Exception(
            f"Instrucción inválida: {token}"
        )

    def var_decl(self):

        tipo = self.current()[1]
        self.pos += 1

        nombre = self.match('ID')[1]

        expr = None

        if self.current() and self.current()[0] == 'ASSIGN':

            self.match('ASSIGN')

            expr = self.expression()

        self.match('SEMI')

        return (
            'VAR_DECL',
            tipo,
            nombre,
            expr
        )

    def assignment(self):

        nombre = self.match('ID')[1]

        self.match('ASSIGN')

        expr = self.expression()

        self.match('SEMI')

        return (
            'ASSIGN',
            nombre,
            expr
        )

    def print_stmt(self):

        self.match('PRINT')

        self.match('LPAREN')

        expr = self.expression()

        self.match('RPAREN')

        self.match('SEMI')

        return Print(expr)

    def if_stmt(self):

        self.match('IF')

        self.match('LPAREN')

        condicion = self.expression()

        self.match('RPAREN')

        cuerpo = self.block()

        sino = []

        if self.current() and self.current()[0] == 'ELSE':

            self.match('ELSE')

            sino = self.block()

        return If(
            condicion,
            cuerpo,
            sino
        )

    def while_stmt(self):

        self.match('WHILE')

        self.match('LPAREN')

        condicion = self.expression()

        self.match('RPAREN')

        cuerpo = self.block()

        return While(
            condicion,
            cuerpo
        )

    def block(self):

        self.match('LBRACE')

        instrucciones = []

        while (
            self.current()
            and
            self.current()[0] != 'RBRACE'
        ):

            instrucciones.append(
                self.statement()
            )

        self.match('RBRACE')

        return instrucciones

    def expression(self):
        return self.relational()

    def relational(self):

        node = self.additive()

        while (
            self.current()
            and
            self.current()[0]
            in (
                'EQ',
                'NE',
                'GT',
                'LT',
                'GE',
                'LE'
            )
        ):

            op = self.current()[1]

            self.pos += 1

            right = self.additive()

            node = BinaryOp(
                node,
                op,
                right
            )

        return node

    def additive(self):

        node = self.term()

        while (
            self.current()
            and
            self.current()[0]
            in (
                'PLUS',
                'MINUS'
            )
        ):

            op = self.current()[1]

            self.pos += 1

            right = self.term()

            node = BinaryOp(
                node,
                op,
                right
            )

        return node

    def term(self):

        node = self.factor()

        while (
            self.current()
            and
            self.current()[0]
            in (
                'MUL',
                'DIV',
                'MOD'
            )
        ):

            op = self.current()[1]

            self.pos += 1

            right = self.factor()

            node = BinaryOp(
                node,
                op,
                right
            )

        return node

    def factor(self):

        token = self.current()

        if token[0] == 'NUM':

            self.pos += 1

            return Literal(
                int(token[1]),
                'int'
            )

        if token[0] == 'STR_VAL':

            self.pos += 1

            return Literal(
                token[1],
                'string'
            )

        if token[0] == 'TRUE':

            self.pos += 1

            return Literal(
                True,
                'bool'
            )

        if token[0] == 'FALSE':

            self.pos += 1

            return Literal(
                False,
                'bool'
            )

        if token[0] == 'ID':

            self.pos += 1

            return Variable(
                token[1]
            )

        if token[0] == 'LPAREN':

            self.match('LPAREN')

            expr = self.expression()

            self.match('RPAREN')

            return expr

        raise Exception(
            f"Factor inválido: {token}"
        )

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador Mejorado")
        self.lexer = Lexer()

        self.txt = tk.Text(root, height=15, width=90)
        self.txt.pack()

        self.out = tk.Text(root, height=15, width=90)
        self.out.pack()

        tk.Button(root, text="Analizar", command=self.run).pack()

        self.txt.insert("1.0", """int a = 5 + 3;
bool activo = true;
print(a);
""")
        
        


    def run(self):
        self.out.delete("1.0", tk.END)
        try:
            tokens = self.lexer.tokenize(self.txt.get("1.0", tk.END))
            for t in tokens:
                self.out.insert(tk.END, str(t) + "\\n")
        except Exception as e:
            self.out.insert(tk.END, str(e))

if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
