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
    FuncDecl,
    IfStmt,
    Literal,
    Print,
    ReturnStmt,
    UnaryOp,
    VarAccess,
    VarDecl,
    WhileStmt,
)
from .errors import MiniLangRuntimeError


UNINITIALIZED = object()


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class InterpEnv:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def set_var(self, name, value):
        if name in self.vars:
            raise MiniLangRuntimeError(f"'{name}' ya existe en este ámbito")
        self.vars[name] = value

    def update_var(self, name, value, token=None):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.update_var(name, value, token)
            return
        raise MiniLangRuntimeError(f"'{name}' no está declarado", token)

    def get_var(self, name, token=None):
        if name in self.vars:
            value = self.vars[name]
            if value is UNINITIALIZED:
                raise MiniLangRuntimeError(f"'{name}' se usó antes de inicializarse", token)
            return value
        if self.parent:
            return self.parent.get_var(name, token)
        raise MiniLangRuntimeError(f"'{name}' no está declarado", token)


class Interpreter:
    def __init__(self, max_steps=100_000, max_call_depth=500):
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth

    def ejecutar(self, ast):
        self.salida = []
        self.steps = 0
        self.call_depth = 0
        self.global_env = InterpEnv()
        self.env = self.global_env
        self.funcs = {node.nombre: node for node in ast if isinstance(node, FuncDecl)}
        for node in ast:
            if not isinstance(node, FuncDecl):
                self.visit(node)
        return "\n".join(self.salida)

    def _tick(self, node):
        self.steps += 1
        if self.steps > self.max_steps:
            raise MiniLangRuntimeError(
                f"se superó el límite de {self.max_steps} instrucciones; posible ciclo infinito",
                getattr(node, "token", None),
            )

    def visit(self, node):
        self._tick(node)
        if isinstance(node, VarDecl):
            value = UNINITIALIZED if node.valor is None else self.visit(node.valor)
            self.env.set_var(node.nombre, value)
        elif isinstance(node, ArrayDecl):
            defaults = {"int": 0, "bool": False, "string": ""}
            self.env.set_var(node.nombre, [defaults[node.tipo] for _ in range(node.size)])
        elif isinstance(node, Assign):
            self.env.update_var(node.nombre, self.visit(node.valor), node.token)
        elif isinstance(node, ArrayAssign):
            array = self.env.get_var(node.nombre, node.token)
            index = self.visit(node.index)
            self._check_bounds(node.nombre, array, index, node.token)
            array[index] = self.visit(node.valor)
        elif isinstance(node, IfStmt):
            branch = node.body if self.visit(node.cond) else node.else_body
            if branch:
                self._execute_block(branch)
        elif isinstance(node, WhileStmt):
            while self.visit(node.cond):
                try:
                    self._execute_block(node.body)
                except ContinueException:
                    continue
                except BreakException:
                    break
        elif isinstance(node, ReturnStmt):
            raise ReturnException(None if node.expr is None else self.visit(node.expr))
        elif isinstance(node, BreakStmt):
            raise BreakException()
        elif isinstance(node, ContinueStmt):
            raise ContinueException()
        elif isinstance(node, Print):
            self.salida.append(str(self.visit(node.expr)))
        elif isinstance(node, ExprStmt):
            self.visit(node.expr)
        elif isinstance(node, CallExpr):
            return self._call(node)
        elif isinstance(node, BinOp):
            return self._binary(node)
        elif isinstance(node, UnaryOp):
            value = self.visit(node.expr)
            return -value if node.op == "-" else not value
        elif isinstance(node, Literal):
            return node.val
        elif isinstance(node, VarAccess):
            return self.env.get_var(node.nombre, node.token)
        elif isinstance(node, ArrayAccess):
            array = self.env.get_var(node.nombre, node.token)
            index = self.visit(node.index)
            self._check_bounds(node.nombre, array, index, node.token)
            return array[index]

    def _call(self, node):
        function = self.funcs.get(node.nombre)
        if function is None:
            raise MiniLangRuntimeError(f"función '{node.nombre}' no declarada", node.token)
        if self.call_depth >= self.max_call_depth:
            raise MiniLangRuntimeError(
                f"se superó la profundidad máxima de {self.max_call_depth} llamadas", node.token
            )
        argument_values = [self.visit(argument) for argument in node.args]
        previous = self.env
        self.env = InterpEnv(self.global_env)
        self.call_depth += 1
        try:
            for parameter, value in zip(function.params, argument_values):
                self.env.set_var(parameter.nombre, value)
            try:
                for statement in function.body:
                    self.visit(statement)
            except ReturnException as returned:
                return returned.value
            if function.tipo != "void":
                raise MiniLangRuntimeError(
                    f"la función '{function.nombre}' terminó sin retornar un valor", function.token
                )
            return None
        finally:
            self.call_depth -= 1
            self.env = previous

    def _execute_block(self, statements):
        previous = self.env
        self.env = InterpEnv(previous)
        try:
            for statement in statements:
                self.visit(statement)
        finally:
            self.env = previous

    def _binary(self, node):
        left = self.visit(node.izq)
        if node.op == "&&":
            return left and self.visit(node.der)
        if node.op == "||":
            return left or self.visit(node.der)
        right = self.visit(node.der)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise MiniLangRuntimeError("división por cero", node.token)
            return left // right
        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        if node.op == "<":
            return left < right
        if node.op == "<=":
            return left <= right
        if node.op == ">":
            return left > right
        if node.op == ">=":
            return left >= right
        raise MiniLangRuntimeError(f"operador desconocido '{node.op}'", node.token)

    @staticmethod
    def _check_bounds(name, array, index, token):
        if type(index) is not int or not 0 <= index < len(array):
            raise MiniLangRuntimeError(
                f"índice {index!r} fuera de rango para '{name}' (tamaño {len(array)})", token
            )
