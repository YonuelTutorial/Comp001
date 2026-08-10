from .ast_nodes import (
    ArrayAccess,
    ArrayAssign,
    ArrayDecl,
    Assign,
    BinOp,
    BreakStmt,
    CallExpr,
    ContinueStmt,
    ExprStmt,
    ForStmt,
    FuncDecl,
    IfStmt,
    ImportStmt,
    Literal,
    Param,
    Print,
    ReturnStmt,
    UnaryOp,
    VarAccess,
    VarDecl,
    WhileStmt,
)
from .errors import ParserError


TYPE_TOKENS = {
    "INT_T": "int",
    "BOOL_T": "bool",
    "STRING_T": "string",
    "FLOAT_T": "float",
    "VOID_T": "void",
}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self):
        return self.tokens[min(self.pos, len(self.tokens) - 1)]

    def check(self, *kinds):
        return self.current.kind in kinds

    def advance(self):
        token = self.current
        if token.kind != "EOF":
            self.pos += 1
        return token

    def match(self, expected):
        if self.check(expected):
            return self.advance()
        found = self.current.value or "fin de archivo"
        raise ParserError(f"se esperaba {expected}, se encontró {found!r}", self.current)

    def accept(self, *kinds):
        if self.check(*kinds):
            return self.advance()
        return None

    def parse(self):
        ast = []
        while not self.check("EOF"):
            ast.append(self.declaration(top_level=True))
        return ast

    def declaration(self, top_level=False):
        if token := self.accept("IMPORT"):
            if not top_level:
                raise ParserError("import solo puede utilizarse en el nivel global", token)
            path = self.match("STRING")
            self.match("SEMI")
            return ImportStmt(self.decode_string(path), token)

        if self.check(*TYPE_TOKENS):
            type_token = self.advance()
            tipo = TYPE_TOKENS[type_token.kind]
            name_token = self.match("ID")

            if self.accept("LPAREN"):
                if not top_level:
                    raise ParserError("las funciones solo pueden declararse en el nivel global", name_token)
                params = self.parameters()
                body = self.block()
                return FuncDecl(tipo, name_token.value, params, body, type_token)

            if tipo == "void":
                raise ParserError("void solo puede usarse como retorno de una función", type_token)

            if self.accept("LBRACKET"):
                size_token = self.match("NUM")
                self.match("RBRACKET")
                self.match("SEMI")
                return ArrayDecl(tipo, name_token.value, int(size_token.value), name_token)

            value = None
            if self.accept("ASSIGN"):
                value = self.expression()
            self.match("SEMI")
            return VarDecl(tipo, name_token.value, value, name_token)

        return self.statement()

    def parameters(self):
        params = []
        if self.accept("RPAREN"):
            return params
        while True:
            if not self.check("INT_T", "BOOL_T", "STRING_T", "FLOAT_T"):
                raise ParserError("se esperaba un tipo de parámetro", self.current)
            type_token = self.advance()
            name_token = self.match("ID")
            params.append(Param(TYPE_TOKENS[type_token.kind], name_token.value, name_token))
            if not self.accept("COMMA"):
                break
        self.match("RPAREN")
        return params

    def statement(self):
        if token := self.accept("PRINT"):
            self.match("LPAREN")
            expr = self.expression()
            self.match("RPAREN")
            self.match("SEMI")
            return Print(expr, token)

        if token := self.accept("IF"):
            self.match("LPAREN")
            cond = self.expression()
            self.match("RPAREN")
            body = self.block()
            else_body = []
            if self.accept("ELSE"):
                if self.check("IF"):
                    else_body = [self.statement()]
                else:
                    else_body = self.block()
            return IfStmt(cond, body, else_body, token)

        if token := self.accept("WHILE"):
            self.match("LPAREN")
            cond = self.expression()
            self.match("RPAREN")
            return WhileStmt(cond, self.block(), token)

        if token := self.accept("FOR"):
            self.match("LPAREN")
            if self.accept("SEMI"):
                init = None
            elif self.check("INT_T", "BOOL_T", "STRING_T", "FLOAT_T"):
                init = self.declaration(top_level=False)
            else:
                init = self.assignment_or_expression()

            if self.accept("SEMI"):
                cond = Literal(True, "bool", token)
            else:
                cond = self.expression()
                self.match("SEMI")

            update = None if self.check("RPAREN") else self.assignment_or_expression(consume_semi=False)
            self.match("RPAREN")
            return ForStmt(init, cond, update, self.block(), token)

        if token := self.accept("RETURN"):
            expr = None if self.check("SEMI") else self.expression()
            self.match("SEMI")
            return ReturnStmt(expr, token)

        if token := self.accept("BREAK"):
            self.match("SEMI")
            return BreakStmt(token)

        if token := self.accept("CONTINUE"):
            self.match("SEMI")
            return ContinueStmt(token)

        if self.check("LBRACE"):
            raise ParserError("un bloque aislado no es una sentencia válida", self.current)

        return self.assignment_or_expression()

    def assignment_or_expression(self, consume_semi=True):
        start = self.current
        target = self.expression()
        operator = self.accept(
            "ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN", "STAR_ASSIGN", "SLASH_ASSIGN", "MOD_ASSIGN"
        )
        if operator:
            value = self.expression()
            if operator.kind != "ASSIGN":
                binary_operator = {
                    "PLUS_ASSIGN": "+",
                    "MINUS_ASSIGN": "-",
                    "STAR_ASSIGN": "*",
                    "SLASH_ASSIGN": "/",
                    "MOD_ASSIGN": "%",
                }[operator.kind]
                value = BinOp(target, binary_operator, value, operator)
            statement = self._assignment(target, value, start)
        elif increment := self.accept("PLUS_PLUS", "MINUS_MINUS"):
            operator_value = "+" if increment.kind == "PLUS_PLUS" else "-"
            value = BinOp(target, operator_value, Literal(1, "int", increment), increment)
            statement = self._assignment(target, value, start)
        else:
            statement = ExprStmt(target, start)
        if consume_semi:
            self.match("SEMI")
        return statement

    @staticmethod
    def _assignment(target, value, token):
        if isinstance(target, VarAccess):
            return Assign(target.nombre, value, token)
        if isinstance(target, ArrayAccess):
            return ArrayAssign(target.nombre, target.index, value, token)
        raise ParserError("el lado izquierdo de una asignación no es modificable", token)

    def block(self):
        self.match("LBRACE")
        statements = []
        while not self.check("RBRACE", "EOF"):
            statements.append(self.declaration(top_level=False))
        if self.check("EOF"):
            raise ParserError("falta '}' para cerrar el bloque", self.current)
        self.advance()
        return statements

    def expression(self):
        return self.logical_or()

    def logical_or(self):
        node = self.logical_and()
        while token := self.accept("OR"):
            node = BinOp(node, token.value, self.logical_and(), token)
        return node

    def logical_and(self):
        node = self.equality()
        while token := self.accept("AND"):
            node = BinOp(node, token.value, self.equality(), token)
        return node

    def equality(self):
        node = self.relational()
        while token := self.accept("EQ", "NE"):
            node = BinOp(node, token.value, self.relational(), token)
        return node

    def relational(self):
        node = self.term()
        while token := self.accept("LT", "LE", "GT", "GE"):
            node = BinOp(node, token.value, self.term(), token)
        return node

    def term(self):
        node = self.factor()
        while token := self.accept("PLUS", "MINUS"):
            node = BinOp(node, token.value, self.factor(), token)
        return node

    def factor(self):
        node = self.unary()
        while token := self.accept("STAR", "SLASH", "MOD"):
            node = BinOp(node, token.value, self.unary(), token)
        return node

    def unary(self):
        if token := self.accept("MINUS", "NOT"):
            return UnaryOp(token.value, self.unary(), token)
        return self.power()

    def power(self):
        node = self.primary()
        if token := self.accept("POW"):
            node = BinOp(node, token.value, self.unary(), token)
        return node

    def primary(self):
        token = self.current
        if self.accept("NUM"):
            return Literal(int(token.value), "int", token)
        if self.accept("FLOAT"):
            return Literal(float(token.value), "float", token)
        if self.accept("TRUE"):
            return Literal(True, "bool", token)
        if self.accept("FALSE"):
            return Literal(False, "bool", token)
        if self.accept("STRING"):
            return Literal(self.decode_string(token), "string", token)
        if self.accept("ID"):
            name = token.value
            if self.accept("LPAREN"):
                args = []
                if not self.check("RPAREN"):
                    while True:
                        args.append(self.expression())
                        if not self.accept("COMMA"):
                            break
                self.match("RPAREN")
                return CallExpr(name, args, token)
            if self.accept("LBRACKET"):
                index = self.expression()
                self.match("RBRACKET")
                return ArrayAccess(name, index, token)
            return VarAccess(name, token)
        if self.accept("LPAREN"):
            expr = self.expression()
            self.match("RPAREN")
            return expr
        raise ParserError("se esperaba una expresión", token)

    @staticmethod
    def decode_string(token):
        body = token.value[1:-1]
        escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"', "'": "'"}
        output = []
        index = 0
        while index < len(body):
            char = body[index]
            if char != "\\":
                output.append(char)
                index += 1
                continue
            index += 1
            if index >= len(body) or body[index] not in escapes:
                raise ParserError("secuencia de escape inválida", token)
            output.append(escapes[body[index]])
            index += 1
        return "".join(output)
