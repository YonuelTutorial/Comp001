from dataclasses import dataclass

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
from .errors import SemanticError


@dataclass(frozen=True)
class Symbol:
    tipo: str
    array_size: int | None = None

    @property
    def is_array(self):
        return self.array_size is not None


@dataclass(frozen=True)
class FunctionSignature:
    return_type: str
    params: tuple
    declaration: FuncDecl


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def declare(self, name, tipo, token=None, array_size=None):
        if name in self.vars:
            raise SemanticError(f"'{name}' ya fue declarado en este ámbito", token)
        self.vars[name] = Symbol(tipo, array_size)

    def get(self, name, token=None):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name, token)
        raise SemanticError(f"'{name}' no está declarado", token)

    def get_type(self, name):
        symbol = self.get(name)
        return f"{symbol.tipo}_array" if symbol.is_array else symbol.tipo


class SemanticAnalyzer:
    def __init__(self):
        self.funcs = {}
        self.current_return_type = None
        self.loop_depth = 0

    def analyze(self, ast):
        self.global_env = Environment()
        self.env = self.global_env
        self.funcs.clear()
        self.current_return_type = None
        self.loop_depth = 0
        global_names = set()

        # Registro global
        for node in ast:
            if isinstance(node, FuncDecl):
                self._reserve_global_name(node.nombre, node.token, global_names)
                param_types = tuple(param.tipo for param in node.params)
                self.funcs[node.nombre] = FunctionSignature(node.tipo, param_types, node)
            elif isinstance(node, VarDecl):
                self._reserve_global_name(node.nombre, node.token, global_names)
                self.global_env.declare(node.nombre, node.tipo, node.token)
            elif isinstance(node, ArrayDecl):
                self._reserve_global_name(node.nombre, node.token, global_names)
                self.global_env.declare(node.nombre, node.tipo, node.token, node.size)

        # Análisis
        for node in ast:
            self.visit(node, predeclared=isinstance(node, (VarDecl, ArrayDecl)))

    @staticmethod
    def _reserve_global_name(name, token, names):
        if name in names:
            raise SemanticError(f"el nombre global '{name}' ya está en uso", token)
        names.add(name)

    def type_of(self, node):
        if isinstance(node, Literal):
            return node.tipo
        if isinstance(node, VarAccess):
            symbol = self.env.get(node.nombre, node.token)
            if symbol.is_array:
                raise SemanticError(f"'{node.nombre}' es un arreglo", node.token)
            return symbol.tipo
        if isinstance(node, ArrayAccess):
            symbol = self._array_symbol(node.nombre, node.token)
            self._check_index(node.index, symbol, node.token)
            return symbol.tipo
        if isinstance(node, UnaryOp):
            expr_type = self.type_of(node.expr)
            if node.op == "-" and expr_type == "int":
                return "int"
            if node.op == "!" and expr_type == "bool":
                return "bool"
            expected = "int" if node.op == "-" else "bool"
            raise SemanticError(f"el operador '{node.op}' requiere {expected}", node.token)
        if isinstance(node, BinOp):
            left_type = self.type_of(node.izq)
            right_type = self.type_of(node.der)
            if node.op in ("+", "-", "*", "/"):
                if left_type != "int" or right_type != "int":
                    raise SemanticError("la operación aritmética requiere enteros", node.token)
                return "int"
            if node.op in ("<", "<=", ">", ">="):
                if left_type != "int" or right_type != "int":
                    raise SemanticError("la comparación relacional requiere enteros", node.token)
                return "bool"
            if node.op in ("==", "!="):
                if left_type != right_type or left_type == "void":
                    raise SemanticError("comparación entre tipos incompatibles", node.token)
                return "bool"
            if node.op in ("&&", "||"):
                if left_type != "bool" or right_type != "bool":
                    raise SemanticError("la operación lógica requiere booleanos", node.token)
                return "bool"
        if isinstance(node, CallExpr):
            return self._check_call(node)
        raise SemanticError(f"no se puede inferir el tipo de {type(node).__name__}", getattr(node, "token", None))

    def visit(self, node, predeclared=False):
        if isinstance(node, FuncDecl):
            self._visit_function(node)
        elif isinstance(node, VarDecl):
            if node.valor is not None:
                value_type = self.type_of(node.valor)
                if value_type != node.tipo:
                    raise SemanticError(
                        f"no se puede asignar '{value_type}' a '{node.nombre}' de tipo '{node.tipo}'", node.token
                    )
            if not predeclared:
                self.env.declare(node.nombre, node.tipo, node.token)
        elif isinstance(node, ArrayDecl):
            if node.size <= 0:
                raise SemanticError("el tamaño de un arreglo debe ser mayor que cero", node.token)
            if not predeclared:
                self.env.declare(node.nombre, node.tipo, node.token, node.size)
        elif isinstance(node, Assign):
            symbol = self.env.get(node.nombre, node.token)
            if symbol.is_array:
                raise SemanticError(f"'{node.nombre}' es un arreglo y no puede asignarse directamente", node.token)
            value_type = self.type_of(node.valor)
            if symbol.tipo != value_type:
                raise SemanticError(
                    f"no se puede asignar '{value_type}' a '{node.nombre}' de tipo '{symbol.tipo}'", node.token
                )
        elif isinstance(node, ArrayAssign):
            symbol = self._array_symbol(node.nombre, node.token)
            self._check_index(node.index, symbol, node.token)
            value_type = self.type_of(node.valor)
            if symbol.tipo != value_type:
                raise SemanticError(
                    f"no se puede asignar '{value_type}' a elementos '{symbol.tipo}' de '{node.nombre}'", node.token
                )
        elif isinstance(node, IfStmt):
            self._require_bool(node.cond, node.token)
            self._visit_block(node.body)
            self._visit_block(node.else_body)
        elif isinstance(node, WhileStmt):
            self._require_bool(node.cond, node.token)
            self.loop_depth += 1
            try:
                self._visit_block(node.body)
            finally:
                self.loop_depth -= 1
        elif isinstance(node, ReturnStmt):
            self._visit_return(node)
        elif isinstance(node, (BreakStmt, ContinueStmt)):
            if self.loop_depth == 0:
                keyword = "break" if isinstance(node, BreakStmt) else "continue"
                raise SemanticError(f"'{keyword}' solo puede utilizarse dentro de un ciclo", node.token)
        elif isinstance(node, Print):
            if self.type_of(node.expr) == "void":
                raise SemanticError("no se puede imprimir una expresión void", node.token)
        elif isinstance(node, ExprStmt):
            if not isinstance(node.expr, CallExpr):
                raise SemanticError("solo una llamada puede utilizarse como sentencia", node.token)
            self._check_call(node.expr)
        else:
            self.type_of(node)

    def _visit_function(self, node):
        previous_env = self.env
        previous_return = self.current_return_type
        previous_loop_depth = self.loop_depth
        self.env = Environment(self.global_env)
        self.current_return_type = node.tipo
        self.loop_depth = 0
        try:
            for param in node.params:
                self.env.declare(param.nombre, param.tipo, param.token)
            for statement in node.body:
                self.visit(statement)
            if node.tipo != "void" and not self._block_returns(node.body):
                raise SemanticError(
                    f"la función '{node.nombre}' debe retornar '{node.tipo}' en todas sus rutas", node.token
                )
        finally:
            self.env = previous_env
            self.current_return_type = previous_return
            self.loop_depth = previous_loop_depth

    def _visit_return(self, node):
        if self.current_return_type is None:
            raise SemanticError("return solo puede utilizarse dentro de una función", node.token)
        if node.expr is None:
            if self.current_return_type != "void":
                raise SemanticError(f"se esperaba retornar '{self.current_return_type}'", node.token)
            return
        if self.current_return_type == "void":
            raise SemanticError("una función void no puede retornar un valor", node.token)
        actual = self.type_of(node.expr)
        if actual != self.current_return_type:
            raise SemanticError(
                f"return incompatible: se esperaba '{self.current_return_type}' y se obtuvo '{actual}'", node.token
            )

    def _check_call(self, node):
        if node.nombre not in self.funcs:
            raise SemanticError(f"función '{node.nombre}' no declarada", node.token)
        signature = self.funcs[node.nombre]
        if len(node.args) != len(signature.params):
            raise SemanticError(
                f"'{node.nombre}' espera {len(signature.params)} argumento(s), recibió {len(node.args)}", node.token
            )
        for index, (argument, expected) in enumerate(zip(node.args, signature.params), start=1):
            actual = self.type_of(argument)
            if actual != expected:
                raise SemanticError(
                    f"argumento {index} de '{node.nombre}': se esperaba '{expected}', se obtuvo '{actual}'", node.token
                )
        return signature.return_type

    def _array_symbol(self, name, token):
        symbol = self.env.get(name, token)
        if not symbol.is_array:
            raise SemanticError(f"'{name}' no es un arreglo", token)
        return symbol

    def _check_index(self, index, symbol, token):
        if self.type_of(index) != "int":
            raise SemanticError("el índice de un arreglo debe ser int", token)
        constant = self._constant_int(index)
        if constant is not None and not 0 <= constant < symbol.array_size:
            raise SemanticError(
                f"índice {constant} fuera de rango; se esperaba 0..{symbol.array_size - 1}", token
            )

    def _require_bool(self, expression, token):
        if self.type_of(expression) != "bool":
            raise SemanticError("la condición debe ser booleana", token)

    def _visit_block(self, statements):
        previous = self.env
        self.env = Environment(previous)
        try:
            for statement in statements:
                self.visit(statement)
        finally:
            self.env = previous

    @classmethod
    def _block_returns(cls, statements):
        for statement in statements:
            if isinstance(statement, ReturnStmt):
                return True
            if isinstance(statement, IfStmt) and statement.else_body:
                if cls._block_returns(statement.body) and cls._block_returns(statement.else_body):
                    return True
            if isinstance(statement, WhileStmt):
                if isinstance(statement.cond, Literal) and statement.cond.val is True:
                    if cls._block_returns(statement.body) and not cls._contains_break(statement.body):
                        return True
        return False

    @classmethod
    def _contains_break(cls, statements):
        for statement in statements:
            if isinstance(statement, BreakStmt):
                return True
            if isinstance(statement, IfStmt):
                if cls._contains_break(statement.body) or cls._contains_break(statement.else_body):
                    return True
            # Ciclos anidados
        return False

    @staticmethod
    def _constant_int(node):
        if isinstance(node, Literal) and node.tipo == "int":
            return node.val
        if isinstance(node, UnaryOp) and node.op == "-":
            value = SemanticAnalyzer._constant_int(node.expr)
            return -value if value is not None else None
        return None
